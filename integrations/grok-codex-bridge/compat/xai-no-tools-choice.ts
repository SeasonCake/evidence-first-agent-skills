/**
 * Candidate xAI wire compatibility: auto/none select no capability when the
 * request has no declared tools. Remove only that redundant selector.
 * Caller supplies the existing exact xAI-destination predicate.
 */
export function normalizeXaiNoToolsChoice(body: unknown, isXaiDestination: boolean, originalChoice?: unknown): unknown {
  if (!isXaiDestination || !body || typeof body !== 'object' || Array.isArray(body)) return body;
  // Earlier transforms can rewrite an unsatisfied required selector to "none".
  // Keep that request rejected instead of making it a valid no-tool request.
  if (originalChoice !== undefined && originalChoice !== 'auto' && originalChoice !== 'none') return body;
  const record = body as Record<string, unknown>;
  if (record.tool_choice !== 'auto' && record.tool_choice !== 'none') return body;

  // Nonempty or malformed tool catalogs remain untouched, including required/
  // named/allowed-tools choices handled by the early return above.
  if (Object.hasOwn(record, 'tools') && record.tools !== undefined
      && (!Array.isArray(record.tools) || record.tools.length !== 0)) return body;
  if (Array.isArray(record.input) && record.input.some(item => {
    if (!item || typeof item !== 'object' || Array.isArray(item)) return false;
    const entry = item as Record<string, unknown>;
    return entry.type === 'additional_tools'
      && (!Array.isArray(entry.tools) || entry.tools.length !== 0);
  })) return body;

  const result = { ...record };
  delete result.tool_choice;
  return result;
}
