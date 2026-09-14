"""Pair native model selections with providers over the host's stdio protocol.

This is not an HTTP/model proxy. The unmodified Codex executable owns authentication,
model requests, tools, policy decisions and history. Only explicit model selections
are paired with a provider; no prompt, credential or tool output is written to logs.
"""
import argparse
import asyncio
from copy import deepcopy
from dataclasses import dataclass, field
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import uuid

MAX_FRAME = 64 * 1024 * 1024
SWITCH_METHODS = {'thread/settings/update', 'turn/start'}


class RoutingError(RuntimeError):
    pass


def selected_model(params):
    direct = params.get('model')
    mode = params.get('collaborationMode') or {}
    nested = (mode.get('settings') or {}).get('model') if isinstance(mode, dict) else None
    if direct and nested and direct != nested:
        raise RoutingError('Conflicting model selections; select one model before sending')
    return direct or nested


@dataclass
class RouteConfig:
    codex_binary: str
    grok_models: set
    native_models: set
    grok_provider: str = 'ocx-grok'
    audit_file: str = None

    @classmethod
    def load(cls, path):
        raw = json.loads(Path(path).read_text(encoding='utf-8'))
        binary = Path(raw['codex_binary'])
        if not binary.is_absolute() or not binary.is_file():
            raise RoutingError('The original Codex executable is unavailable')
        grok = set(raw['grok_models'])
        native = set(raw['native_models'])
        if not grok or grok & native or not all(x.startswith('xai/grok-') for x in grok):
            raise RoutingError('Invalid or overlapping model routing configuration')
        if not native or not all(x.startswith('gpt-') for x in native):
            raise RoutingError('Native model identities must come from the native GPT catalog')
        return cls(str(binary), grok, native, raw.get('grok_provider', 'ocx-grok'), raw.get('audit_file'))

    def provider(self, model):
        if model in self.grok_models:
            return self.grok_provider
        if model in self.native_models:
            return 'openai'
        return None


@dataclass
class RuntimeState:
    model: str
    provider: str
    runtime: dict = field(default_factory=dict)
    overrides: dict = field(default_factory=dict)
    active: bool = False

    def resume_params(self, thread_id, model, provider):
        result = {'threadId': thread_id, 'model': model, 'modelProvider': provider, 'excludeTurns': True}
        for key in ('cwd', 'runtimeWorkspaceRoots', 'approvalPolicy', 'approvalsReviewer', 'serviceTier'):
            if key in self.runtime:
                result[key] = deepcopy(self.runtime[key])
        profile = self.runtime.get('activePermissionProfile') or {}
        if profile.get('id'):
            result['permissions'] = profile['id']
        else:
            sandbox = self.runtime.get('sandbox', {}).get('type')
            names = {'readOnly': 'read-only', 'workspaceWrite': 'workspace-write', 'dangerFullAccess': 'danger-full-access'}
            if sandbox not in names:
                raise RoutingError('Cannot preserve this task permission profile during a provider switch')
            result['sandbox'] = names[sandbox]
        for key in ('config', 'developerInstructions', 'baseInstructions', 'personality'):
            if key in self.overrides:
                result[key] = deepcopy(self.overrides[key])
        result.setdefault('config', {})
        if self.runtime.get('reasoningEffort') is not None:
            result['config']['model_reasoning_effort'] = self.runtime['reasoningEffort']
        return result


