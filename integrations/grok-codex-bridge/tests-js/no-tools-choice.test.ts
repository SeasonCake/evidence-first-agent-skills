import {expect,test} from 'bun:test';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const root=process.env.GROK_BRIDGE_OCX_ROOT;
if(!root) throw new Error('Set GROK_BRIDGE_OCX_ROOT to the inspected opencodex package');
process.env.OPENCODEX_HOME=import.meta.dir+'/../../../outputs/grok-offline';
globalThis.fetch=async()=>{throw new Error('Offline installed smoke forbids network');};
const {createResponsesPassthroughAdapter}=await import(root+'/src/adapters/openai-responses.ts');
const {parseRequest}=await import(root+'/src/responses/parser.ts');
function wire(raw:any,baseUrl='https://cli-chat-proxy.grok.com/v1'){
 const request=createResponsesPassthroughAdapter({baseUrl,authMode:'oauth',supportsOpenAiWebSearchToolFields:false}).buildRequest(parseRequest(raw),{headers:new Headers(),translatorBudget:{observeExternallyCapped:()=>()=>{}}});
 const body=JSON.parse(request.body);request.releaseBodyObservation?.();return body;
}
const base={model:'grok-4.6',input:[{role:'user',content:'Synthetic rollout smoke.'}],stream:false};
for(const choice of ['auto','none']){
 for(const tools of [undefined,[]]) test('installed absent/empty tools '+choice+' '+String(tools),()=>expect(wire({...base,tools,tool_choice:choice})).not.toHaveProperty('tool_choice'));
 test('installed real catalog '+choice,()=>{const body=wire({...base,tools:[{type:'function',name:'fixture',parameters:{type:'object',properties:{}}}],tool_choice:choice});expect(body.tools).toHaveLength(1);expect(body.tool_choice).toBe(choice);});
}
test('required remains invalid instead of silently successful prose',()=>expect(wire({...base,tools:[],tool_choice:'required'}).tool_choice).toBe('none'));
test('explicit compaction remains without tools or choice',()=>{const body=wire({...base,tool_choice:'auto',tools:[],input:[...base.input,{type:'compaction_trigger'}]});expect(body).not.toHaveProperty('tool_choice');expect(body).not.toHaveProperty('tools');});
test('plain checkpoint summary',()=>expect(wire({...base,tool_choice:'auto',input:[{role:'user',content:'You are performing a CONTEXT CHECKPOINT COMPACTION.'}]})).not.toHaveProperty('tool_choice'));
for(const url of ['https://api.openai.com/v1','https://api.x.ai.evil.test/v1','http://api.x.ai/v1','https://api.x.ai:8443/v1'])test('other destination untouched '+url,()=>expect(wire({...base,tool_choice:'none'},url).tool_choice).toBe('none'));
test('loaded installed bytes and candidate helper text match',()=>{
 expect(createHash('sha256').update(readFileSync(root+'/src/adapters/openai-responses.ts')).digest('hex')).toBe('603a67c1a68133e4259df5a74c611c3aef19c119bc28327b35cee64863f28ac4');
 const candidate=readFileSync(import.meta.dir+'/../compat/xai-no-tools-choice.ts','utf8').replaceAll('\r\n','\n');
 expect(readFileSync(root+'/src/adapters/xai-no-tools-choice.ts','utf8').replaceAll('\r\n','\n')).toBe(candidate);
});
