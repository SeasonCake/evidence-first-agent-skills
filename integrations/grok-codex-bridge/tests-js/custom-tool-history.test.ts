import { expect, test } from 'bun:test';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { plugin } from 'bun';
import { normalizeXaiCustomToolHistory as normalize } from '../compat/xai-custom-tool-history';

const call = {type:'custom_tool_call', call_id:'call_synthetic_1', name:'exec', input:'text(17 * 19);'};
const output = {type:'custom_tool_call_output', call_id:call.call_id, output:'323'};
test('missing xAI item id is filled without changing pairing or source input', () => {
  const original = Object.freeze({...call});
  const body = Object.freeze({input:Object.freeze([original, Object.freeze({...output})]), store:false, tool_choice:'none'});
  const result = normalize(body,true) as any;
  expect(result.input[0].id).toMatch(/^ctc_[a-f0-9]{40}$/);
  const {id, ...unchanged} = result.input[0];
  expect(unchanged).toEqual(call);
  expect(result.input[1]).toBe(body.input[1]);
  expect(result.store).toBe(false);
  expect(result.tool_choice).toBe('none');
  expect(body.input[0]).not.toHaveProperty('id');
  expect(normalize(result,true)).toBe(result);
  expect((normalize(body,true) as any).input[0].id).toBe(id);
});
test('valid, malformed, unrelated and incomplete entries are not repaired', () => {
  for (const item of [{...call,id:'ctc_existing'}, {...call,id:null}, {...call,id:''},
    {...call,input:null}, {...call,name:''}, {...call,call_id:''}, {...call,type:'function_call'}, output]) {
    const body = {input:[item]};
    expect(normalize(body,true)).toBe(body);
  }
  for (const body of [null, [], 0, 'prompt', {}, {input:'text'}, {input:null}]) {
    expect(normalize(body,true)).toBe(body);
  }
});
test('other destinations and required choice remain unchanged', () => {
  const body = {input:[call,output],tool_choice:'required',tools:[],metadata:{test:'synthetic'}};
  expect(normalize(body,false)).toBe(body);
  const result = normalize(body,true) as any;
  expect(result.tool_choice).toBe('required');
  expect(result.tools).toBe(body.tools);
  expect(result.metadata).toBe(body.metadata);
});
test('generated ids avoid existing and repeated collisions deterministically', () => {
  const id = `ctc_${createHash('sha256').update(call.call_id).digest('hex').slice(0,40)}`;
  const body = {input:[{...call,id},call,{...call}]};
  const result = normalize(body,true) as any;
  expect(result.input.map((item:any)=>item.id)).toEqual([id,`${id}_1`,`${id}_2`]);
  expect(result.input.map((item:any)=>item.call_id)).toEqual([call.call_id,call.call_id,call.call_id]);
});

// Selected-package tests never make network calls. A before run demonstrates the
// actual adapter's missing-id output; an overlay/installed run checks the fix.
const ocx = process.env.GROK_BRIDGE_OCX_ROOT;
if (!ocx) throw new Error('Set GROK_BRIDGE_OCX_ROOT to the inspected package');
const original = join(ocx,'src/adapters/openai-responses.ts');
const installedBytes = readFileSync(original);
const overlay = process.env.GROK_BRIDGE_ADAPTER_OVERLAY;
const helper = resolve(import.meta.dir,'../compat/xai-custom-tool-history.ts');
if (overlay) plugin({name:'xai-history-selected-overlay',setup(build) {
  build.onLoad({filter:/[/\\]adapters[/\\]openai-responses\.ts$/},args=>{
    if (resolve(args.path) !== resolve(original)) return;
    const source = readFileSync(overlay,'utf8');
    const key = '"./xai-custom-tool-history"';
    if (source.split(key).length !== 2) throw new Error('Expected exactly one helper import');
    return {contents:source.replace(key,JSON.stringify(helper.replaceAll('\\','/'))),loader:'ts'};
  });
}});
globalThis.fetch = async () => { throw new Error('Network forbidden in offline tests'); };
const { createResponsesPassthroughAdapter } = await import(pathToFileURL(original).href);
const { parseRequest } = await import(pathToFileURL(join(ocx,'src/responses/parser.ts')).href);
function wire(raw:any, baseUrl='https://cli-chat-proxy.grok.com/v1', compact=false, authMode='oauth') {
  const provider = {baseUrl,authMode,supportsOpenAiWebSearchToolFields:false};
  const parsed = parseRequest(raw);
  if (compact) parsed._compactionRequest = true;
  const request = createResponsesPassthroughAdapter(provider).buildRequest(parsed,
    {headers:new Headers(),translatorBudget:{observeExternallyCapped:()=>()=>{}}});
  const body = JSON.parse(request.body);
  request.releaseBodyObservation?.();
  return body;
}
const base = {model:'grok-4.6',store:false,stream:false,input:[
  {type:'message',role:'user',content:'Synthetic compact continuity test.'},
  {...call,id:'ctc_original'},output,
  {type:'message',role:'assistant',content:'The answer is 323.'},
]};
for (const compact of [false,true]) test(`actual adapter preserves replay pairing with compact=${compact}`,()=>{
  const body = wire(base,undefined,compact);
  const c = body.input.find((item:any)=>item.type==='custom_tool_call');
  const o = body.input.find((item:any)=>item.type==='custom_tool_call_output');
  expect(c.id).toMatch(/^ctc_[a-f0-9]{40}$/);
  expect(c.call_id).toBe(call.call_id);
  expect(c.input).toBe(call.input);
  expect(o.call_id).toBe(call.call_id);
  expect(o.output).toBe('323');
  expect(body.store).toBe(false);
  expect(base.input[1].id).toBe('ctc_original');
});
for (const host of ['https://example.test/v1','https://api.x.ai.evil.test/v1','http://api.x.ai/v1','https://api.x.ai:8443/v1']) {
  test(`actual adapter does not add metadata for ${host}`,()=>{
    const body = wire(base,host);
    expect(body.input.find((item:any)=>item.type==='custom_tool_call')).not.toHaveProperty('id');
  });
}
test('actual adapter retains ordinary custom-tool lowering and no-tools behavior',()=>{
  const body = wire({...base,tools:[{type:'custom',name:'exec',description:'Synthetic executor'}]});
  const c = body.input.find((item:any)=>item.type==='function_call');
  const o = body.input.find((item:any)=>item.type==='function_call_output');
  expect(JSON.parse(c.arguments)).toEqual({input:call.input});
  expect(o.call_id).toBe(c.call_id);
  expect(body.input.some((item:any)=>item.type==='custom_tool_call')).toBe(false);
  const plain = wire({model:'grok-4.6',input:'Synthetic summary.',tools:[],tool_choice:'auto'});
  expect(plain).not.toHaveProperty('tool_choice');
});
test('actual xAI store:true preserves an existing valid item id',()=>{
  const body=wire({...base,store:true});
  expect(body.input.find((item:any)=>item.type==='custom_tool_call').id).toBe('ctc_original');
});
for (const [destination,authMode] of [['https://api.openai.com/v1','api-key'],
  ['https://chatgpt.com/backend-api/codex','forward']]) {
  test(`actual GPT path does not receive xAI metadata: ${authMode}`,()=>{
    const body=wire({...base,model:'gpt-6-astra'},destination,false,authMode);
    expect(body.input.find((item:any)=>item.type==='custom_tool_call')).not.toHaveProperty('id');
    expect(JSON.stringify(body)).not.toContain('ctc_');
  });
}
test('offline adapter test never edits installed source',()=>{
  expect(readFileSync(original).equals(installedBytes)).toBe(true);
});