class ModelRouter:
    def __init__(self, config, rpc, forward, audit=None):
        self.config = config
        self.rpc = rpc
        self.forward = forward
        self.audit = audit or (lambda **unused: None)
        self.states = {}
        self.switching = set()
        self.locks = {}

    def paired(self, params):
        output = deepcopy(params)
        model = selected_model(output)
        provider = self.config.provider(model)
        old = output.get('modelProvider')
        if provider and old in (None, 'openai', self.config.grok_provider):
            output['modelProvider'] = provider
            output['model'] = model
        return output

    def observe_result(self, method, params, result):
        if not isinstance(result, dict):
            return
        if method in ('thread/start', 'thread/resume', 'thread/fork') and isinstance(result.get('thread'), dict):
            thread = result['thread']
            tid = thread['id']
            model = result.get('model') or thread.get('model')
            provider = result.get('modelProvider') or thread.get('modelProvider')
            prior = self.states.get(tid)
            overrides = deepcopy(prior.overrides) if prior else {}
            for key in ('config', 'developerInstructions', 'baseInstructions', 'personality'):
                if params.get(key) is not None:
                    overrides[key] = deepcopy(params[key])
            runtime = {key: deepcopy(result[key]) for key in (
                'cwd', 'runtimeWorkspaceRoots', 'approvalPolicy', 'approvalsReviewer',
                'serviceTier', 'sandbox', 'activePermissionProfile', 'reasoningEffort') if key in result}
            self.states[tid] = RuntimeState(model, provider, runtime, overrides, prior.active if prior else False)
            self.audit(event='runtime_bound', method=method, thread_id=tid, model=model, provider=provider)
        elif method == 'thread/settings/update':
            state = self.states.get(params.get('threadId'))
            if state:
                self._settings(state, params)
        elif method == 'turn/start':
            state = self.states.get(params.get('threadId'))
            if state:
                self._settings(state, params)
                # A fast completion notification can precede the response. The caller
                # marks active before forwarding; do not turn it back on here.

    @staticmethod
    def _settings(state, params):
        model = selected_model(params)
        if model:
            state.model = model
        mapping = {'effort': 'reasoningEffort', 'cwd': 'cwd', 'approvalPolicy': 'approvalPolicy',
                   'approvalsReviewer': 'approvalsReviewer', 'serviceTier': 'serviceTier',
                   'runtimeWorkspaceRoots': 'runtimeWorkspaceRoots', 'sandboxPolicy': 'sandbox'}
        for source, dest in mapping.items():
            if source in params and (params[source] is not None or source == 'serviceTier'):
                state.runtime[dest] = deepcopy(params[source])
        if params.get('permissions'):
            state.runtime['activePermissionProfile'] = {'id': params['permissions']}
        elif params.get('sandboxPolicy'):
            state.runtime.pop('activePermissionProfile', None)
        if params.get('personality') is not None:
            state.overrides['personality'] = params['personality']

    def observe_notification(self, message):
        method, params = message.get('method'), message.get('params', {})
        tid = params.get('threadId')
        state = self.states.get(tid)
        if state:
            if method == 'turn/started':
                state.active = True
            elif method == 'turn/completed':
                state.active = False
        # Closing the backend subscription is internal to an idle provider switch.
        # Never filter a turn, tool, approval, error or usage event.
        return not (tid in self.switching and method in {'thread/closed', 'thread/status/changed'})

    async def ensure_state(self, tid):
        if tid not in self.states:
            params = {'threadId': tid, 'excludeTurns': True}
            result = await self.rpc('thread/resume', params)
            self.observe_result('thread/resume', params, result)
        return self.states[tid]

    async def switch(self, tid, model, provider):
        old = await self.ensure_state(tid)
        if old.provider == provider:
            return
        if old.provider not in {'openai', self.config.grok_provider}:
            raise RoutingError('This task uses another provider; its binding was preserved')
        if old.active:
            raise RoutingError('Wait for the current response to finish, or stop it, before switching between GPT and Grok')
        # Snapshot current effective policy before unloading. Settings-update replies
        # are void; a named profile change can also change the effective sandbox.
        current_params = {'threadId': tid, 'excludeTurns': True}
        current = await self.rpc('thread/resume', current_params)
        self.observe_result('thread/resume', current_params, current)
        old = self.states[tid]
        if old.provider == provider:
            return
        params = old.resume_params(tid, model, provider)
        rollback = old.resume_params(tid, old.model, old.provider)
        self.switching.add(tid)
        unloaded = False
        try:
            await self.rpc('thread/unsubscribe', {'threadId': tid})
            unloaded = True
            result = await self.rpc('thread/resume', params)
            if result.get('modelProvider') != provider or result.get('model') != model:
                raise RoutingError('The backend did not apply the requested model and provider')
            for key in ('cwd', 'runtimeWorkspaceRoots', 'approvalPolicy', 'approvalsReviewer', 'sandbox'):
                if key in old.runtime and result.get(key) != old.runtime[key]:
                    raise RoutingError('The backend changed task settings while switching providers: '+key)
            old_profile = (old.runtime.get('activePermissionProfile') or {}).get('id')
            new_profile = (result.get('activePermissionProfile') or {}).get('id')
            if old_profile and new_profile != old_profile:
                raise RoutingError('The backend changed the task permission profile while switching providers')
            self.observe_result('thread/resume', params, result)
            self.audit(event='provider_switched', thread_id=tid, model=model, provider=provider)
        except Exception:
            if unloaded:
                try:
                    await self.rpc('thread/unsubscribe', {'threadId': tid})
                    result = await self.rpc('thread/resume', rollback)
                    self.observe_result('thread/resume', rollback, result)
                except Exception:
                    self.states.pop(tid, None)
            raise
        finally:
            self.switching.discard(tid)

    async def handle(self, message, raw):
        method, params = message.get('method'), message.get('params', {})
        if 'id' not in message or method not in SWITCH_METHODS | {'thread/start', 'thread/resume', 'thread/fork'}:
            await self.forward(message, raw)
            return
        tid = params.get('threadId')
        lock = self.locks.setdefault(tid, asyncio.Lock()) if tid else asyncio.Lock()
        async with lock:
            outgoing = message
            if method in ('thread/start', 'thread/fork'):
                effective = params
                if not selected_model(effective):
                    configured = (effective.get('config') or {}).get('model')
                    if not configured:
                        config = await self.rpc('config/read', {'cwd': effective.get('cwd'), 'includeLayers': False})
                        configured = config.get('config', {}).get('model')
                    if configured:
                        effective = {**effective, 'model': configured}
                outgoing = {**message, 'params': self.paired(effective)}
            elif method == 'thread/resume':
                model = selected_model(params)
                if not model:
                    metadata = await self.rpc('thread/read', {'threadId': tid, 'includeTurns': False})
                    model = metadata['thread'].get('model')
                provider = self.config.provider(model)
                explicit_provider = params.get('modelProvider')
                if provider and explicit_provider in (None, 'openai', self.config.grok_provider):
                    if tid in self.states and self.states[tid].provider != provider:
                        await self.switch(tid, model, provider)
                    outgoing = {**message, 'params': {**params, 'model': model, 'modelProvider': provider}}
            else:
                model = selected_model(params)
                if model:
                    provider = self.config.provider(model)
                    if provider:
                        await self.switch(tid, model, provider)
                if method == 'turn/start' and tid in self.states:
                    self.states[tid].active = True
            await self.forward(outgoing, raw if outgoing is message else None)


