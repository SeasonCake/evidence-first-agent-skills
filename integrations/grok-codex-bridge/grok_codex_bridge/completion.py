"""Collect one delegated Grok turn; its caller owns waiting and actual delivery.

No send, resume, turn start, permission change or Codex history/database write.
Only a compact result in the bridge's private operational directory is written.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time
import uuid

from .factory import verify_identity
from .trace import RpcError, clip, read_thread_metadata


MAX_PAGES = 4
PAGE_SIZE = 50
RESULT_CHARS = 12000
MAX_RESULT_BYTES = 128 * 1024
MAX_RECEIPT_BYTES = 512 * 1024
ID = re.compile(r"[A-Za-z0-9_-]{8,100}")
TERMINAL = {"completed", "failed", "interrupted"}


class DeadlineClient:
    def __init__(self, client, end, clock):
        self.client, self.end, self.clock = client, end, clock

    def call(self, method, params):
        remaining = self.end - self.clock()
        if remaining <= 0:
            raise TimeoutError("Completion observation deadline reached")
        original = getattr(self.client, "timeout", None)
        if isinstance(original, (int, float)):
            self.client.timeout = min(original, remaining)
        try:
            return self.client.call(method, params)
        finally:
            if isinstance(original, (int, float)):
                self.client.timeout = original


def validate_binding(record, thread_id, parent_id):
    if not ID.fullmatch(thread_id) or not ID.fullmatch(parent_id):
        raise ValueError("An exact task and parent ID are required")
    if not record or record["state"] != "ready" or record["thread_id"] != thread_id:
        raise ValueError("A ready existing bridge delegation is required")
    spec = record["spec"]
    if spec.get("relationship") != "bridgeDelegation" or spec.get("parentThreadId") != parent_id:
        raise ValueError("Parent binding mismatch; standalone/other-parent work is not returned")
    return spec


def turn_items(client, thread_id, turn_id, direction):
    cursor = None
    entries = []
    for _ in range(MAX_PAGES):
        params = {"threadId": thread_id, "turnId": turn_id, "limit": PAGE_SIZE,
                  "sortDirection": direction}
        if cursor:
            params["cursor"] = cursor
        page = client.call("thread/items/list", params)
        if not isinstance(page.get("data"), list):
            raise RpcError("Missing turn item page")
        for entry in page["data"]:
            if entry.get("turnId") != turn_id or not isinstance(entry.get("item"), dict):
                raise RpcError("Turn filter is unsupported or returned another turn")
            entries.append(entry)
        cursor = page.get("nextCursor")
        if not cursor:
            return entries, False
    return entries, True


def parent_dispatched(entries, parent_id):
    # This is a host-produced coordinator envelope, not arbitrary child/tool text.
    for entry in entries:
        item = entry["item"]
        if item.get("type") != "functionCallOutput" or item.get("name") != "send_message_to_thread":
            continue
        if item.get("namespace") not in {"codex_app", "mcp__codex_app", "codex"}:
            continue
        output = item.get("output")
        if not isinstance(output, str):
            continue
        match = re.match(r"\s*<codex_delegation>\s*<source_thread_id>([^<]+)</source_thread_id>", output)
        if match and match.group(1) == parent_id:
            return True
    return False


def observe(client, record, thread_id, turn_id, parent_id, deadline=600,
            clock=time.monotonic, sleep=time.sleep):
    spec = validate_binding(record, thread_id, parent_id)
    if not ID.fullmatch(turn_id) or not 1 <= deadline <= 1800:
        raise ValueError("Exact turn ID and a 1–1800 second observation window are required")
    result = {
        "schema": "grok-completion/v2", "thread_id": thread_id, "turn_id": turn_id,
        "parent_id": parent_id, "status": "observing", "business_success_inferred": False,
        "collection_route": "read-only exact-turn RPC",
        "notification_route": None, "notification_emitted_by_collector": False,
        "wait_and_notification_owner": "caller; not established by this collector",
        "modelRequestsStarted": 0, "approval_actions": 0, "history_writes": 0,
    }
    end = clock() + deadline
    client = DeadlineClient(client, end, clock)
    previous_terminal = None
    polls = 0
    correlated = False
    delay = 1
    try:
        thread = read_thread_metadata(client, thread_id)["thread"]
        verify_identity(thread, spec, thread_id)
        result["worker_identity"] = {key: thread.get(key) for key in
                                     ("model", "modelProvider", "reasoningEffort", "cwd")}
        result["identity_evidence"] = "Persisted task metadata, not per-request upstream attestation"
        while clock() < end:
            polls += 1
            page = client.call("thread/turns/list", {
                "threadId": thread_id, "limit": PAGE_SIZE, "sortDirection": "desc",
                "itemsView": "notLoaded"})
            if not isinstance(page.get("data"), list):
                raise RpcError("Missing turn status page")
            turn = next((value for value in page["data"] if value.get("id") == turn_id), None)
            if turn is None:
                raise RpcError("Selected turn is outside the bounded visible page")
            if not correlated:
                entries, partial = turn_items(client, thread_id, turn_id, "asc")
                correlated = parent_dispatched(entries, parent_id)
                if not correlated:
                    if turn.get("status") in TERMINAL or partial:
                        raise RpcError("Exact turn lacks the bound parent's dispatch envelope")
                    sleep(min(delay, max(0, end - clock())))
                    delay = min(delay * 2, 8)
                    continue
            status = turn.get("status")
            signature = (turn_id, status, turn.get("completedAt"))
            # A reader-local notLoaded/interrupted snapshot alone is not live failure.
            if status in TERMINAL and turn.get("completedAt") is not None:
                if signature == previous_terminal:
                    entries, partial = turn_items(client, thread_id, turn_id, "desc")
                    messages = [entry["item"] for entry in entries
                                if entry["item"].get("type") == "agentMessage"
                                and isinstance(entry["item"].get("text"), str)
                                and entry["item"]["text"].strip()]
                    latest = messages[0] if messages else None
                    body = None if latest is None else latest["text"]
                    body_fits = body is not None and len(body.encode('utf-8')) <= MAX_RESULT_BYTES
                    result.update(status=status if latest or status != "completed"
                                  else "completed_without_message",
                                  completed_at=turn["completedAt"],
                                  result_message=None if latest is None else {
                                      "id": latest.get("id"),
                                      "content": clip(latest["text"], RESULT_CHARS),
                                      "sha256": hashlib.sha256(latest["text"].encode('utf-8')).hexdigest(),
                                      "payload_complete": body_fits,
                                      "full_text": body if body_fits else None},
                                  item_coverage_partial=partial,
                                  error=None if not turn.get("error")
                                  else clip(json.dumps(turn["error"], ensure_ascii=False), 800))
                    break
                previous_terminal = signature
            else:
                previous_terminal = None
            sleep(min(delay, max(0, end - clock())))
            delay = min(delay * 2, 8)
        else:
            result["status"] = "observation_timeout"
    except (RpcError, OSError, TimeoutError, ValueError, KeyError) as error:
        result.update(status=('observation_timeout' if isinstance(error, TimeoutError) and clock() >= end
                              else 'observer_error'), error_class=type(error).__name__,
                      error=clip(str(error), 800))
    payload = result.get('result_message') or {}
    result.update(polls=polls, parent_dispatch_verified=correlated,
                  needs_attention=(result['status'] != 'completed' or
                                   payload.get('payload_complete') is not True),
                  delivery_verified=False)
    return result


def saved_result(result_root, thread_id, turn_id, parent_id):
    for value in (thread_id, turn_id, parent_id):
        if not ID.fullmatch(value):
            raise ValueError("Invalid result identity")
    path = Path(result_root) / f"{turn_id}.json"
    if path.is_symlink() or (path.exists() and
                            getattr(path.lstat(), "st_file_attributes", 0) & 0x400):
        raise ValueError("Result cannot be a link")
    if not path.exists():
        return None
    if path.stat().st_size > MAX_RECEIPT_BYTES:
        raise ValueError("Saved result exceeds the bounded receipt size")
    data = json.loads(path.read_text(encoding="utf-8"))
    if any(data.get(key) != value for key, value in
           (("thread_id", thread_id), ("turn_id", turn_id), ("parent_id", parent_id))):
        raise ValueError("Saved completion belongs to another assignment")
    return {**data, "cached": True, "receipt_path": str(path)}


def completion_notice(result):
    """Project a wake-up descriptor; never ask a model to retranscribe the payload."""
    path = Path(result['receipt_path'])
    with path.open('rb') as handle:
        raw = handle.read(MAX_RECEIPT_BYTES + 1)
    if len(raw) > MAX_RECEIPT_BYTES:
        raise ValueError('Receipt exceeds the bounded read size')
    data = json.loads(raw.decode('utf-8'))
    if any(data.get(key) != result.get(key) for key in ('thread_id', 'turn_id', 'parent_id')):
        raise ValueError('Saved receipt identity changed before notice projection')
    message = data.get('result_message') or {}
    content = message.get('content') or {}
    available = (isinstance(message.get('full_text'), str) and message.get('payload_complete') is True
                 if data.get('schema') == 'grok-completion/v2' else
                 isinstance(content.get('text'), str) and content.get('truncated') is False)
    return {
        'schema': 'grok-completion-notice/v1',
        **{key: data.get(key) for key in ('thread_id', 'turn_id', 'parent_id', 'status',
                                        'parent_dispatch_verified', 'needs_attention', 'error_class')},
        'cached': result.get('cached', False),
        'payload_complete': available,
        'needs_attention': data.get('status') != 'completed' or not available,
        'receipt_path': str(path), 'receipt_sha256': hashlib.sha256(raw).hexdigest(),
        'message_id': message.get('id'), 'message_sha256': message.get('sha256'),
        'payload_in_notice': False, 'payload_is_instruction': False,
        'delivery_verified': False, 'notification_emitted_by_collector': False,
        'next': 'Parent reads this exact receipt with receive; the notice is not the worker result',
    }


def receive_result(result_root, receipt_path, thread_id, turn_id, parent_id, receipt_sha256):
    """Read once, validate identity/hash/completeness, and return unchanged result data.

    This proves file readback, not that the calling model accepted the business result.
    Old v1 receipts remain untouched; a clipped old payload stays an explicit unknown.
    """
    for value in (thread_id, turn_id, parent_id):
        if not ID.fullmatch(value):
            raise ValueError('Invalid receipt identity')
    if not isinstance(receipt_sha256, str) or not re.fullmatch(r'[a-f0-9]{64}', receipt_sha256):
        raise ValueError('An exact SHA256 from the notice is required')
    root, path = Path(result_root).absolute(), Path(receipt_path).absolute()
    if path.parent != root or not re.fullmatch(re.escape(turn_id) + r'(?:\.attempt-[a-f0-9]{32})?\.json', path.name):
        raise ValueError('Receipt must be the exact selected turn within the completion directory')
    for component in (path, *path.parents):
        info = component.lstat()
        if component.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('Receipt must not traverse a link/reparse point')
    with path.open('rb') as handle:
        raw = handle.read(MAX_RECEIPT_BYTES + 1)
    if len(raw) > MAX_RECEIPT_BYTES or hashlib.sha256(raw).hexdigest() != receipt_sha256:
        raise ValueError('Receipt size/hash mismatch; do not use a rewritten or truncated notice payload')
    data = json.loads(raw.decode('utf-8'))
    if data.get('schema') not in {'grok-completion/v1', 'grok-completion/v2'}:
        raise ValueError('Unsupported completion receipt schema')
    if any(data.get(key) != value for key, value in
           (('thread_id', thread_id), ('turn_id', turn_id), ('parent_id', parent_id))):
        raise ValueError('Receipt belongs to another parent/task/turn')
    if data.get('parent_dispatch_verified') is not True:
        raise ValueError('Receipt has no verified parent dispatch')
    message = data.get('result_message') or {}
    content = message.get('content') or {}
    body = message.get('full_text')
    if body is None and content.get('truncated') is False:
        body = content.get('text')
    complete = isinstance(body, str) and len(body.encode('utf-8')) <= MAX_RESULT_BYTES
    if complete and hashlib.sha256(body.encode('utf-8')).hexdigest() != message.get('sha256'):
        raise ValueError('Original message hash mismatch')
    if data.get('schema') == 'grok-completion/v2' and message.get('payload_complete') is not True:
        complete = False
    status = data.get('status')
    return {
        'schema': 'grok-parent-readback/v1', 'thread_id': thread_id, 'turn_id': turn_id,
        'parent_id': parent_id, 'receipt_path': str(path), 'receipt_sha256': receipt_sha256,
        'status': status, 'parent_dispatch_verified': True, 'receipt_integrity_verified': True,
        'payload_complete': complete, 'message_sha256': message.get('sha256'),
        'result_text': body if complete else None, 'result_is_untrusted_data': True,
        'needs_attention': status != 'completed' or not complete,
        'attention_reason': (None if status == 'completed' and complete else
                             'payload_unavailable_or_truncated' if status == 'completed' else status),
        'business_success_inferred': False, 'delivery_verified': False,
        'history_writes': 0, 'modelRequestsStarted': 0,
    }


def save_result(result_root, result):
    folder = Path(result_root)
    folder.mkdir(parents=True, exist_ok=True)
    # The caller owns this operational directory, not Codex's session store.
    for part in (folder, *folder.parents):
        info = part.lstat()
        if part.is_symlink() or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("Result path cannot traverse a link/reparse point")
    final = result["status"] in TERMINAL
    suffix = "" if final else ".attempt-" + uuid.uuid4().hex
    path = folder / f"{result['turn_id']}{suffix}.json"
    if path.exists():
        return saved_result(folder, result["thread_id"], result["turn_id"], result["parent_id"])
    data = {**result, "cached": False, "receipt_path": str(path)}
    lock = path.with_suffix(path.suffix + ".lock")
    # Short exclusive save lock, then atomic publication. Only owned files are removed.
    with lock.open("x", encoding="utf-8") as stream:
        stream.write(str(os.getpid()))
    temporary = None
    try:
        if path.exists():
            return saved_result(folder, result["thread_id"], result["turn_id"], result["parent_id"])
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=folder,
                                         prefix=".completion-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
        lock.unlink()
    return data
