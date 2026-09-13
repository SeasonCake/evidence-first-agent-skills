import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from grok_codex_bridge.factory import (MetadataAppServer, create_task, load_selection,
                                      reconcile_task, start_params, task_spec)
from grok_codex_bridge.registry import Registry, RegistryError
from grok_codex_bridge.trace import RpcError


class FactoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='grok-factory-test-')
        self.root = Path(self.temp.name)
        self.registry = Registry(self.root / 'owned-ledger.sqlite3')
        self.selection = {'provider': 'ocx-grok', 'model': 'xai/grok-4.6', 'effort': 'xhigh',
                          'overrides': {'agents': {'default_subagent_model': 'xai/grok-4.6',
                                                  'default_subagent_reasoning_effort': 'xhigh'}}}
        self.spec = task_spec('合成 Grok task', str(self.root), self.selection)
        self.thread = {'id': 'fixture-task-id', 'modelProvider': 'ocx-grok',
                       'model': 'xai/grok-4.6', 'reasoningEffort': 'xhigh',
                       'ephemeral': False, 'cwd': str(self.root), 'threadSource': 'grok_bridge:request-01'}

    def tearDown(self):
        self.registry.close()
        self.temp.cleanup()

    def client(self):
        client = Mock()
        client.call.side_effect = [{'thread': copy.deepcopy(self.thread)}, {}]
        def initialize(thread_id, request_key, on_started):
            on_started('initial-turn-id')
            return {'initialTurnId': 'initial-turn-id', 'initialReply': 'GROK_TASK_READY',
                    'initialToolItems': 0, 'initialModelTurnsStarted': 1}
        client.initialize_task.side_effect = initialize
        return client

    def verifier(self):
        client = Mock()
        client.call.side_effect = [{'thread': copy.deepcopy(self.thread)},
            {'data': [{'id': 'initial-turn-id', 'status': 'completed'}]},
            {'data': [{'item': {'type': 'agentMessage', 'text': 'GROK_TASK_READY'}}], 'nextCursor': None}, {}]
        return client

    def test_clean_create_is_not_ready_until_persisted_readback(self):
        client = self.client()
        result = create_task(client, self.registry, 'request-01', self.spec, self.selection)
        self.assertEqual(result['binding']['state'], 'initialized')
        self.assertEqual(result['binding']['thread_id'], 'fixture-task-id')
        self.assertEqual(result['initialization']['initialModelTurnsStarted'], 1)
        self.assertTrue(result['createdNewTaskThisOperation'])
        self.assertEqual(result['modelTurnsStartedByThisOperation'], 1)
        self.assertEqual([c.args[0] for c in client.call.call_args_list], ['thread/start', 'thread/name/set'])
        params = client.call.call_args_list[0].args[1]
        self.assertFalse(params['allowProviderModelFallback'])
        self.assertFalse(params['ephemeral'])
        self.assertNotIn('approvalPolicy', params)
        self.assertNotIn('sandbox', params)
        self.assertEqual(params['config']['agents']['default_subagent_model'], 'xai/grok-4.6')
        verified = reconcile_task(self.verifier(), self.registry, 'request-01')
        self.assertEqual(verified['binding']['state'], 'ready')
        self.assertTrue(verified['initialization']['persistedReadback'])
        self.assertIsNone(verified['completionReturn'])
        self.assertFalse(verified['permissionInspection']['inheritanceVerified'])
        self.assertFalse(verified['permissionInspection']['permissionsChangedByFactory'])
        self.assertTrue(verified['permissionInspection']['requiresExactTurn'])

    def test_creation_root_identity_fields_are_supported(self):
        client = self.client()
        response = {key: self.thread[key] for key in ['model', 'modelProvider', 'reasoningEffort', 'cwd']}
        response['thread'] = {'id': self.thread['id'], 'ephemeral': False}
        client.call.side_effect = [response, {}]
        self.assertEqual(create_task(client, self.registry, 'request-01', self.spec, self.selection)
                         ['binding']['state'], 'initialized')

    def test_same_key_reuse_is_read_only(self):
        create_task(self.client(), self.registry, 'request-01', self.spec, self.selection)
        reconcile_task(self.verifier(), self.registry, 'request-01')
        again = Mock()
        again.call.return_value = {'thread': self.thread}
        result = create_task(again, self.registry, 'request-01', self.spec, self.selection)
        self.assertEqual(result['binding']['thread_id'], 'fixture-task-id')
        self.assertFalse(result['createdNewTaskThisOperation'])
        self.assertEqual(result['modelTurnsStartedByThisOperation'], 0)
        again.call.assert_called_once_with('thread/read', {'threadId': 'fixture-task-id', 'includeTurns': False})

    def test_reused_key_changed_spec_stops_before_rpc(self):
        self.registry.reserve('request-01', self.spec)
        changed = dict(self.spec, title='different purpose')
        client = Mock()
        with self.assertRaises(RegistryError):
            create_task(client, self.registry, 'request-01', changed, self.selection)
        client.call.assert_not_called()

    def test_creation_timeout_is_uncertain_and_not_retried(self):
        client = Mock()
        client.call.side_effect = TimeoutError('fixture timeout')
        with self.assertRaises(TimeoutError):
            create_task(client, self.registry, 'request-01', self.spec, self.selection)
        self.assertEqual(self.registry.get('request-01')['state'], 'uncertain')
        with self.assertRaises(RegistryError):
            create_task(client, self.registry, 'request-01', self.spec, self.selection)
        self.assertEqual(client.call.call_count, 1)

    def test_failed_naming_preserves_returned_handle(self):
        client = self.client()
        client.call.side_effect = [{'thread': self.thread}, RpcError('name failed')]
        with self.assertRaises(RpcError):
            create_task(client, self.registry, 'request-01', self.spec, self.selection)
        record = self.registry.get('request-01')
        self.assertEqual(record['thread_id'], 'fixture-task-id')
        self.assertEqual(record['state'], 'uncertain')

    def test_wrong_provider_is_not_fixed_by_rebinding(self):
        client = self.client()
        client.call.side_effect = [{'thread': dict(self.thread, modelProvider='openai')}]
        with self.assertRaises(RpcError):
            create_task(client, self.registry, 'request-01', self.spec, self.selection)
        self.assertEqual(self.registry.get('request-01')['state'], 'identity_mismatch')
        self.assertEqual(client.call.call_count, 1)

    def test_wrong_model_effort_cwd_or_ephemeral_is_rejected(self):
        for override in [{'model': 'gpt-6-astra'}, {'reasoningEffort': 'high'},
                         {'cwd': str(self.root / 'other')}, {'ephemeral': True}]:
            key = 'request-' + next(iter(override))
            client = Mock()
            client.call.return_value = {'thread': dict(self.thread, id=key, **override)}
            with self.assertRaises(RpcError):
                create_task(client, self.registry, key, self.spec, self.selection)
            self.assertEqual(client.call.call_count, 1)

    def test_parent_checked_before_create_and_not_faked_as_native_parent(self):
        spec = task_spec('delegate', str(self.root), self.selection, 'parent-task-id')
        client = self.client()
        client.call.side_effect = [{'thread': {'id': 'parent-task-id'}}, {'thread': self.thread}, {}]
        result = create_task(client, self.registry, 'request-01', spec, self.selection)
        self.assertEqual(result['binding']['spec']['parentThreadId'], 'parent-task-id')
        self.assertEqual(result['binding']['spec']['relationship'], 'bridgeDelegation')
        self.assertEqual(result['completionReturn']['parentThreadId'], 'parent-task-id')
        self.assertTrue(result['completionReturn']['requiresExactDispatchedTurn'])
        self.assertFalse(result['completionReturn']['activeObserverCreatedByFactory'])
        self.assertEqual(result['completionReturn']['observerSpawnParameters'],
                         {'model': 'gpt-5.6-luna', 'reasoning_effort': 'high', 'fork_turns': 'none'})
        self.assertNotIn('observerSpawnParameters', result['binding']['spec'])
        params = client.call.call_args_list[1].args[1]
        self.assertEqual(params['model'], 'xai/grok-4.6')
        self.assertNotIn('parentThreadId', params)
        self.assertIn('parent-task-id', params['developerInstructions'])

    def test_invalid_parent_creates_no_binding_or_task(self):
        spec = task_spec('delegate', str(self.root), self.selection, 'parent-task-id')
        client = Mock()
        client.call.return_value = {'thread': {'id': 'another-id'}}
        with self.assertRaises(RpcError):
            create_task(client, self.registry, 'request-01', spec, self.selection)
        self.assertIsNone(self.registry.get('request-01'))
        self.assertEqual(client.call.call_count, 1)

    def test_reconcile_same_task_after_partial_creation(self):
        self.registry.reserve('request-01', self.spec)
        self.registry.update('request-01', 'uncertain', 'fixture-task-id', evidence={'initialTurnId': 'initial-turn-id'})
        client = self.verifier()
        result = reconcile_task(client, self.registry, 'request-01')
        self.assertEqual(result['binding']['state'], 'ready')
        self.assertEqual([c.args[0] for c in client.call.call_args_list],
                         ['thread/read', 'thread/turns/list', 'thread/items/list', 'thread/name/set'])

    def test_metadata_only_task_cannot_be_marked_ready(self):
        self.registry.reserve('request-01', self.spec)
        self.registry.update('request-01', 'uncertain', 'fixture-task-id')
        client = self.verifier()
        with self.assertRaises(RegistryError):
            reconcile_task(client, self.registry, 'request-01')
        self.assertEqual(self.registry.get('request-01')['state'], 'uncertain')
        self.assertEqual(client.call.call_count, 1)

    def test_initialization_failure_preserves_turn_id(self):
        client = self.client()
        def fail(thread_id, request_key, on_started):
            on_started('initial-turn-id')
            raise TimeoutError('synthetic interruption')
        client.initialize_task.side_effect = fail
        with self.assertRaises(TimeoutError):
            create_task(client, self.registry, 'request-01', self.spec, self.selection)
        record = self.registry.get('request-01')
        self.assertEqual(record['state'], 'uncertain')
        self.assertEqual(record['evidence']['initialTurnId'], 'initial-turn-id')

    def test_persisted_unexpected_tool_does_not_pass_initialization(self):
        self.registry.reserve('request-01', self.spec)
        self.registry.update('request-01', 'initialized', 'fixture-task-id', evidence={'initialTurnId': 'initial-turn-id'})
        client = self.verifier()
        client.call.side_effect = [{'thread': self.thread},
            {'data': [{'id': 'initial-turn-id', 'status': 'completed'}]},
            {'data': [{'item': {'type': 'commandExecution'}}], 'nextCursor': None}]
        with self.assertRaises(RegistryError):
            reconcile_task(client, self.registry, 'request-01')
        self.assertEqual(self.registry.get('request-01')['state'], 'initialized')

    def test_reconcile_requires_matching_provenance(self):
        self.registry.reserve('request-01', self.spec)
        client = Mock()
        client.call.return_value = {'thread': dict(self.thread, threadSource='unrelated')}
        with self.assertRaises(RegistryError):
            reconcile_task(client, self.registry, 'request-01', 'fixture-task-id')
        self.assertEqual(client.call.call_count, 1)

    def test_reconcile_cannot_replace_known_task_id(self):
        self.registry.reserve('request-01', self.spec)
        self.registry.update('request-01', 'uncertain', 'fixture-task-id')
        client = Mock()
        with self.assertRaises(RegistryError):
            reconcile_task(client, self.registry, 'request-01', 'other-task-id')
        client.call.assert_not_called()

    def test_reconcile_preserves_a_user_renamed_task(self):
        self.registry.reserve('request-01', self.spec)
        self.registry.update('request-01', 'initialized', 'fixture-task-id', evidence={'initialTurnId': 'initial-turn-id'})
        client = self.verifier()
        responses = list(client.call.side_effect)
        responses[0]['thread']['name'] = 'User chosen title'
        client.call.side_effect = responses
        result = reconcile_task(client, self.registry, 'request-01')
        self.assertEqual(result['thread']['name'], 'User chosen title')
        self.assertEqual(client.call.call_count, 3)

    def test_ledger_pagination_and_parent_filter(self):
        for i in range(4):
            spec = dict(self.spec, parentThreadId='parent-a' if i % 2 else 'parent-b')
            self.registry.reserve(f'request-{i:02}', spec)
        page = self.registry.list(limit=1, parent_id='parent-a')
        self.assertEqual(page['data'][0]['request_key'], 'request-01')
        next_page = self.registry.list(limit=1, after=page['nextCursor'], parent_id='parent-a')
        self.assertEqual(next_page['data'][0]['request_key'], 'request-03')
        self.assertIsNone(next_page['nextCursor'])

    def test_second_registry_connection_observes_reservation(self):
        self.registry.reserve('request-01', self.spec)
        with Registry(self.registry.path) as other:
            record, fresh = other.reserve('request-01', self.spec)
        self.assertFalse(fresh)
        self.assertEqual(record['state'], 'reserved')

    def test_metadata_transport_does_not_allow_model_or_config_writes(self):
        client = MetadataAppServer.__new__(MetadataAppServer)
        client._request = Mock()
        for method in ['turn/start', 'thread/resume', 'config/value/write', 'thread/archive']:
            with self.assertRaises(ValueError):
                client.call(method, {})
        client._request.assert_not_called()

    def test_invalid_spec_inputs_fail_before_ledger(self):
        for title, folder, parent in [('', self.root, None), ('x' * 121, self.root, None),
                                      ('okay', 'relative', None), ('okay', self.root, '../bad')]:
            with self.assertRaises(ValueError):
                task_spec(title, str(folder), self.selection, parent)

    def test_loading_selection_preserves_gpt_config_and_installs_no_settings(self):
        adapter = self.root / 'adapter'
        adapter.mkdir()
        (adapter / 'settings.json').write_text(json.dumps({
            'selected_model': 'grok-4.6', 'selected_effort': 'xhigh',
            'codex_grok_profile': 'grok-isolated', 'codex_grok_provider': 'ocx-grok',
            'verified_model_aliases': {'grok-4.6': {'codex_model': 'xai/grok-4.6'}}}), encoding='utf-8')
        catalog = self.root / 'catalog.json'
        catalog.write_text('{}', encoding='utf-8')
        profile = self.root / 'grok-isolated.config.toml'
        profile.write_text('model="xai/grok-4.6"\nmodel_provider="ocx-grok"\n'
                           'model_reasoning_effort="xhigh"\nmodel_catalog_json=' + json.dumps(str(catalog)) +
                           '\n[model_providers.ocx-grok]\nrequires_openai_auth=false\n'
                           'base_url="http://127.0.0.1:10100/v1"\n', encoding='utf-8')
        native = self.root / 'config.toml'
        native.write_text('model="gpt-6-astra"\n', encoding='utf-8')
        before = native.read_bytes(), profile.read_bytes()
        result = load_selection(adapter, self.root)
        self.assertEqual(result['overrides']['agents']['default_subagent_model'], 'xai/grok-4.6')
        self.assertEqual((native.read_bytes(), profile.read_bytes()), before)
        profile.write_text(profile.read_text(encoding='utf-8').replace('effort="xhigh"', 'effort="high"'), encoding='utf-8')
        with self.assertRaises(ValueError):
            load_selection(adapter, self.root)


if __name__ == '__main__':
    unittest.main()
