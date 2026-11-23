const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const GraphQA=require('./dist/qa.js');
const data=JSON.parse(fs.readFileSync(__dirname+'/dist/graph.json','utf8'));
const qa=new GraphQA(data),id=name=>data.nodes.find(n=>n.name===name).id;
const hitler=id('Adolf Hitler'),stalin=id('Joseph Stalin');
const ask=q=>qa.answer(q,hitler,stalin);
test('Vietnamese two-hop answer uses both stated entities and original directions',()=>{
 const a=ask('Hitler và Stalin có mối liên hệ gì?');assert.equal(a.kind,'path');assert.equal(a.context.length,2);
 assert.equal(a.context[0].source,'Adolf Hitler');assert.equal(a.context[1].source,'Joseph Stalin');assert.match(a.text,/1941/);assert.match(a.text,/1943/);
 assert.ok(a.context.every(e=>e.url?.startsWith('https://en.wikipedia.org/')));
});
test('empty question retains explicit target-selection workflow',()=>assert.equal(ask('').kind,'path'));
test('declaration question returns outgoing declaration, not invasion or all neighbors',()=>{
 const a=ask('Hitler tuyên chiến với ai năm 1941?');assert.equal(a.kind,'relations');assert.equal(a.context.length,1);
 assert.equal(a.context[0].target,'United States');assert.equal(a.context[0].relation,'DECLARED_WAR_ON');
});
test('unaccented questions work',()=>assert.equal(ask('Hitler tuyen chien voi ai nam 1941?').context.length,1));
test('different question yields a different grounded answer',()=>{
 const a=ask('PageRank của Hitler là bao nhiêu?');assert.equal(a.kind,'ranking');assert.match(a.text,/Adolf Hitler/);assert.equal(a.context.length,0);
 assert.notEqual(a.text,ask('Hitler thuộc cộng đồng nào?').text);
});
test('community membership is read from snapshot',()=>{const a=ask('Hitler thuộc cộng đồng nào?');assert.equal(a.kind,'community');assert.match(a.text,new RegExp('cộng đồng '+(qa.nodes.get(hitler).community+1)))});
test('global ranking and statistics answer without calling an API',()=>{
 assert.equal(ask('Ai có PageRank cao nhất?').kind,'ranking');assert.match(ask('Mạng có bao nhiêu nút và cạnh?').text,/6642/);
});
test('timeline returns only the requested year',()=>{const a=ask('Dòng thời gian của Hitler năm 1941');assert.equal(a.kind,'timeline');assert.ok(a.context.every(e=>e.year===1941))});
test('year-limited path does not mix 1941 and 1943',()=>assert.equal(ask('Hitler và Stalin có liên hệ gì năm 1941?').kind,'not_found'));
test('missing positive evidence cannot establish personal alliance',()=>{const a=ask('Hitler và Stalin có phải đồng minh không?');assert.equal(a.kind,'not_found');assert.match(a.text,/không khẳng định/)});
test('same endpoints and disconnected endpoints are handled',()=>{
 assert.equal(qa.answer('',hitler,hitler).kind,'same_entity');
 const isolated=data.nodes.find(n=>n.degree===0);assert.equal(qa.answer('',hitler,isolated.id).kind,'not_found');
});
test('unknown endpoint cannot silently become Stalin',()=>assert.equal(ask('Hitler và Harry Potter có mối liên hệ gì?').kind,'clarify'));
test('unknown subject cannot silently become current profile',()=>assert.equal(ask('Napoleon có quan hệ với ai?').kind,'clarify'));
test('unsupported facts and out-of-period questions abstain',()=>{
 assert.equal(ask('Hitler sinh ngày nào?').kind,'unsupported');assert.equal(ask('Thời tiết hôm nay?').kind,'unsupported');
 assert.equal(ask('Hitler có quan hệ gì năm 1920?').kind,'unsupported');
});
test('ambiguous party names request disambiguation',()=>assert.equal(ask('Communist có quan hệ gì?').kind,'clarify'));
test('incoming declarations do not reverse an outgoing edge',()=>assert.equal(ask('Ai tuyên chiến với Hitler năm 1941?').kind,'not_found'));
test('a new entity named in the question overrides the current profile',()=>{const a=ask('PageRank của Churchill là bao nhiêu?');assert.match(a.text,/Winston Churchill/)});
test('malicious text is treated as an unsupported question',()=>assert.equal(ask('<img src=x onerror=alert(1)>').kind,'unsupported'));
test('Vietnamese country alias is resolved without confusing English my',()=>{
 const a=ask('Hitler và Mỹ có mối liên hệ gì?');assert.equal(a.kind,'path');assert.equal(a.context[0].target,'United States');
 assert.equal(qa.mentions('my question').ids.length,0);
});
test('person ranking does not return parties as people',()=>{const a=ask('Nhân vật nào có PageRank cao nhất?');assert.match(a.title,/chính khách/);assert.doesNotMatch(a.text,/Democratic|Republican/)});
