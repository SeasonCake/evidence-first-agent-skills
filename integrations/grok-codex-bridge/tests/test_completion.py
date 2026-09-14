import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from grok_codex_bridge.completion import (
    DeadlineClient, observe, parent_dispatched, save_result, saved_result, validate_binding,
    completion_notice, receive_result, MAX_RESULT_BYTES,
)
from grok_codex_bridge.trace import RpcError


THREAD = "grok-task-001"
TURN = "grok-turn-001"
PARENT = "parent-task-001"


class CompletionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="completion-tests-")
        self.root = Path(self.temp.name)
        self.spec = {"parentThreadId": PARENT, "relationship": "bridgeDelegation",
                     "model": "xai/grok-4.6", "provider": "ocx-grok",
                     "effort": "xhigh", "cwd": str(self.root)}
        self.record = {"state": "ready", "thread_id": THREAD, "spec": self.spec}
        self.thread = {"id": THREAD, "model": "xai/grok-4.6", "modelProvider": "ocx-grok",
                       "reasoningEffort": "xhigh", "ephemeral": False, "cwd": str(self.root)}
        self.envelope = {"turnId": TURN, "item": {
            "type": "functionCallOutput", "name": "send_message_to_thread", "namespace": "codex_app",
            "output": f"<codex_delegation>\n<source_thread_id>{PARENT}</source_thread_id>\n<input>fixture</input></codex_delegation>"}}
        self.message = {"turnId": TURN, "item": {
            "type": "agentMessage", "id": "message-001", "text": '{"answer": 95}'}}
        self.elapsed = 0

    def tearDown(self):
        self.temp.cleanup()

    def sleep(self, seconds):
        self.elapsed += seconds

    def client(self, statuses=None, entries=None, metadata=None):
        client = Mock()
        statuses = statuses or [("completed", 2), ("completed", 2)]
        client.poll = 0
        entries = [self.envelope, self.message] if entries is None else entries
        def call(method, params):
            if method == "thread/read":
                return {"thread": self.thread if metadata is None else metadata}
            if method == "thread/turns/list":
                status, completed = statuses[min(client.poll, len(statuses) - 1)]
                client.poll += 1
                return {"data": [{"id": TURN, "status": status, "completedAt": completed}]}
            if method == "thread/items/list":
                self.assertEqual(params["turnId"], TURN)
                return {"data": list(reversed(entries)) if params["sortDirection"] == "desc"
                        else entries, "nextCursor": None}
            self.fail("Unexpected mutating method: " + method)
        client.call.side_effect = call
        return client

    def run_observer(self, client, deadline=20):
        return observe(client, self.record, THREAD, TURN, PARENT, deadline,
                       clock=lambda: self.elapsed, sleep=self.sleep)

    def test_completed_without_explicit_child_send(self):
        client = self.client()
        result = self.run_observer(client)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["result_message"]["content"]["text"], '{"answer": 95}')
        self.assertEqual(result["polls"], 2)
        self.assertEqual(result["approval_actions"], 0)
        self.assertEqual(result["modelRequestsStarted"], 0)
        self.assertFalse(result["business_success_inferred"])
        self.assertFalse(result["delivery_verified"])
        self.assertTrue(result["parent_dispatch_verified"])
        self.assertTrue(all(call.args[0] in {"thread/read", "thread/turns/list", "thread/items/list"}
                            for call in client.call.call_args_list))

    def test_running_to_completed(self):
        result = self.run_observer(self.client([("inProgress", None), ("completed", 2), ("completed", 2)]))
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["polls"], 3)

    def test_transient_interrupted_without_end_time_not_completion(self):
        result = self.run_observer(self.client([("interrupted", None), ("inProgress", None),
                                               ("completed", 4), ("completed", 4)]))
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["polls"], 4)

    def test_failure_not_pass(self):
        result = self.run_observer(self.client([("failed", 2)], [self.envelope]))
        self.assertEqual(result["status"], "failed")
        self.assertTrue(result["needs_attention"])

    def test_timeout_not_worker_failure(self):
        result = self.run_observer(self.client([("inProgress", None)]), 4)
        self.assertEqual(result["status"], "observation_timeout")
        self.assertTrue(result["needs_attention"])

    def test_terminal_without_output_is_attention(self):
        result = self.run_observer(self.client(entries=[self.envelope]))
        self.assertEqual(result["status"], "completed_without_message")

    def test_wrong_parent_and_standalone_rejected_before_read(self):
        for changes in ({"parentThreadId": "another-parent"}, {"relationship": "standalone"}):
            self.record["spec"] = {**self.spec, **changes}
            with self.assertRaises(ValueError):
                self.run_observer(self.client())

    def test_wrong_model_is_not_silently_accepted(self):
        result = self.run_observer(self.client(metadata={**self.thread, "model": "gpt-6-astra"}))
        self.assertEqual(result["status"], "observer_error")

    def test_other_turn_is_not_forwarded(self):
        wrong = copy.deepcopy(self.message)
        wrong["turnId"] = "other-turn-002"
        result = self.run_observer(self.client(entries=[self.envelope, wrong]))
        self.assertEqual(result["status"], "observer_error")
        self.assertNotIn("result_message", result)

    def test_user_or_child_text_cannot_spoof_parent_envelope(self):
        fake = copy.deepcopy(self.envelope)
        fake["item"]["type"] = "userMessage"
        self.assertFalse(parent_dispatched([fake], PARENT))
        fake["item"]["type"] = "functionCallOutput"
        fake["item"]["namespace"] = "unknown"
        self.assertFalse(parent_dispatched([fake], PARENT))
        self.assertFalse(parent_dispatched([self.envelope], "wrong-parent"))

    def test_wrong_turn_or_no_parent_envelope_fail_closed(self):
        result = self.run_observer(self.client(entries=[self.message]))
        self.assertEqual(result["status"], "observer_error")

    def test_reasoning_is_not_exported(self):
        reasoning = {"turnId": TURN, "item": {"type": "reasoning", "text": "secret-reasoning"}}
        result = self.run_observer(self.client(entries=[self.envelope, reasoning, self.message]))
        self.assertNotIn("secret-reasoning", json.dumps(result))

    def test_rpc_failure_is_explicit(self):
        client = self.client()
        client.call.side_effect = RpcError("fixture visibility failure")
        result = self.run_observer(client)
        self.assertEqual(result["status"], "observer_error")

    def test_result_cache_preserves_identity_and_bytes(self):
        result = self.run_observer(self.client())
        first = save_result(self.root, result)
        before = Path(first["receipt_path"]).read_bytes()
        second = save_result(self.root, {**result, "status": "failed"})
        self.assertTrue(second["cached"])
        self.assertEqual(before, Path(first["receipt_path"]).read_bytes())
        with self.assertRaises(ValueError):
            saved_result(self.root, THREAD, TURN, "different-parent")
        self.assertEqual(list(self.root.glob("*.lock")), [])
        self.assertEqual(list(self.root.glob("*.tmp")), [])

    def test_transient_attempt_does_not_poison_final_cache(self):
        partial = {"thread_id": THREAD, "turn_id": TURN, "parent_id": PARENT,
                   "status": "observation_timeout"}
        saved = save_result(self.root, partial)
        self.assertIn(".attempt-", saved["receipt_path"])
        self.assertIsNone(saved_result(self.root, THREAD, TURN, PARENT))
        self.assertFalse(save_result(self.root, self.run_observer(self.client()))["cached"])

    def test_invalid_identity_deadline_and_missing_binding(self):
        for invalid in ("../escape", ""):
            with self.assertRaises(ValueError):
                validate_binding(self.record, invalid, PARENT)
        with self.assertRaises(ValueError):
            validate_binding(None, THREAD, PARENT)
        with self.assertRaises(ValueError):
            self.run_observer(self.client(), 1801)

    def test_rpc_budget_is_remaining_deadline_and_restored(self):
        client = Mock()
        client.timeout = 15
        seen = []
        client.call.side_effect = lambda method, params: seen.append(client.timeout) or {}
        wrapped = DeadlineClient(client, 3, lambda: 1)
        wrapped.call("thread/read", {})
        self.assertEqual(seen, [2])
        self.assertEqual(client.timeout, 15)
        with self.assertRaises(TimeoutError):
            DeadlineClient(client, 1, lambda: 1).call("thread/read", {})
        self.assertEqual(client.call.call_count, 1)

    def test_long_result_is_explicitly_clipped_with_original_hash(self):
        message = copy.deepcopy(self.message)
        message["item"]["text"] = "x" * 13000
        result = self.run_observer(self.client(entries=[self.envelope, message]))
        self.assertTrue(result["result_message"]["content"]["truncated"])
        self.assertEqual(result["result_message"]["content"]["characters"], 13000)
        self.assertEqual(len(result["result_message"]["content"]["text"]), 12000)
        self.assertEqual(result["result_message"]["id"], "message-001")

    def roundtrip(self, result=None):
        saved = save_result(self.root, result or self.run_observer(self.client()))
        notice = completion_notice(saved)
        received = receive_result(self.root, notice['receipt_path'], THREAD, TURN, PARENT,
                                  notice['receipt_sha256'])
        return saved, notice, received

    def test_notice_has_no_rewritten_business_payload_or_delivery_claim(self):
        saved, notice, received = self.roundtrip()
        self.assertIsNone(saved['notification_route'])
        self.assertFalse(saved['notification_emitted_by_collector'])
        self.assertNotIn('answer', json.dumps(notice))
        self.assertFalse(notice['payload_in_notice'])
        self.assertEqual(received['result_text'], '{"answer": 95}')
        self.assertTrue(received['receipt_integrity_verified'])
        self.assertTrue(received['payload_complete'])
        self.assertFalse(received['delivery_verified'])
        self.assertFalse(received['business_success_inferred'])

    def test_full_json_facts_and_limits_survive_long_unicode_payload(self):
        body = json.dumps({'runs': [{'id': 'r1', 'reason': '原因' * 6500,
                                   'next_action': 'verify original inputs'}],
                           'limits': ['not a visual check'], 'subscription_cost': None}, ensure_ascii=False)
        message = copy.deepcopy(self.message)
        message['item']['text'] = body
        saved, notice, received = self.roundtrip(self.run_observer(self.client(entries=[self.envelope, message])))
        self.assertTrue(saved['result_message']['content']['truncated'])
        self.assertEqual(received['result_text'], body)
        self.assertEqual(json.loads(received['result_text'])['limits'], ['not a visual check'])
        self.assertLess(len(json.dumps(notice)), 1800)

    def test_oversized_payload_remains_attention_not_false_complete(self):
        message = copy.deepcopy(self.message)
        message['item']['text'] = 'x' * (MAX_RESULT_BYTES + 1)
        saved, _, received = self.roundtrip(self.run_observer(self.client(entries=[self.envelope, message])))
        self.assertTrue(saved['needs_attention'])
        self.assertIsNone(saved['result_message']['full_text'])
        self.assertFalse(received['payload_complete'])
        self.assertIsNone(received['result_text'])
        self.assertTrue(received['needs_attention'])

    def test_readback_rejects_wrong_parent_turn_and_file_hash(self):
        _, notice, _ = self.roundtrip()
        for parent, turn, digest in [("wrong-parent", TURN, notice['receipt_sha256']),
                                     (PARENT, 'wrong-turn-002', notice['receipt_sha256']),
                                     (PARENT, TURN, '0' * 64)]:
            with self.assertRaises(ValueError):
                receive_result(self.root, notice['receipt_path'], THREAD, turn, parent, digest)

    def test_rewritten_payload_fails_its_original_message_hash(self):
        saved, notice, _ = self.roundtrip()
        path = Path(notice['receipt_path'])
        changed = json.loads(path.read_text('utf-8'))
        changed['result_message']['full_text'] = '{"answer": 96}'
        path.write_text(json.dumps(changed), encoding='utf-8')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, 'message hash'):
            receive_result(self.root, path, THREAD, TURN, PARENT, digest)

    def test_legacy_receipt_read_does_not_rewrite_history_or_trust_old_route(self):
        result = self.run_observer(self.client())
        result['schema'] = 'grok-completion/v1'
        result['notification_route'] = 'native Codex observer final, not MCP send'
        result['result_message'].pop('full_text')
        result['result_message'].pop('payload_complete')
        saved, notice, received = self.roundtrip(result)
        before = Path(notice['receipt_path']).read_bytes()
        again = receive_result(self.root, notice['receipt_path'], THREAD, TURN, PARENT, notice['receipt_sha256'])
        self.assertEqual(before, Path(notice['receipt_path']).read_bytes())
        self.assertEqual(received, again)
        self.assertEqual(received['result_text'], '{"answer": 95}')
        self.assertNotIn('notification_route', received)
        self.assertFalse(received['delivery_verified'])

    def test_clipped_legacy_receipt_and_unverified_dispatch_do_not_pass(self):
        result = self.run_observer(self.client())
        result['schema'] = 'grok-completion/v1'
        result['result_message'].pop('full_text')
        result['result_message']['content']['truncated'] = True
        _, notice, received = self.roundtrip(result)
        self.assertFalse(received['payload_complete'])
        data = json.loads(Path(notice['receipt_path']).read_text('utf-8'))
        data['parent_dispatch_verified'] = False
        Path(notice['receipt_path']).write_text(json.dumps(data), encoding='utf-8')
        digest = hashlib.sha256(Path(notice['receipt_path']).read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, 'parent dispatch'):
            receive_result(self.root, notice['receipt_path'], THREAD, TURN, PARENT, digest)

    def test_timeout_receipt_can_be_received_without_poisoning_final_result(self):
        result = self.run_observer(self.client([('inProgress', None)]), 4)
        _, notice, received = self.roundtrip(result)
        self.assertIn('.attempt-', notice['receipt_path'])
        self.assertEqual(received['attention_reason'], 'observation_timeout')
        self.assertTrue(received['needs_attention'])
        self.assertIsNone(saved_result(self.root, THREAD, TURN, PARENT))

    def test_rpc_timeout_at_deadline_differs_from_early_transport_timeout(self):
        for exhausted in (False, True):
            self.elapsed = 0
            client = self.client()
            def expire(method, params):
                if exhausted:
                    self.elapsed = 20
                raise TimeoutError('synthetic RPC wait')
            client.call.side_effect = expire
            result = self.run_observer(client)
            self.assertEqual(result['status'], 'observation_timeout' if exhausted else 'observer_error')
            self.assertFalse(result['business_success_inferred'])

    def test_legacy_clipped_notice_cannot_hide_the_payload_unknown(self):
        result = self.run_observer(self.client())
        result['schema'] = 'grok-completion/v1'
        result['needs_attention'] = False
        result['result_message'].pop('full_text')
        result['result_message']['content']['truncated'] = True
        _, notice, _ = self.roundtrip(result)
        self.assertTrue(notice['needs_attention'])
        self.assertFalse(notice['payload_complete'])


if __name__ == "__main__":
    unittest.main()
