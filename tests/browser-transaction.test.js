const test = require('node:test');
const assert = require('node:assert/strict');
const { createBrowserWorkflowKit } = require('../skills/browser-workflow/scripts/transaction-kit.js');

const kit = createBrowserWorkflowKit();
const plan = kit.prepareBatch({ title: 'new' }, [{key: 'item-a', owned: {quantity: 0},
  protected: {price: 12}, requirementRevision: 'revision-a'}])[0];
const before = {key: 'item-a', fields: {title: 'old', quantity: 1, price: 12}};
const desired = {key: 'item-a', fields: {title: 'new', quantity: 0, price: 12}};
const settled = {authoritative: true, settled: true};

test('a complete owned delta with unchanged surrounding fields is ready', () => {
  assert.equal(kit.checkDraft(plan, before, desired).ok, true);
  assert.equal(kit.judgeReadback(plan, before, desired, settled).outcome, 'verified');
});
test('zero quantity is not equivalent to a string or missing field', () => {
  for (const fields of [{title:'new',price:12}, {title:'new',quantity:'0',price:12}])
    assert.equal(kit.checkDraft(plan, before, {key:'item-a',fields}).ok, false);
});
test('wrong identity and changed surrounding fields stop the item', () => {
  assert.equal(kit.checkDraft(plan,before,{...desired,key:'item-b'}).outcome,'wrong-identity');
  assert.equal(kit.judgeReadback(plan,before,{...desired,fields:{...desired.fields,price:99}},settled).outcome,'conflict');
});
test('pending or unauthoritative save is not a retry instruction', () => {
  for (const status of [{}, {authoritative:true,settled:false}])
    assert.deepEqual(kit.judgeReadback(plan,before,before,status),{outcome:'unknown',next:'read-only-check',differences:[]});
});
test('unchanged baseline after settled save differs from partial state', () => {
  assert.equal(kit.judgeReadback(plan,before,before,settled).outcome,'not-saved');
  assert.equal(kit.judgeReadback(plan,before,{...before,fields:{...before.fields,title:'new'}},settled).outcome,'conflict');
});
test('already desired state does not invent a save', () => {
  assert.equal(kit.judgeReadback(plan,desired,desired,settled).outcome,'unchanged');
});
test('non-JSON field maps and conflicting ownership are rejected', () => {
  assert.throws(()=>kit.prepareBatch(new Date(),[{key:'a',owned:{title:'x'},requirementRevision:'a'}]),TypeError);
  assert.throws(()=>kit.prepareBatch({},[{key:'a',owned:{title:'x'},protected:{title:'y'},requirementRevision:'a'}]));
  assert.throws(()=>kit.prepareBatch({},[{key:'a',owned:{quantity:NaN},requirementRevision:'a'}]));
});
test('summaries require evidence and keep one current row per business key', () => {
  const row={key:'item-a',requirementRevision:'a',outcome:'verified',saveAttempts:1,
    authoritative:true,settled:true,evidence:'synthetic-readback'};
  assert.equal(kit.summarize([row]).complete,true);
  assert.throws(()=>kit.summarize([row,{...row,requirementRevision:'b'}]));
  assert.throws(()=>kit.summarize([{...row,evidence:''}]));
  assert.equal(kit.summarize([]).complete,false);
});
