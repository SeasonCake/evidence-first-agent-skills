"""Create a task, initialize durable history, then hand all subsequent turns to the app."""
import hashlib
import json
from pathlib import Path
import re
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
from urllib.parse import quote

from .registry import RegistryError
from .initial_turn import InitialTurnMixin, READY_MARKER
from .trace import ReadOnlyAppServer, RpcError, read_thread_metadata


class MetadataAppServer(InitialTurnMixin, ReadOnlyAppServer):
    """The factory initializes its own new task; later turn writers stay in the app."""
    def call(self, method, params):
        if method in {'thread/start', 'thread/name/set'}:
            return self._request(method, params)
        return super().call(method, params)


def load_selection(adapter_root, codex_home):
    settings = json.loads((Path(adapter_root) / 'settings.json').read_text(encoding='utf-8'))
    profile_name = settings['codex_grok_profile']
    if not re.fullmatch(r'[A-Za-z0-9_-]+', profile_name):
        raise ValueError('The selected profile name must be a plain filename stem')
    profile_path = Path(codex_home) / (profile_name + '.config.toml')
    profile = tomllib.loads(profile_path.read_text(encoding='utf-8'))
    native_model = settings['selected_model']
    model = settings['verified_model_aliases'][native_model]['codex_model']
    provider = settings['codex_grok_provider']
    effort = settings['selected_effort']
    if (profile['model'], profile['model_provider'], profile['model_reasoning_effort']) != (model, provider, effort):
        raise ValueError('Selected Grok settings and dedicated Codex profile disagree; no model substitution')
    provider_config = profile['model_providers'][provider]
    if provider_config.get('requires_openai_auth') is not False:
        raise ValueError('Dedicated Grok provider must not request native OpenAI authentication')
    catalog = Path(profile['model_catalog_json'])
    if not catalog.is_file():
        raise ValueError('Selected Grok model catalog does not exist')
    overrides = {
        'model_providers': {provider: provider_config},
        'model_catalog_json': str(catalog),
        'model_reasoning_effort': effort,
        'agents': {'default_subagent_model': model, 'default_subagent_reasoning_effort': effort},
    }
    if 'features' in profile:
        overrides['features'] = profile['features']
    return {'model': model, 'provider': provider, 'effort': effort, 'overrides': overrides}


def task_spec(title, cwd, selection, parent_id=None):
    if not isinstance(title, str) or not title.strip() or len(title) > 120:
        raise ValueError('A nonempty task title of at most 120 characters is required')
    folder = Path(cwd)
    if not folder.is_absolute() or not folder.is_dir():
        raise ValueError('Choose an existing absolute project or fixture directory')
    if parent_id is not None and not re.fullmatch(r'[A-Za-z0-9_-]{8,100}', parent_id):
        raise ValueError('Invalid parent task ID')
    return {'title': title.strip(), 'cwd': str(folder.resolve()),
            'model': selection['model'], 'provider': selection['provider'], 'effort': selection['effort'],
            'parentThreadId': parent_id,
            'relationship': 'bridgeDelegation' if parent_id else 'standalone',
            'selectionSha256': hashlib.sha256(json.dumps(selection, sort_keys=True).encode()).hexdigest()}


