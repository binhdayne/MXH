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
test('empty question requests names instead of using an implicit target',()=>{
 const a=ask('');assert.equal(a.kind,'clarify');assert.match(a.text,/Nhập tên hai thực thể/);assert.equal(a.context.length,0);
});
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
 assert.equal(ask('Ai có PageRank cao nhất?').kind,'ranking');assert.match(ask('Mạng có bao nhiêu nút và cạnh?').text,/6643/);
});
test('timeline includes events and tenures active in the requested year',()=>{const a=ask('Dòng thời gian của Hitler năm 1941');assert.equal(a.kind,'timeline');assert.ok(a.context.every(e=>e.year===1941||e.start_year<=1941&&1941<=e.end_year));assert.ok(a.context.some(e=>e.relation==='LED_GOVERNMENT'))});
test('year-limited path does not mix 1941 and 1943',()=>assert.equal(ask('Hitler và Stalin có liên hệ gì năm 1941?').kind,'not_found'));
test('missing positive evidence cannot establish personal alliance',()=>{const a=ask('Hitler và Stalin có phải đồng minh không?');assert.equal(a.kind,'not_found');assert.match(a.text,/không khẳng định/)});
test('same endpoints and disconnected endpoints are handled',()=>{
 assert.equal(qa.answer('Quan hệ với Hitler',hitler).kind,'same_entity');
 const isolated=data.nodes.find(n=>n.degree===0);assert.equal(qa.answer('Hitler và '+isolated.name+' có mối liên hệ gì?',hitler).kind,'not_found');
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

test('reported Hiter Germany question resolves both names independently of selected profile',()=>{
 const q='Quan hệ của Hiter là Germany';
 assert.deepEqual(qa.mentions(q).ids,[hitler,id('Nazi Germany')]);
 const a=qa.answer(q,stalin,id('United States'));
 assert.equal(a.kind,'path');assert.equal(a.start,hitler);assert.equal(a.target,id('Nazi Germany'));
 assert.equal(a.direct,true);assert.match(a.title,/trực tiếp/);
 assert.equal(a.context.length,1);assert.equal(a.context[0].relation,'LED_GOVERNMENT');assert.match(a.text,/lãnh đạo chính phủ/);assert.match(a.text,/1933–1945/);
 assert.ok(a.context[0].url);assert.equal(a.context[0].start_date,'1933-01-30');assert.equal(a.context[0].end_date,'1945-04-30');
});

test('short Stalin Soviet phrasing returns original direct relation and year',()=>{
 for(const q of ['Stalin với Soviet','Quan hệ của Stalin với Soviet Union','Stalin và Liên Xô','Stalin USSR']){
  const a=ask(q);assert.equal(a.kind,'path',q);assert.equal(a.direct,true,q);
  assert.equal(a.start,stalin);assert.equal(a.target,id('Soviet Union'));
  assert.equal(a.context.length,1);assert.equal(a.context[0].relation,'REPRESENTED');
  assert.equal(a.context[0].source,'Joseph Stalin');assert.equal(a.context[0].target,'Soviet Union');assert.equal(a.context[0].year,1943);
 }
});

test('Germany Soviet pair preserves both the pact and invasion rather than one arbitrary edge',()=>{
 const a=ask('Germany với Soviet');assert.equal(a.direct,true);
 assert.deepEqual(new Set(a.context.map(e=>e.relation)),new Set(['INVADED','NON_AGGRESSION_PACT']));
 assert.deepEqual(new Set(a.context.map(e=>e.year)),new Set([1939,1941]));
 const b=ask('Germany với Soviet năm 1941');assert.equal(b.context.length,1);assert.equal(b.context[0].relation,'INVADED');
});

test('unknown second endpoint in short with-phrasing never falls back to current profile',()=>{
 assert.equal(ask('Stalin với Harry Potter').kind,'clarify');
 assert.equal(ask('Quan hệ của Harry Potter với Germany').kind,'clarify');
});

test('short Soviet alias does not swallow the longer event name',()=>{
 assert.deepEqual(qa.mentions('Soviet–Japanese Neutrality Pact').ids,[id('Soviet–Japanese Neutrality Pact')]);
 assert.equal(qa.mentions('Germanyish Sovietish Hiteration').ids.length,0);
});

test('contextual relation request can still use current profile as the subject',()=>{
 const a=ask('Quan hệ với Stalin');assert.equal(a.kind,'path');assert.equal(a.start,hitler);assert.equal(a.target,stalin);
});

test('leadership questions and year filters retrieve the sourced leadership edge',()=>{
 const a=ask('Hitler lãnh đạo nước nào?');assert.equal(a.kind,'relations');assert.equal(a.context.length,1);assert.equal(a.context[0].relation,'LED_GOVERNMENT');
 for(const year of [1939,1941,1945]){const b=ask('Hitler với nước Đức có mối quan hệ gì năm '+year);assert.equal(b.direct,true);assert.equal(b.context[0].relation,'LED_GOVERNMENT')}
 const incoming=ask('Ai lãnh đạo Germany năm 1941?');assert.equal(incoming.context[0].source,'Adolf Hitler');assert.equal(incoming.context[0].target,'Nazi Germany');
});