class StdioHost:
    def __init__(self, config, argv):
        self.config, self.argv = config, argv
        self.pending = {}
        self.internal = {}
        self.router = ModelRouter(config, self.rpc, self.forward, self.audit)
        self.child = None
        self.outgoing_lock = asyncio.Lock()

    def audit(self, **fields):
        if not self.config.audit_file:
            return
        # Explicit allowlist; never log request parameters, prompts or credentials.
        safe = {k: v for k, v in fields.items() if k in {'event', 'method', 'thread_id', 'model', 'provider', 'code'}}
        safe.update(at=datetime.datetime.now().astimezone().isoformat(), router_pid=os.getpid())
        path = Path(self.config.audit_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(safe, ensure_ascii=False)+'\n')

    @staticmethod
    def emit(message=None, raw=None):
        sys.stdout.buffer.write(raw if raw is not None else (json.dumps(message, ensure_ascii=False, separators=(',', ':'))+'\n').encode())
        sys.stdout.buffer.flush()

    async def send_child(self, message=None, raw=None):
        data = raw if raw is not None else (json.dumps(message, ensure_ascii=False, separators=(',', ':'))+'\n').encode()
        async with self.outgoing_lock:
            self.child.stdin.write(data)
            await self.child.stdin.drain()

    async def rpc(self, method, params):
        ident = 'grok-router-internal-'+uuid.uuid4().hex
        future = asyncio.get_running_loop().create_future()
        self.internal[ident] = future
        try:
            await self.send_child({'id': ident, 'method': method, 'params': params})
            return await asyncio.wait_for(future, timeout=30)
        finally:
            self.internal.pop(ident, None)

    async def forward(self, message, raw):
        ident, method = message.get('id'), message.get('method')
        waiting = method in SWITCH_METHODS | {'thread/start', 'thread/resume', 'thread/fork'} and ident is not None
        future = asyncio.get_running_loop().create_future() if waiting else None
        if waiting:
            self.pending[ident] = (method, message.get('params', {}), future)
        await self.send_child(message, raw)
        if future:
            await future

    async def output_loop(self):
        while True:
            raw = await self.child.stdout.readline()
            if not raw:
                break
            message = json.loads(raw)
            ident = message.get('id')
            if 'method' not in message and ident in self.internal:
                future = self.internal[ident]
                if not future.done():
                    if 'error' in message:
                        future.set_exception(RoutingError(message['error'].get('message', 'Backend rejected provider switch')))
                    else:
                        future.set_result(message.get('result', {}))
                continue
            if 'method' not in message and ident in self.pending:
                method, params, future = self.pending.pop(ident)
                if 'result' in message:
                    self.router.observe_result(method, params, message['result'])
                elif method == 'turn/start' and params.get('threadId') in self.router.states:
                    self.router.states[params['threadId']].active = False
                self.emit(raw=raw)
                if not future.done():
                    future.set_result(None)
                continue
            if 'method' in message and not self.router.observe_notification(message):
                continue
            self.emit(raw=raw)
        for future in [*self.internal.values(), *(v[2] for v in self.pending.values())]:
            if not future.done():
                future.set_exception(RoutingError('Original Codex backend closed'))

    async def run(self):
        env = os.environ.copy()
        env['CODEX_CLI_PATH'] = self.config.codex_binary
        self.child = await asyncio.create_subprocess_exec(
            self.config.codex_binary, *self.argv, stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE, stderr=None, env=env,
            limit=MAX_FRAME, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        loop = asyncio.get_running_loop()
        incoming = asyncio.Queue(maxsize=16)
        def pump():
            try:
                while True:
                    raw = sys.stdin.buffer.readline(MAX_FRAME+1)
                    if len(raw)>MAX_FRAME:
                        raise RoutingError('Protocol frame exceeds supported size')
                    asyncio.run_coroutine_threadsafe(incoming.put(raw or None), loop).result()
                    if not raw: break
            except Exception:
                if not loop.is_closed():
                    asyncio.run_coroutine_threadsafe(incoming.put(None), loop)
        threading.Thread(target=pump, daemon=True).start()
        output = asyncio.create_task(self.output_loop())
        handlers = set()
        async def handle(raw):
            message = None
            try:
                message = json.loads(raw)
                await self.router.handle(message, raw)
            except Exception as error:
                if message is not None and 'id' in message:
                    self.emit({'id': message['id'], 'error': {'code': -32001, 'message': str(error)}})
                    self.audit(event='routing_error', method=message.get('method'), code=type(error).__name__)
                else:
                    raise
        try:
            while not output.done():
                next_input = asyncio.create_task(incoming.get())
                done, _ = await asyncio.wait([next_input, output], return_when=asyncio.FIRST_COMPLETED)
                if output in done:
                    next_input.cancel()
                    await output
                    break
                raw = next_input.result()
                if raw is None:
                    break
                task = asyncio.create_task(handle(raw))
                handlers.add(task)
                task.add_done_callback(handlers.discard)
            if self.child.stdin:
                self.child.stdin.close()
            try:
                await asyncio.wait_for(self.child.wait(), timeout=5)
            except asyncio.TimeoutError:
                self.child.kill()
                await self.child.wait()
            await output
        finally:
            for task in handlers:
                task.cancel()
            if self.child.returncode is None:
                self.child.kill()
                await self.child.wait()
        return self.child.returncode


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--settings', required=True)
    parser.add_argument('codex_args', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    config = RouteConfig.load(args.settings)
    argv = args.codex_args[1:] if args.codex_args[:1] == ['--'] else args.codex_args
    # Only the interactive stdio app-server protocol is intercepted. All native CLI
    # tools, version checks, schema generation and command-runner use stay native.
    is_server = 'app-server' in argv and not any(x in argv for x in ('generate-ts', 'generate-json-schema', 'daemon', 'proxy', '--help', '-h'))
    if not is_server:
        return subprocess.call([config.codex_binary, *argv])
    return asyncio.run(StdioHost(config, argv).run())


if __name__ == '__main__':
    raise SystemExit(main())
