const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const crypto=require('node:crypto');
const model=require('./dist/graph-model.js');
const bytes=fs.readFileSync(__dirname+'/dist/graph.json');
const data=JSON.parse(bytes);
const cache=require('./dist/layout.json');

test('overview preserves every node and edge without filters',()=>{
 const result=model.filterGraph(data);
 assert.equal(result.nodes.length,2750);
 assert.equal(result.edges.length,6643);
 assert.deepEqual(result.nodes,data.nodes);
 assert.deepEqual(result.edges,data.edges);
});

test('filters preserve endpoints and apply relation, sign and year together',()=>{
 for(const sign of ['1','-1','0']){
  const result=model.filterGraph(data,{sign});
  const ids=new Set(result.nodes.map(n=>n.id));
  const expected=data.edges.filter(e=>sign==='0'?e.sign==null:e.sign===Number(sign));
  assert.deepEqual(result.edges,expected);
  assert.ok(result.edges.every(e=>ids.has(e.source)&&ids.has(e.target)));
 }
 const edge=data.edges.find(e=>e.year&&e.sign===1);
 const filtered=model.filterGraph(data,{relation:edge.relation,year:String(edge.year),sign:'1'});
 assert.ok(filtered.edges.length);
 assert.ok(filtered.edges.every(e=>e.relation===edge.relation&&e.year===edge.year&&e.sign===1));
 assert.deepEqual(model.filterGraph(data,{relation:'missing'}),{nodes:[],edges:[]});
});

test('entity and community filters produce an induced graph',()=>{
 const n=data.nodes[0];
 const result=model.filterGraph(data,{kind:n.kind,community:String(n.community)});
 const ids=new Set(result.nodes.map(x=>x.id));
 assert.ok(ids.has(n.id));
 assert.ok(result.nodes.every(x=>x.kind===n.kind&&x.community===n.community));
 assert.deepEqual(result.edges,data.edges.filter(e=>ids.has(e.source)&&ids.has(e.target)));
});

test('cached layout matches the exact graph snapshot and covers each node once',()=>{
 assert.equal(cache.graph_sha256,crypto.createHash('sha256').update(bytes).digest('hex'));
 assert.equal(cache.nodes.length,data.nodes.length);
 assert.equal(new Set(cache.nodes.map(n=>n.id)).size,data.nodes.length);
 assert.deepEqual(cache.nodes.map(n=>n.id).sort(),data.nodes.map(n=>n.id).sort());
 assert.ok(cache.nodes.every(n=>Number.isFinite(n.x)&&Number.isFinite(n.y)));
 assert.equal(cache.groups.length,data.stats.communities);
});

test('re-layout releases dragged nodes, pins only focus and does not mutate source',()=>{
 const nodes=Array.from({length:60},(_,i)=>({id:'n'+i,name:'Node '+i,degree:2,pagerank:1,community:0,fx:100,fy:100}));
 const edges=nodes.slice(1).map(n=>({source:'n0',target:n.id}));
 const before=JSON.stringify({nodes,edges});
 const layout=model.prepare(nodes,edges,{focus:'n0'});
 assert.equal(layout.nodes.find(n=>n.id==='n0').fx,0);
 assert.ok(layout.nodes.filter(n=>n.id!=='n0').every(n=>n.fx==null&&n.fy==null));
 layout.simulation.tick(180).stop();
 assert.equal(JSON.stringify({nodes,edges}),before);
 for(let i=0;i<layout.nodes.length;i++)for(let j=0;j<i;j++){
  const a=layout.nodes[i],b=layout.nodes[j];
  assert.ok(Math.hypot(a.x-b.x,a.y-b.y)>=a.r+b.r,'node circles overlap');
 }
});

test('labels stay in viewport and never overlap previously placed labels',()=>{
 const occupied=[];
 for(let i=0;i<100;i++){
  const box=model.placeLabel(90+(i%10)*30,60+Math.floor(i/10)*25,8,100,20,occupied,500,400);
  if(!box)continue;
  assert.ok(box.x>=4&&box.y>=4&&box.x+box.w<=496&&box.y+box.h<=396);
  assert.ok(occupied.every(other=>!model.intersects(box,other,3)));
  occupied.push(box);
 }
 assert.ok(occupied.length>0&&occupied.length<100);
 assert.equal(model.placeLabel(40,40,8,100,20,[{x:0,y:0,w:500,h:400}],500,400),null);
});

test('edge hover uses screen pixels after zoom and groups parallel records in both directions',()=>{
 const a={id:'a',x:0,y:0},b={id:'b',x:100,y:0},c={id:'c',x:0,y:100};
 const edges=[{source:a,target:b,relation:'SIGNED'},{source:b,target:a,relation:'REPRESENTED'},{source:a,target:c,relation:'ATTENDED'}];
 for(const k of [.1,1,4]){
  const project=n=>({x:20+n.x*k,y:30+n.y*k});
  assert.deepEqual(model.edgesAtPoint(edges,{x:20+50*k,y:25},project),edges.slice(0,2));
  assert.deepEqual(model.edgesAtPoint(edges,{x:20+50*k,y:23},project),[]);
 }
 assert.deepEqual(model.edgesAtPoint([{source:a,target:a}],{x:0,y:0},n=>n),[]);
});

test('pointer hover displays relation details, gives nodes priority, and clears on blank space',()=>{
 globalThis.GraphModel=model;require('./dist/graph-view.js');
 const view=Object.create(globalThis.GraphView.prototype);
 const a={id:'a',name:'Adolf Hitler',x:0,y:0},b={id:'b',name:'United States',x:100,y:0};
 Object.assign(view,{camera:{x:0,y:0,k:1},width:400,height:360,pointers:new Map(),edges:[{source:a,target:b,relation:'DECLARED_WAR_ON',year:1941,sign:-1}],canvas:{style:{},getBoundingClientRect:()=>({left:0,top:0})},tip:{hidden:true,style:{},offsetWidth:200,offsetHeight:70},options:{relations:{DECLARED_WAR_ON:'tuyên chiến'}},schedule:()=>{},hit:()=>null});
 view.move({clientX:50,clientY:3,pointerId:1});
 assert.equal(view.tip.hidden,false);assert.match(view.tip.textContent,/tuyên chiến/);assert.match(view.tip.textContent,/Adolf Hitler → United States/);assert.match(view.tip.textContent,/1941/);assert.match(view.tip.textContent,/−1/);
 assert.equal(view.hoverEdges.length,1);
 view.hit=()=>({...a,kind:'WartimePolitician',degree:3});view.move({clientX:50,clientY:3,pointerId:1});
 assert.equal(view.hoverEdges.length,0);assert.match(view.tip.textContent,/Bậc 3/);
 view.hit=()=>null;view.move({clientX:250,clientY:100,pointerId:1});
 assert.equal(view.tip.hidden,true);assert.equal(view.hoverEdges.length,0);
});

test('leadership interval is included in every applicable wartime year',()=>{
 const leadership=data.edges.find(e=>e.relation==='LED_GOVERNMENT');assert.ok(leadership);
 assert.equal(leadership.start_year,1933);assert.equal(leadership.end_year,1945);
 for(let year=1939;year<=1945;year++)assert.ok(model.filterGraph(data,{year:String(year)}).edges.some(e=>e.id===leadership.id));
 assert.equal(model.matchesYear(leadership,1946),false);
});
