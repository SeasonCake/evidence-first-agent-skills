"""Local task creation, discovery and bounded trace entry; the native app owns turns."""
import argparse
import json
import os
from pathlib import Path
import sys

from .factory import MetadataAppServer, create_task, load_selection, reconcile_task, task_spec
from .registry import Registry
from .trace import ReadOnlyAppServer, read_trace
from .context import instruction_context, public_context, context_prompt, shared_user_instruction_paths, TASK_ROLES
from .completion import observe, saved_result, save_result, validate_binding, completion_notice, receive_result
from .permissions import inspect_permissions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adapter-root', default=str(Path.home() / '.codex/grok-adapter'))
    parser.add_argument('--codex-home', default=os.environ.get('CODEX_HOME', str(Path.home() / '.codex')))
    parser.add_argument('--codex-binary', default=os.environ.get('GROK_BRIDGE_CODEX_BINARY'))
    parser.add_argument('--registry')
    commands = parser.add_subparsers(dest='command', required=True)
    new = commands.add_parser('create', help='Create a task with one no-tools initialization turn and persisted readback')
    new.add_argument('--request-key', required=True)
    new.add_argument('--title', required=True)
    new.add_argument('--cwd', required=True)
    new.add_argument('--parent-id')
    context = commands.add_parser('context', help='Read current canonical project guidance; no model call or task write')
    context.add_argument('--cwd', required=True)
    context.add_argument('--workspace-root', help='Explicit instruction ancestor boundary; use the selected workspace, not the installation directory')
    context.add_argument('--doc', action='append', default=[], help='Additional selected current document, repeatable')
    context.add_argument('--role', choices=TASK_ROLES, help='Current selected assignment role; never changes permissions')
    context.add_argument('--thread-id', help='Also verify the existing task uses this exact cwd')
    context.add_argument('--include-content', action='store_true')
    context.add_argument('--prompt', action='store_true', help='Emit refreshed file content for a native app handoff')
    context.add_argument('--expect-fingerprint', help='Compare with a previously sent context; never silently reuse it')
    listing = commands.add_parser('list', help='Read the bridge binding ledger, not conversation contents')
    listing.add_argument('--limit', type=int, default=20)
    listing.add_argument('--after', type=int, default=0)
    listing.add_argument('--parent-id')
    children = commands.add_parser('children', help='Read bridge bindings and native Grok children separately')
    children.add_argument('--parent-id', required=True)
    children.add_argument('--limit', type=int, default=20)
    children.add_argument('--native-cursor')
    children.add_argument('--bridge-after', type=int, default=0)
    trace = commands.add_parser('trace', help='Read saved history; no model call')
    trace.add_argument('--thread-id', required=True)
    trace.add_argument('--turn-limit', type=int, default=3)
    trace.add_argument('--item-limit', type=int, default=20)
    trace.add_argument('--turns-cursor')
    trace.add_argument('--items-cursor')
    trace.add_argument('--include-content', action='store_true')
    trace.add_argument('--raw-tools', action='store_true')
    trace.add_argument('--raw-cursor')
    repair = commands.add_parser('reconcile', help='Recover an uncertain creation; never create another task')
    repair.add_argument('--request-key', required=True)
    repair.add_argument('--thread-id')
    observer = commands.add_parser('observe', help='Collect one delegated turn; caller owns waiting and notification')
    observer.add_argument('--thread-id', required=True)
    observer.add_argument('--turn-id', required=True)
    observer.add_argument('--parent-id', required=True)
    observer.add_argument('--deadline', type=int, default=600)
    receiver = commands.add_parser('receive', help='Read and verify the exact completion receipt without rewriting its payload')
    receiver.add_argument('--thread-id', required=True)
    receiver.add_argument('--turn-id', required=True)
    receiver.add_argument('--parent-id', required=True)
    receiver.add_argument('--receipt', required=True)
    receiver.add_argument('--receipt-sha256', required=True)
    permissions = commands.add_parser('permissions', help='Inspect exact-turn permission evidence without changing settings')
    permissions.add_argument('--thread-id', required=True)
    permissions.add_argument('--turn-id', required=True)
    args = parser.parse_args()
    root = Path(args.adapter_root)
    if args.command == 'receive':
        result = receive_result(root / 'runtime/completion-results', args.receipt,
                                args.thread_id, args.turn_id, args.parent_id, args.receipt_sha256)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if args.command == 'permissions':
        binary = args.codex_binary or json.loads((root / 'desktop-settings.json').read_text(encoding='utf-8'))['codex_binary']
        with ReadOnlyAppServer(binary, Path.cwd()) as client:
            result = inspect_permissions(client, args.thread_id, args.turn_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if args.command == 'context':
        # This operation must not open/create the separate task-binding ledger.
        context_options = {'global_instructions': shared_user_instruction_paths(args.codex_home),
                           'task_role': args.role}
        if args.workspace_root:
            context_options['workspace_root'] = args.workspace_root
        current = instruction_context(args.cwd, args.doc, **context_options)
        if args.thread_id:
            binary = args.codex_binary or json.loads((root / 'desktop-settings.json').read_text(encoding='utf-8'))['codex_binary']
            with ReadOnlyAppServer(binary, Path(args.cwd)) as client:
                from .trace import read_thread_metadata
                thread = read_thread_metadata(client, args.thread_id)['thread']
            if thread.get('id') != args.thread_id or Path(thread.get('cwd', '')).resolve() != Path(current['cwd']):
                raise ValueError('Existing task cwd does not match the selected project; no context or task rebinding')
            current['threadId'] = args.thread_id
            current['modelProvider'] = thread.get('modelProvider')
        result = public_context(current, args.include_content)
        result['changedFromExpected'] = (None if args.expect_fingerprint is None else
                                         current['fingerprint'] != args.expect_fingerprint)
        if args.prompt:
            result['refreshPrompt'] = context_prompt(current)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    registry_path = Path(args.registry) if args.registry else root / 'runtime/desktop-tasks.sqlite3'
    with Registry(registry_path) as registry:
        if args.command == 'list':
            result = registry.list(args.limit, args.after, args.parent_id)
        else:
            binary = args.codex_binary
            if not binary:
                local = json.loads((root / 'desktop-settings.json').read_text(encoding='utf-8'))
                binary = local['codex_binary']
            if args.command == 'observe':
                record = registry.for_thread(args.thread_id)
                spec = validate_binding(record, args.thread_id, args.parent_id)
                output_root = root / 'runtime/completion-results'
                result = saved_result(output_root, args.thread_id, args.turn_id, args.parent_id)
                if result is None:
                    with ReadOnlyAppServer(binary, spec['cwd']) as client:
                        result = observe(client, record, args.thread_id, args.turn_id,
                                         args.parent_id, args.deadline)
                    result = save_result(output_root, result)
                result = completion_notice(result)
            elif args.command == 'children':
                selection = load_selection(root, args.codex_home)
                with ReadOnlyAppServer(binary, Path.cwd()) as client:
                    params = {'parentThreadId': args.parent_id, 'modelProviders': [selection['provider']],
                        'sourceKinds': ['subAgent', 'subAgentThreadSpawn', 'subAgentOther'],
                        'limit': args.limit, 'useStateDbOnly': True}
                    if args.native_cursor:
                        params['cursor'] = args.native_cursor
                    native = client.call('thread/list', params)
                result = {'parentThreadId': args.parent_id,
                    'bridgeDelegates': registry.list(args.limit, args.bridge_after, args.parent_id),
                    'nativeGrokChildren': {'data': [{key: t.get(key) for key in (
                        'id', 'name', 'modelProvider', 'model', 'reasoningEffort', 'parentThreadId')}
                        for t in native['data']], 'nextCursor': native.get('nextCursor')},
                    'modelRequestsStarted': 0}
            elif args.command == 'create':
                selection = load_selection(root, args.codex_home)
                spec = task_spec(args.title, args.cwd, selection, args.parent_id)
                with MetadataAppServer(binary, spec['cwd']) as client:
                    result = create_task(client, registry, args.request_key, spec, selection)
                if result['binding']['state'] != 'ready':
                    # A returned ID is not enough. Reopen through an independent process
                    # after creator exit, and require the real initialization history.
                    with MetadataAppServer(binary, spec['cwd']) as verifier:
                        result = reconcile_task(verifier, registry, args.request_key)
                    result['createdNewTaskThisOperation'] = True
                    result['modelTurnsStartedByThisOperation'] = 1
            elif args.command == 'reconcile':
                record = registry.get(args.request_key)
                if not record:
                    raise ValueError('Unknown request key')
                with MetadataAppServer(binary, record['spec']['cwd']) as client:
                    result = reconcile_task(client, registry, args.request_key, args.thread_id)
            else:
                selection = load_selection(root, args.codex_home)
                with ReadOnlyAppServer(binary, Path.cwd()) as client:
                    result = read_trace(client, args.thread_id, args.turn_limit, args.item_limit,
                                        args.turns_cursor, args.items_cursor, selection['provider'], args.include_content,
                                        args.raw_tools, args.raw_cursor)
                result['bridgeBinding'] = registry.for_thread(args.thread_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))


def run_cli():
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        main()
    except Exception as error:
        print(json.dumps({'status': 'error', 'errorClass': type(error).__name__,
            'message': str(error)[:700],
            'recovery': 'Keep the existing request/task ID. Do not recreate, switch model or start another writer.'},
            ensure_ascii=False))
        raise SystemExit(1)


if __name__ == '__main__':
    run_cli()
