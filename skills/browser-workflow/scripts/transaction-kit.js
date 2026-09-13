/* Pure plan/check/receipt helpers. No browser access, implicit retry or persistence. */
function createBrowserWorkflowKit() {
  const own = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
  function fields(value, label) {
    if (!value || typeof value !== 'object' || Array.isArray(value) ||
        ![Object.prototype, null].includes(Object.getPrototypeOf(value))) {
      throw new TypeError(`${label} must be a field map`);
    }
    for (const [key, item] of Object.entries(value)) {
      if (!key || ['__proto__', 'prototype', 'constructor'].includes(key) ||
          !(item === null || ['string', 'boolean', 'number'].includes(typeof item)) ||
          (typeof item === 'number' && !Number.isFinite(item))) {
        throw new TypeError(`${label}.${key} must be a finite JSON scalar with a safe key`);
      }
    }
    return { ...value };
  }
  function identifier(value, label) {
    if (typeof value !== 'string' || !value.trim()) throw new TypeError(`${label} is required`);
    return value;
  }
  function prepareBatch(shared, items) {
    const common = fields(shared, 'shared');
    if (!Array.isArray(items) || items.length === 0) throw new TypeError('items must be nonempty');
    const seen = new Set();
    return items.map(item => {
      const key = identifier(item.key, 'key');
      if (seen.has(key)) throw new Error(`duplicate key: ${key}`);
      seen.add(key);
      const owned = { ...common, ...fields(item.owned, 'owned') };
      if (Object.keys(owned).length === 0) throw new Error(`no selected fields: ${key}`);
      const protectedFields = fields(item.protected || {}, 'protected');
      for (const field of Object.keys(protectedFields)) {
        if (own(owned, field)) throw new Error(`owned/protected overlap: ${key}.${field}`);
      }
      return Object.freeze({ key, requirementRevision: identifier(item.requirementRevision, 'requirementRevision'),
        owned: Object.freeze(owned), protected: Object.freeze(protectedFields) });
    });
  }
  function differences(expected, observed) {
    const found = [];
    for (const [field, value] of Object.entries(expected)) {
      if (!observed || !own(observed, field)) found.push({ field, reason: 'missing' });
      else if (observed[field] !== value) found.push({ field, reason: 'mismatch' });
    }
    return found;
  }
  function checkDraft(plan, baseline, draft) {
    if (baseline?.key !== plan.key || draft?.key !== plan.key) {
      return { ok: false, outcome: 'wrong-identity', differences: [] };
    }
    const before = differences(plan.protected, baseline.fields);
    const delta = differences(plan.owned, draft.fields);
    const surrounding = differences(plan.protected, draft.fields);
    const all = [...before.map(x => ({ ...x, area: 'baseline-protected' })),
      ...delta.map(x => ({ ...x, area: 'owned' })),
      ...surrounding.map(x => ({ ...x, area: 'draft-protected' }))];
    return { ok: all.length === 0, outcome: all.length ? 'draft-conflict' : 'ready', differences: all };
  }
  function judgeReadback(plan, baseline, readback, status) {
    if (baseline?.key !== plan.key || readback?.key !== plan.key) {
      return { outcome: 'wrong-identity', next: 'inspect-identity', differences: [] };
    }
    if (status?.authoritative !== true || status?.settled !== true) {
      return { outcome: 'unknown', next: 'read-only-check', differences: [] };
    }
    const protectedBefore = differences(plan.protected, baseline.fields);
    const protectedAfter = differences(plan.protected, readback.fields);
    const delta = differences(plan.owned, readback.fields);
    if (protectedBefore.length || protectedAfter.length) {
      return { outcome: 'conflict', next: 'inspect-surrounding',
        differences: [...protectedBefore.map(x => ({ ...x, area: 'baseline-protected' })),
          ...protectedAfter.map(x => ({ ...x, area: 'readback-protected' }))] };
    }
    if (!delta.length) {
      return { outcome: differences(plan.owned, baseline.fields).length ? 'verified' : 'unchanged',
        next: 'done', differences: [] };
    }
    const baselineOwned = {};
    for (const field of Object.keys(plan.owned)) {
      if (!baseline.fields || !own(baseline.fields, field)) {
        return { outcome: 'unknown', next: 'inspect-baseline', differences: [{ field, reason: 'missing-baseline' }] };
      }
      baselineOwned[field] = baseline.fields[field];
    }
    const identicalToBaseline = differences(baselineOwned, readback.fields).length === 0;
    return { outcome: identicalToBaseline ? 'not-saved' : 'conflict',
      next: identicalToBaseline ? 'consider-narrow-retry' : 'inspect-partial-state', differences: delta };
  }
  function summarize(rows) {
    if (!Array.isArray(rows)) throw new TypeError('rows must be an array');
    const seen = new Set();
    const outcomes = { verified: 0, unchanged: 0, 'not-saved': 0, conflict: 0, unknown: 0, 'wrong-identity': 0, 'draft-conflict': 0 };
    const items = rows.map(row => {
      const key = identifier(row.key, 'key');
      const revision = identifier(row.requirementRevision, 'requirementRevision');
      if (seen.has(key)) throw new Error(`duplicate current result: ${key}; retain older revisions in history`);
      seen.add(key);
      if (!own(outcomes, row.outcome)) throw new Error(`unsupported outcome: ${row.outcome}`);
      if (!Number.isSafeInteger(row.saveAttempts) || row.saveAttempts < 0) throw new Error('invalid saveAttempts');
      if (['verified', 'unchanged'].includes(row.outcome) &&
          (row.authoritative !== true || row.settled !== true || typeof row.evidence !== 'string' || !row.evidence.trim())) {
        throw new Error('verified results require settled authoritative evidence');
      }
      outcomes[row.outcome]++;
      return { key, requirementRevision: revision, outcome: row.outcome, saveAttempts: row.saveAttempts,
        evidence: typeof row.evidence === 'string' ? row.evidence : null,
        next: typeof row.next === 'string' ? row.next : null };
    });
    return { complete: items.length > 0 && outcomes.verified + outcomes.unchanged === items.length,
      itemCount: items.length, saveAttempts: items.reduce((n, row) => n + row.saveAttempts, 0), outcomes, items };
  }
  return Object.freeze({ prepareBatch, checkDraft, judgeReadback, summarize });
}
if (typeof module !== 'undefined' && module.exports) module.exports = { createBrowserWorkflowKit };