def start_params(spec, selection, request_key):
    return {'model': spec['model'], 'modelProvider': spec['provider'],
            'allowProviderModelFallback': False, 'cwd': spec['cwd'], 'ephemeral': False,
            'serviceName': 'grok_codex_bridge', 'threadSource': 'grok_bridge:' + request_key,
            'config': selection['overrides'],
            'developerInstructions': (
                'This is a dedicated Grok-backed Codex task. Keep the selected Grok provider/model. '
                'Do not substitute a GPT child or switch provider without the user selecting it. '
                'For requested Grok delegation, use the installed grok-bridge Skill and its persistent '
                'desktop.py task route. The P0-tested explicit Grok-model spawn_agent path was rejected; '
                'do not use it unless the user explicitly selects a new native-compatibility probe. '
                'Verify actual child identity rather than silently using GPT. '
                'Before substantive project work, use the grok-bridge context operation or explicitly reread '
                'the current canonical workspace/project AGENTS.md and selected current documents. '
                'Old conversation instructions are not proof of current file contents. On a document revision '
                'or stage change, refresh those same files before continuing; do not use a copied project policy. '
                'Project instructions and host tool/approval rules continue to apply. '
                'Other tasks may inspect this persisted conversation by its task ID. '
                + ('This task was delegated by Codex task ' + spec['parentThreadId'] +
                   '; the bridge ledger records this relationship, not a native Subagents-tree claim. '
                   'For delegated assignments follow the current installed grok-bridge Skill return mode. '
                   'With a native completion observer, put the complete handoff in your final result; '
                   'do not call a cross-task send tool unless the assignment separately requests that '
                   'approval-controlled action. The observer does not change your model or do your work.'
                   if spec['parentThreadId'] else 'The user can converse directly in this standalone task.'))}


def verify_identity(thread, spec, thread_id=None):
    if not isinstance(thread, dict) or not thread.get('id'):
        raise RpcError('Missing task identity')
    if thread_id is not None and thread['id'] != thread_id:
        raise RpcError('Task ID mismatch')
    if thread.get('modelProvider') != spec['provider'] or thread.get('model') != spec['model']:
        raise RpcError('Task provider/model mismatch; no fallback or history migration')
    if thread.get('reasoningEffort') != spec['effort'] or thread.get('ephemeral') is not False:
        raise RpcError('Task effort/persistence mismatch')
    if Path(thread.get('cwd', '')).resolve() != Path(spec['cwd']).resolve():
        raise RpcError('Task project directory mismatch')


def receipt(record, thread):
    return {'binding': record, 'thread': {key: thread.get(key) for key in (
        'id', 'name', 'modelProvider', 'model', 'reasoningEffort', 'ephemeral',
        'historyMode', 'cwd', 'parentThreadId', 'threadSource', 'canAcceptDirectInput')},
        'openInCodex': 'codex://threads/' + quote(thread['id'], safe=''),
        'initialization': record['evidence'], 'subsequentWriter': 'native Codex app',
        'permissionInspection': {'operation': 'permissions', 'threadId': thread['id'],
                                 'requiresExactTurn': True, 'inheritanceVerified': False,
                                 'permissionsChangedByFactory': False,
                                 'notice': 'Ready verifies persistence/model/cwd, not permission parity with the parent'},
        'contextRefresh': {'operation': 'context', 'cwd': record['spec']['cwd'], 'threadId': thread['id'],
                           'requiredBefore': 'substantive project handoff or continuing after guidance changes'},
        'completionReturn': (None if not record['spec'].get('parentThreadId') else {
            'mode': 'nativeCompletionObserver', 'operation': 'observe',
            'parentThreadId': record['spec']['parentThreadId'],
            'requiresExactDispatchedTurn': True, 'observerIsCreatedByNativeParent': True,
            'observerSpawnParameters': {'model': 'gpt-5.6-luna', 'reasoning_effort': 'high',
                                        'fork_turns': 'none'},
            'activeObserverCreatedByFactory': False}),
        'createdNewTaskThisOperation': False, 'modelTurnsStartedByThisOperation': 0,
        'nextAction': (
            'Close the creator and verify persisted history before handing off'
            if record['state'] != 'ready' else
            'Dispatch with the native app, capture the exact new turn, and assign the native completion observer'
            if record['spec'].get('parentThreadId') else
            'Open this task or send its work with the native app send operation, without model override')}


