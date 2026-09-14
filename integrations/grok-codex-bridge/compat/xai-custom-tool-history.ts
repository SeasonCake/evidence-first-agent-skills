import { createHash } from 'node:crypto';

/**
 * xAI requires an item id for custom-tool calls replayed without a tool catalog
 * (for example Codex's compact request). Generic store:false sanitization can
 * remove it. Add only missing item metadata at the final xAI wire boundary;
 * call_id remains the authoritative call/output pairing key.
 */
export function normalizeXaiCustomToolHistory(body: unknown, isXaiDestination: boolean): unknown {
  if (!isXaiDestination || !body || typeof body !== 'object' || Array.isArray(body)) return body;
  const record = body as Record<string, unknown>;
  if (!Array.isArray(record.input)) return body;
  const used = new Set(record.input.flatMap(item =>
    item && typeof item === 'object' && typeof item.id === 'string' ? [item.id] : []));
  let changed = false;
  const input = record.input.map(item => {
    if (!item || typeof item !== 'object' || Array.isArray(item)
        || item.type !== 'custom_tool_call' || Object.hasOwn(item, 'id')
        || typeof item.call_id !== 'string' || item.call_id.length === 0
        || typeof item.name !== 'string' || item.name.length === 0
        || typeof item.input !== 'string') return item;
    const digest = createHash('sha256').update(item.call_id).digest('hex').slice(0, 40);
    const base = `ctc_${digest}`;
    let id = base;
    let suffix = 0;
    while (used.has(id)) id = `${base}_${++suffix}`;
    used.add(id);
    changed = true;
    return { ...item, id };
  });
  return changed ? { ...record, input } : body;
}
