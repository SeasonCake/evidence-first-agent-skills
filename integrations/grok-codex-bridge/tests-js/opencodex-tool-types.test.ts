import { expect, test } from "bun:test";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const root = process.env.GROK_BRIDGE_OCX_ROOT;
if (!root) throw new Error("Set GROK_BRIDGE_OCX_ROOT to the selected local opencodex package");
const { collectFunctionCallRepairSchemas, repairFunctionCalls } = await import(
  pathToFileURL(join(root, "src/responses/function-call-compat.ts")).href);
const { createResponsesFunctionToolRepairBlockRewrite } = await import(
  pathToFileURL(join(root, "src/server/responses-function-tool-repair.ts")).href);

function schema(name: string, field: string, type: unknown = "number", namespace?: string) {
  const tool = { type: "function", name, parameters: { type: "object", properties: { [field]: { type } } } };
  return collectFunctionCallRepairSchemas({ tools: namespace ? [{ type: "namespace", name: namespace, tools: [tool] }] : [tool] });
}

function item(name: string, args: string, namespace?: string, status = "completed") {
  return { type: "function_call", id: "fc-synthetic", name, status, arguments: args,
    ...(namespace ? { namespace } : {}) };
}

test("native write_stdin session_id integral float has the same integer value", () => {
  const result = repairFunctionCalls(item("write_stdin", '{"session_id":97968.0}'), schema("write_stdin", "session_id"));
  expect(result.value.arguments).toBe('{"session_id":97968}');
});

test("native exec_command yield_time_ms integral float is not rounded or truncated", () => {
  const result = repairFunctionCalls(item("exec_command", '{"yield_time_ms":30000.0}'), schema("exec_command", "yield_time_ms"));
  expect(result.value.arguments).toBe('{"yield_time_ms":30000}');
});

test("exact MCP app wait timeout numeric string has one safe integral reading", () => {
  const result = repairFunctionCalls(item("wait_threads", '{"timeoutMs":"60000"}', "mcp__codex_app"),
    schema("wait_threads", "timeoutMs", "number", "mcp__codex_app"));
  expect(result.value.arguments).toBe('{"timeoutMs":60000}');
});

test("captured wait wire shape uses MCP namespace and zero-only decimal string", () => {
  const result = repairFunctionCalls(item("wait_threads", '{"timeoutMs":"120000.0"}', "mcp__codex_app"),
    schema("wait_threads", "timeoutMs", "number", "mcp__codex_app"));
  expect(result.value.arguments).toBe('{"timeoutMs":120000}');
});

test("coordinator envelope namespace is not the executable MCP tool namespace", () => {
  const value = item("wait_threads", '{"timeoutMs":"60000"}', "codex_app");
  expect(repairFunctionCalls(value, schema("wait_threads", "timeoutMs", "number", "codex_app")).value).toBe(value);
});

test("a namespaced third-party tool with the same bare name is unchanged", () => {
  const value = item("write_stdin", '{"session_id":12.0}', "third_party");
  const result = repairFunctionCalls(value, schema("write_stdin", "session_id", "number", "third_party"));
  expect(result.changed).toBe(false);
  expect(result.value).toBe(value);
});

test("fractional native fields remain invalid instead of being truncated", () => {
  const value = item("write_stdin", '{"session_id":12.5}');
  expect(repairFunctionCalls(value, schema("write_stdin", "session_id")).value).toBe(value);
});

test("unrelated numeric field with the same property name remains unchanged", () => {
  const value = item("animation", '{"yield_time_ms":12.0}');
  expect(repairFunctionCalls(value, schema("animation", "yield_time_ms")).value).toBe(value);
});

test("string-only schema is not overridden by a native field-name match", () => {
  const value = item("wait_threads", '{"timeoutMs":"60000"}', "mcp__codex_app");
  expect(repairFunctionCalls(value, schema("wait_threads", "timeoutMs", "string", "mcp__codex_app")).value).toBe(value);
});

test("ambiguous union numeric strings are not coerced", () => {
  const value = item("wait_threads", '{"timeoutMs":"60000"}', "mcp__codex_app");
  expect(repairFunctionCalls(value, schema("wait_threads", "timeoutMs", ["number", "string"], "mcp__codex_app")).value).toBe(value);
});

test("fractional, padded, exponent and unsafe numeric strings remain unchanged", () => {
  for (const text of ["1.5", "060000", " 60000", "6e4", "9007199254740993", "001.0", "60000.01", "-0.0"]) {
    const value = item("wait_threads", JSON.stringify({ timeoutMs: text }), "mcp__codex_app");
    expect(repairFunctionCalls(value, schema("wait_threads", "timeoutMs", "number", "mcp__codex_app")).value).toBe(value);
  }
});

test("unsafe sibling integer prevents reserialization of the entire argument object", () => {
  const value = item("exec_command", '{"yield_time_ms":30000.0,"opaque_id":9007199254740993}');
  expect(repairFunctionCalls(value, schema("exec_command", "yield_time_ms")).value).toBe(value);
});

test("undeclared function and mismatched namespace remain unmodified", () => {
  const value = item("write_stdin", '{"session_id":97968.0}', "unknown");
  expect(repairFunctionCalls(value, schema("write_stdin", "session_id")).value).toBe(value);
});

test("in-progress or failed calls are not executable completions to repair", () => {
  for (const status of ["in_progress", "failed", "incomplete", "cancelled"]) {
    const value = item("exec_command", '{"yield_time_ms":30000.0}', undefined, status);
    expect(repairFunctionCalls(value, schema("exec_command", "yield_time_ms")).value).toBe(value);
  }
});

test("explicit integer schema continues to normalize nested integer representation", () => {
  const result = repairFunctionCalls(item("fixture", '{"count":2.0}'), schema("fixture", "count", "integer"));
  expect(result.value.arguments).toBe('{"count":2}');
});

test("SSE authoritative arguments completion is normalized, previews stay unchanged", () => {
  const rewrite = createResponsesFunctionToolRepairBlockRewrite(schema("write_stdin", "session_id"));
  const added = 'data: ' + JSON.stringify({ type: "response.output_item.added", output_index: 0,
    item: item("write_stdin", "", undefined, "in_progress") }) + '\n\n';
  rewrite(added);
  const delta = 'data: ' + JSON.stringify({ type: "response.function_call_arguments.delta",
    item_id: "fc-synthetic", output_index: 0, delta: '{"session_id":97968.0}' }) + '\n\n';
  expect(rewrite(delta)).toEqual([delta]);
  const done = 'data: ' + JSON.stringify({ type: "response.function_call_arguments.done",
    item_id: "fc-synthetic", output_index: 0, arguments: '{"session_id":97968.0}' }) + '\n\n';
  const result = JSON.parse(rewrite(done)[0].slice(6).trim());
  expect(result.arguments).toBe('{"session_id":97968}');
});

test("SSE MCP completion preserves namespace and repairs captured decimal string", () => {
  const rewrite = createResponsesFunctionToolRepairBlockRewrite(
    schema("wait_threads", "timeoutMs", "number", "mcp__codex_app"));
  rewrite('data: ' + JSON.stringify({ type: "response.output_item.added", output_index: 0,
    item: item("wait_threads", "", "mcp__codex_app", "in_progress") }) + '\n\n');
  const done = 'data: ' + JSON.stringify({ type: "response.function_call_arguments.done",
    item_id: "fc-synthetic", output_index: 0, arguments: '{"timeoutMs":"120000.0"}' }) + '\n\n';
  const result = JSON.parse(rewrite(done)[0].slice(6).trim());
  expect(result.arguments).toBe('{"timeoutMs":120000}');
});
