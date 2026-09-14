import asyncio
from copy import deepcopy
import unittest

from grok_codex_bridge.model_router import ModelRouter, RouteConfig, RoutingError, RuntimeState, selected_model

GPT = 'gpt-6-astra'
GROK = 'xai/grok-4.6'
TID = 'synthetic-task'


def native_result(model=GPT, provider='openai'):
    return {'thread': {'id': TID, 'model': model, 'modelProvider': 'openai'},
            'model': model, 'modelProvider': provider, 'reasoningEffort': 'high',
            'cwd': '/synthetic', 'runtimeWorkspaceRoots': ['/synthetic'],
            'approvalPolicy': 'on-request', 'approvalsReviewer': 'user',
            'sandbox': {'type': 'workspaceWrite', 'networkAccess': False, 'writableRoots': ['/synthetic']},
            'activePermissionProfile': {'id': 'synthetic-profile'}, 'serviceTier': None}


class RouterTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.calls = []
        self.sent = []
        self.fail_grok = False
        self.drift_grok_policy = False
        self.runtime = native_result()
        self.config = RouteConfig('/original/codex', {GROK}, {GPT, 'gpt-5.6-sol'})
        async def rpc(method, params):
            self.calls.append((method, deepcopy(params)))
            if method == 'config/read':
                return {'config': {'model': GROK}}
            if method == 'thread/read':
                return {'thread': deepcopy(self.runtime['thread'])}
            if method == 'thread/unsubscribe':
                return {'status': 'unsubscribed'}
            if method == 'thread/resume':
                if self.fail_grok and params.get('modelProvider') == 'ocx-grok':
                    raise RoutingError('Synthetic Grok resume rejected')
                if params.get('model'):
                    self.runtime = deepcopy(self.runtime)
                    self.runtime.update(model=params['model'], modelProvider=params['modelProvider'])
                    self.runtime['thread']['model'] = params['model']
                    for key in ('cwd', 'runtimeWorkspaceRoots', 'approvalPolicy', 'approvalsReviewer', 'serviceTier'):
                        if key in params: self.runtime[key] = deepcopy(params[key])
                    if params.get('permissions'):
                        self.runtime['activePermissionProfile'] = {'id': params['permissions']}
                    if self.drift_grok_policy and params['modelProvider'] == 'ocx-grok':
                        self.runtime['approvalPolicy'] = 'never'
                return deepcopy(self.runtime)
            raise AssertionError(method)
        async def forward(message, raw):
            self.sent.append((deepcopy(message), raw))
        self.router = ModelRouter(self.config, rpc, forward)
        self.router.observe_result('thread/start', {'config': {'synthetic': {'keep': True}},
            'developerInstructions': 'Preserve this synthetic instruction'}, self.runtime)

    async def handle(self, method, params):
        await self.router.handle({'id': 1, 'method': method, 'params': params}, b'original-wire\n')

    async def test_new_grok_pairs_provider_without_changing_other_fields(self):
        params = {'model': GROK, 'modelProvider': None, 'approvalPolicy': 'on-request',
                  'config': {'mcp_servers.example': {'enabled': False}}, 'inputMarker': 'untouched'}
        before = deepcopy(params)
        await self.handle('thread/start', params)
        out = self.sent[0][0]['params']
        self.assertEqual(out, {**params, 'modelProvider': 'ocx-grok'})
        self.assertEqual(params, before)

    async def test_native_gpt_always_selects_native_provider(self):
        await self.handle('thread/start', {'model': GPT, 'modelProvider': None})
        self.assertEqual(self.sent[0][0]['params']['modelProvider'], 'openai')
        self.assertEqual(self.calls, [])

    async def test_saved_model_default_is_resolved_before_pairing(self):
        await self.handle('thread/start', {'model': None, 'cwd': '/synthetic'})
        self.assertEqual(self.calls[0][0], 'config/read')
        self.assertEqual(self.sent[0][0]['params']['modelProvider'], 'ocx-grok')

    async def test_explicit_other_provider_is_preserved(self):
        await self.handle('thread/start', {'model': GPT, 'modelProvider': 'other-author-selected'})
        self.assertEqual(self.sent[0][0]['params']['modelProvider'], 'other-author-selected')

    async def test_unknown_model_is_not_silently_substituted(self):
        await self.handle('thread/start', {'model': 'unknown-model', 'modelProvider': None})
        self.assertEqual(self.sent[0][0]['params'], {'model': 'unknown-model', 'modelProvider': None})

    async def test_unrelated_packets_remain_byte_identical(self):
        await self.handle('command/exec', {'command': ['echo', 'not-run']})
        self.assertEqual(self.sent[0][1], b'original-wire\n')
        self.assertEqual(self.calls, [])

    async def test_idle_switch_unloads_then_restores_exact_policy(self):
        await self.handle('thread/settings/update', {'threadId': TID, 'model': GROK, 'effort': 'xhigh'})
        self.assertEqual([x[0] for x in self.calls], ['thread/resume', 'thread/unsubscribe', 'thread/resume'])
        resume = self.calls[2][1]
        self.assertEqual(resume['permissions'], 'synthetic-profile')
        self.assertEqual(resume['approvalPolicy'], 'on-request')
        self.assertEqual(resume['approvalsReviewer'], 'user')
        self.assertEqual(resume['cwd'], '/synthetic')
        self.assertEqual(resume['runtimeWorkspaceRoots'], ['/synthetic'])
        self.assertEqual(resume['config']['synthetic'], {'keep': True})
        self.assertEqual(resume['developerInstructions'], 'Preserve this synthetic instruction')
        self.assertEqual(self.router.states[TID].provider, 'ocx-grok')
        self.assertEqual(self.sent[0][0]['params']['effort'], 'xhigh')

    async def test_runtime_provider_wins_over_original_creation_provider(self):
        self.router.observe_result('thread/resume', {}, native_result(GROK, 'ocx-grok'))
        self.assertEqual(self.router.states[TID].provider, 'ocx-grok')

    async def test_grok_back_to_gpt_uses_openai(self):
        self.runtime = native_result(GROK, 'ocx-grok')
        self.router.observe_result('thread/resume', {}, native_result(GROK, 'ocx-grok'))
        await self.handle('turn/start', {'threadId': TID, 'model': GPT, 'input': [{'type': 'text', 'text': 'synthetic'}]})
        self.assertEqual(self.calls[2][1]['modelProvider'], 'openai')
        self.assertTrue(self.router.states[TID].active)
        self.assertEqual(self.sent[0][0]['params']['input'], [{'type': 'text', 'text': 'synthetic'}])

    async def test_active_cross_provider_switch_does_not_interrupt(self):
        self.router.states[TID].active = True
        with self.assertRaisesRegex(RoutingError, 'current response'):
            await self.handle('thread/settings/update', {'threadId': TID, 'model': GROK})
        self.assertEqual(self.calls, [])
        self.assertEqual(self.sent, [])

    async def test_same_provider_model_switch_does_not_reload(self):
        await self.handle('thread/settings/update', {'threadId': TID, 'model': 'gpt-5.6-sol'})
        self.assertEqual(self.calls, [])
        self.assertEqual(self.sent[0][1], b'original-wire\n')

    async def test_rejected_switch_rolls_back_without_sending_user_prompt(self):
        self.fail_grok = True
        with self.assertRaisesRegex(RoutingError, 'rejected'):
            await self.handle('turn/start', {'threadId': TID, 'model': GROK, 'input': [{'type': 'text', 'text': 'synthetic'}]})
        self.assertEqual([x[0] for x in self.calls], ['thread/resume', 'thread/unsubscribe', 'thread/resume', 'thread/unsubscribe', 'thread/resume'])
        self.assertEqual(self.calls[-1][1]['modelProvider'], 'openai')
        self.assertEqual(self.sent, [])
        self.assertFalse(self.router.switching)

    async def test_policy_drift_is_detected_and_native_state_restored(self):
        self.drift_grok_policy = True
        with self.assertRaisesRegex(RoutingError, 'changed task settings'):
            await self.handle('thread/settings/update', {'threadId': TID, 'model': GROK})
        self.assertEqual(self.router.states[TID].provider, 'openai')
        self.assertEqual(self.runtime['approvalPolicy'], 'on-request')
        self.assertEqual(self.sent, [])

    async def test_collaboration_mode_model_is_routed(self):
        await self.handle('turn/start', {'threadId': TID, 'model': None,
            'collaborationMode': {'mode': 'default', 'settings': {'model': GROK}}})
        self.assertEqual(self.calls[2][1]['modelProvider'], 'ocx-grok')

    async def test_conflicting_model_fields_fail_before_any_backend_request(self):
        with self.assertRaisesRegex(RoutingError, 'Conflicting'):
            await self.handle('turn/start', {'threadId': TID, 'model': GPT,
                'collaborationMode': {'settings': {'model': GROK}}})
        self.assertEqual(self.calls, [])

    async def test_resume_pairs_stored_selected_model(self):
        self.runtime['thread']['model'] = GROK
        self.router.states.clear()
        await self.handle('thread/resume', {'threadId': TID, 'model': None, 'modelProvider': None})
        self.assertEqual(self.sent[0][0]['params']['modelProvider'], 'ocx-grok')
        self.assertEqual(self.sent[0][0]['params']['model'], GROK)

    async def test_only_internal_connection_events_are_filtered(self):
        self.router.switching.add(TID)
        self.assertFalse(self.router.observe_notification({'method': 'thread/closed', 'params': {'threadId': TID}}))
        for method in ['turn/completed', 'item/started', 'item/completed', 'error', 'thread/tokenUsage/updated', 'item/commandExecution/requestApproval']:
            self.assertTrue(self.router.observe_notification({'method': method, 'params': {'threadId': TID}}))

    async def test_completion_clears_active_before_late_turn_response(self):
        self.router.states[TID].active = True
        self.router.observe_notification({'method': 'turn/completed', 'params': {'threadId': TID}})
        self.router.observe_result('turn/start', {'threadId': TID}, {'turn': {'id': 'synthetic'}})
        self.assertFalse(self.router.states[TID].active)

    async def test_permission_changes_are_retained_for_later_switch(self):
        self.runtime['approvalPolicy'] = 'never'
        self.runtime['activePermissionProfile'] = {'id': ':read-only'}
        self.runtime['sandbox'] = {'type': 'readOnly', 'networkAccess': False}
        self.router.observe_result('thread/settings/update', {'threadId': TID,
            'permissions': ':read-only', 'approvalPolicy': 'never'}, {})
        await self.handle('thread/settings/update', {'threadId': TID, 'model': GROK})
        self.assertEqual(self.calls[2][1]['permissions'], ':read-only')
        self.assertEqual(self.calls[2][1]['approvalPolicy'], 'never')


if __name__ == '__main__':
    unittest.main()
