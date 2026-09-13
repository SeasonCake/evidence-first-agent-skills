import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from grok_codex_bridge.completion import (
    DeadlineClient, observe, parent_dispatched, save_result, saved_result, validate_binding,
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


if __name__ == "__main__":
    unittest.main()