def create_task(client, registry, request_key, spec, selection):
    existing = registry.get(request_key)
    if existing is None and spec['parentThreadId']:
        # Verify the parent exists before reserving or creating anything.
        parent = read_thread_metadata(client, spec['parentThreadId'])
        if parent.get('thread', {}).get('id') != spec['parentThreadId']:
            raise RpcError('Delegation parent was not found')
    record, fresh = registry.reserve(request_key, spec)
    if not fresh:
        if record['state'] != 'ready' or not record['thread_id']:
            raise RegistryError('Creation is unfinished or uncertain; reconcile this request key before creating another task')
        thread = read_thread_metadata(client, record['thread_id'])['thread']
        verify_identity(thread, spec, record['thread_id'])
        return receipt(record, thread)
    try:
        response = client.call('thread/start', start_params(spec, selection, request_key))
        thread = response.get('thread', {})
        thread_id = thread.get('id')
        if not thread_id:
            raise RpcError('Creation reply omitted its task ID')
        # Save the handle before naming, verification or any later fallible step.
        registry.update(request_key, 'identified', thread_id=thread_id)
        # Creation may expose current settings at the response root before the first turn.
        for key in ('model', 'modelProvider', 'reasoningEffort', 'cwd'):
            if thread.get(key) is None and key in response:
                thread[key] = response[key]
        try:
            verify_identity(thread, spec, thread_id)
        except RpcError:
            registry.update(request_key, 'identity_mismatch')
            raise
        client.call('thread/name/set', {'threadId': thread_id, 'name': spec['title']})
        thread['name'] = spec['title']
        registry.update(request_key, 'initializing')
        evidence = client.initialize_task(thread_id, request_key,
            lambda turn_id: registry.update(request_key, 'initializing', evidence={'initialTurnId': turn_id}))
        record = registry.update(request_key, 'initialized', evidence=evidence)
        result = receipt(record, thread)
        result['createdNewTaskThisOperation'] = True
        result['modelTurnsStartedByThisOperation'] = 1
        return result
    except Exception as error:
        if registry.get(request_key)['state'] != 'identity_mismatch':
            registry.update(request_key, 'uncertain', error_class=type(error).__name__)
        raise


def reconcile_task(client, registry, request_key, thread_id=None):
    record = registry.get(request_key)
    if record is None:
        raise RegistryError('Unknown creation request')
    selected_id = record['thread_id'] or thread_id
    if not selected_id or (thread_id and selected_id != thread_id):
        raise RegistryError('Supply the exact created task ID; an existing binding cannot be replaced')
    thread = read_thread_metadata(client, selected_id)['thread']
    verify_identity(thread, record['spec'], selected_id)
    if thread.get('threadSource') != 'grok_bridge:' + request_key:
        raise RegistryError('Task provenance does not match this creation request')
    initial_turn_id = record['evidence'].get('initialTurnId')
    if not initial_turn_id:
        raise RegistryError('Initialization was not recorded; no automatic new turn or task')
    turns = client.call('thread/turns/list', {'threadId': selected_id, 'limit': 20,
        'sortDirection': 'asc', 'itemsView': 'notLoaded'})
    initial = next((t for t in turns.get('data', []) if t.get('id') == initial_turn_id), None)
    if not initial or initial.get('status') != 'completed':
        raise RegistryError('Initialization is not a verified completed turn')
    items = client.call('thread/items/list', {'threadId': selected_id, 'turnId': initial_turn_id,
        'limit': 20, 'sortDirection': 'asc'})
    if items.get('nextCursor') is not None:
        raise RegistryError('Initialization contains more than the bounded expected item page')
    raw_items = [entry.get('item', {}) for entry in items.get('data', [])]
    if any(i.get('type') not in {'userMessage', 'agentMessage', 'reasoning'} for i in raw_items):
        raise RegistryError('Unexpected initialization tool activity')
    if not any(i.get('type') == 'agentMessage' and i.get('text', '').strip() == READY_MARKER for i in raw_items):
        raise RegistryError('Persisted initialization reply was not found')
    if not thread.get('name'):
        client.call('thread/name/set', {'threadId': selected_id, 'name': record['spec']['title']})
        thread['name'] = record['spec']['title']
    evidence = {'initialTurnId': initial_turn_id, 'initialReply': READY_MARKER,
                'initialToolItems': 0, 'initialModelTurnsStarted': 1, 'persistedReadback': True}
    record = registry.update(request_key, 'ready', thread_id=selected_id, evidence=evidence)
    return receipt(record, thread)
