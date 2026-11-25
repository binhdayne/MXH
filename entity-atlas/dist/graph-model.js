(function(root){
'use strict';
const d3=typeof module!=='undefined'&&module.exports?require('./vendor/d3.v7.9.0.min.js'):root.d3;
function matchesYear(e,year){const y=Number(year);return e.start_year!=null&&e.end_year!=null?Number(e.start_year)<=y&&y<=Number(e.end_year):Number(e.year)===y}
function filterGraph(data,f={}){
 let nodes=data.nodes.filter(n=>(!f.kind||n.kind===f.kind)&&(f.community===''||f.community==null||n.community===Number(f.community)));
 const ids=new Set(nodes.map(n=>n.id));
 const edges=data.edges.filter(e=>ids.has(e.source)&&ids.has(e.target)&&(!f.relation||e.relation===f.relation)&&(!f.sign||(f.sign==='0'?e.sign==null:e.sign===Number(f.sign)))&&(!f.year||matchesYear(e,f.year)));
 if(f.relation||f.sign||f.year){const incident=new Set(edges.flatMap(e=>[e.source,e.target]));nodes=nodes.filter(n=>incident.has(n.id))}
 return {nodes,edges};
}
function radius(n,overview=false){return overview?Math.min(13,3+Math.log1p(n.degree||0)*1.4):Math.min(18,8+Math.log1p(n.degree||0))}
function prepare(nodes,edges,{overview=false,focus=null}={}){
 const items=nodes.slice().sort((a,b)=>a.id.localeCompare(b.id)).map(n=>{const copy={...n,r:radius(n,overview)};delete copy.fx;delete copy.fy;copy.vx=0;copy.vy=0;return copy}),byId=new Map(items.map(n=>[n.id,n]));
 const links=edges.filter(e=>e.source!==e.target&&byId.has(e.source)&&byId.has(e.target)).map(e=>({...e}));
 let groups=[];
 if(overview){
  const grouped=d3.group(items,n=>n.community);groups=[...grouped].map(([id,v])=>({id,r:Math.sqrt(v.length)*14+45,size:v.length,name:v.slice().sort((a,b)=>b.pagerank-a.pagerank)[0].name})).sort((a,b)=>b.size-a.size||a.id-b.id);
  d3.packSiblings(groups);const groupMap=new Map(groups.map(g=>[g.id,g]));
  for(const [,list] of grouped)list.forEach((n,i)=>{const g=groupMap.get(n.community),a=i*2.399963229728653,r=Math.sqrt(i)*14;n.ax=g.x;n.ay=g.y;n.x=g.x+Math.cos(a)*r;n.y=g.y+Math.sin(a)*r});
 }else items.forEach((n,i)=>{const a=i*2.399963229728653,r=70+Math.sqrt(i)*34;n.x=Math.cos(a)*r;n.y=Math.sin(a)*r;if(n.id===focus){n.x=0;n.y=0;n.fx=0;n.fy=0}});
 const sim=d3.forceSimulation(items).randomSource(d3.randomLcg(1945)).stop()
  .force('charge',d3.forceManyBody().strength(overview?-45:-260).distanceMax(overview?500:1200))
  .force('link',d3.forceLink(links).id(n=>n.id).distance(overview?36:110).strength(overview?.035:.16))
  .force('collide',d3.forceCollide(n=>n.r+(overview?5:14)).strength(1).iterations(2))
  .force('x',d3.forceX(n=>overview?n.ax:0).strength(overview?.13:.012))
  .force('y',d3.forceY(n=>overview?n.ay:0).strength(overview?.13:.012));
 return {nodes:items,edges:links,simulation:sim,groups};
}
function intersects(a,b,gap=0){return a.x<b.x+b.w+gap&&a.x+a.w+gap>b.x&&a.y<b.y+b.h+gap&&a.y+a.h+gap>b.y}
function placeLabel(x,y,r,w,h,occupied,width,height){
 const positions=[[x+r+5,y-h/2],[x-r-w-5,y-h/2],[x-w/2,y-r-h-5],[x-w/2,y+r+5],[x+r+7,y-r-h-4],[x-r-w-7,y+r+4]];
 for(const [a,b] of positions){const box={x:a,y:b,w,h};if(a<4||b<4||a+w>width-4||b+h>height-4)continue;if(!(occupied.collides?occupied.collides(box):occupied.some(o=>intersects(box,o,3))))return box}
 return null;
}
// Distances are measured in screen pixels so hover stays usable at every zoom.
function edgesAtPoint(edges,p,project,tolerance=6){
 let nearest=null,best=tolerance;
 for(const e of edges){
  const a=project(e.source),b=project(e.target),dx=b.x-a.x,dy=b.y-a.y,den=dx*dx+dy*dy;if(!den)continue;
  if(p.x<Math.min(a.x,b.x)-tolerance||p.x>Math.max(a.x,b.x)+tolerance||p.y<Math.min(a.y,b.y)-tolerance||p.y>Math.max(a.y,b.y)+tolerance)continue;
  const t=Math.max(0,Math.min(1,((p.x-a.x)*dx+(p.y-a.y)*dy)/den));
  const distance=Math.hypot(p.x-a.x-t*dx,p.y-a.y-t*dy);
  if(distance<best){nearest=e;best=distance}
 }
 if(!nearest)return [];
 return edges.filter(e=>(e.source.id===nearest.source.id&&e.target.id===nearest.target.id)||(e.source.id===nearest.target.id&&e.target.id===nearest.source.id));
}
const api={filterGraph,radius,prepare,intersects,placeLabel,edgesAtPoint,matchesYear};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.GraphModel=api;
})(typeof globalThis!=='undefined'?globalThis:this);
