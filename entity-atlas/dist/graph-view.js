(function(root){
'use strict';
const colors={WartimePolitician:'#467f7a',WartimeParty:'#5377b4',WartimeGovernment:'#b16b50',WartimeEvent:'#bc9a43'};
class Boxes{
 constructor(){this.cells=new Map()}
 keys(b){const a=[];for(let x=Math.floor((b.x-3)/48);x<=Math.floor((b.x+b.w+3)/48);x++)for(let y=Math.floor((b.y-3)/48);y<=Math.floor((b.y+b.h+3)/48);y++)a.push(x+','+y);return a}
 add(b){for(const k of this.keys(b)){if(!this.cells.has(k))this.cells.set(k,[]);this.cells.get(k).push(b)}}
 collides(b){return this.keys(b).some(k=>(this.cells.get(k)||[]).some(a=>GraphModel.intersects(a,b,3)))}
}
class GraphView{
 constructor(host,options={}){
  this.host=host;this.options=options;this.camera={x:0,y:0,k:1};this.nodes=[];this.edges=[];this.colorMode='kind';this.labels=true;this.pointers=new Map();
  host.classList.add('graph-shell');host.innerHTML='<div class="graph-tools"><button type="button" data-tool="in" aria-label="Phóng to">+</button><button type="button" data-tool="out" aria-label="Thu nhỏ">−</button><button type="button" data-tool="fit">Vừa khung</button><button type="button" data-tool="reset">Bố trí lại</button><button type="button" data-tool="labels" aria-pressed="true">Nhãn</button><button type="button" data-tool="expand">Mở rộng</button></div><canvas tabindex="0" role="img"></canvas><div class="graph-tooltip" role="tooltip" hidden></div><div class="graph-state" aria-live="polite"></div>';
  this.canvas=host.querySelector('canvas');this.ctx=this.canvas.getContext('2d');this.tip=host.querySelector('.graph-tooltip');this.state=host.querySelector('.graph-state');
  host.querySelectorAll('[data-tool]').forEach(b=>b.onclick=()=>{const t=b.dataset.tool;if(t==='in')this.zoom(1.35);if(t==='out')this.zoom(1/1.35);if(t==='fit')this.fit();if(t==='reset')this.reset();if(t==='labels'){this.labels=!this.labels;b.setAttribute('aria-pressed',this.labels);this.schedule()}if(t==='expand')this.expand()});
  this.resizeObserver=new ResizeObserver(()=>this.resize());this.resizeObserver.observe(host);
  this.canvas.addEventListener('wheel',e=>{e.preventDefault();const p=this.local(e);this.zoom(Math.exp(-e.deltaY*.0015),p.x,p.y)},{passive:false});
  this.canvas.addEventListener('pointerdown',e=>this.down(e));this.canvas.addEventListener('pointermove',e=>this.move(e));
  this.canvas.addEventListener('pointerup',e=>this.up(e));this.canvas.addEventListener('pointercancel',e=>this.up(e,true));
  this.canvas.addEventListener('pointerleave',()=>{if(!this.drag){this.clearHover();this.schedule()}});
  this.canvas.addEventListener('dblclick',e=>{const n=this.hit(this.local(e));if(n)this.options.onOpen?.(n.id)});
  this.canvas.addEventListener('keydown',e=>{if(['+','=','-','0','ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Escape','Enter'].includes(e.key))e.preventDefault();if(e.key==='+'||e.key==='=')this.zoom(1.3);if(e.key==='-')this.zoom(1/1.3);if(e.key==='0')this.fit();if(e.key==='ArrowLeft')this.camera.x+=45;if(e.key==='ArrowRight')this.camera.x-=45;if(e.key==='ArrowUp')this.camera.y+=45;if(e.key==='ArrowDown')this.camera.y-=45;if(e.key==='Enter'&&this.selectedId)this.options.onOpen?.(this.selectedId);if(e.key==='Escape'){if(this.expanded)this.expand(false);else this.highlight(null)}this.schedule()});
  this.escape=e=>{if(e.key==='Escape'&&this.expanded)this.expand(false)};document.addEventListener('keydown',this.escape);this.resize();
 }
 resize(){
  const rect=this.host.getBoundingClientRect();if(rect.width<10||rect.height<10)return;
  this.width=rect.width;this.height=rect.height;const ratio=Math.min(devicePixelRatio||1,2);
  this.canvas.width=Math.round(rect.width*ratio);this.canvas.height=Math.round(rect.height*ratio);this.ratio=ratio;
  if(this.pendingFit){this.pendingFit=false;this.fit()}else this.schedule();
 }
 setData(nodes,edges,{positions=null,focus=null,groups=[]}={}){
  this.simulation?.stop();this.layoutToken=(this.layoutToken||0)+1;const token=this.layoutToken;this.focusId=focus;this.selectedId=null;this.clearHover();this.groups=groups;
  if(positions){this.nodes=nodes.map(n=>({...n,...positions.get(n.id),r:GraphModel.radius(n,true)}));const byId=new Map(this.nodes.map(n=>[n.id,n]));this.edges=edges.map(e=>({...e,source:byId.get(e.source),target:byId.get(e.target)})).filter(e=>e.source&&e.target);this.done=true;this.reindex();this.fit()}
  else{
   const layout=GraphModel.prepare(nodes,edges,{focus});this.nodes=layout.nodes;this.edges=layout.edges;this.simulation=layout.simulation;this.done=false;let ticks=0;
   const advance=()=>{if(token!==this.layoutToken)return;this.simulation.tick(6);ticks+=6;this.reindex();this.fit(false);if(ticks<180){this.layoutFrame=requestAnimationFrame(advance)}else{this.done=true;this.simulation.stop();this.reindex();this.fit();this.describe()}};
   this.layoutFrame=requestAnimationFrame(advance);
  }
  this.original=this.nodes.map(n=>({id:n.id,x:n.x,y:n.y}));this.describe();this.schedule();
 }
 describe(){this.canvas.setAttribute('aria-label',`Đồ thị ${this.nodes.length} nút, ${this.edges.length} quan hệ. Dùng phím cộng trừ để phóng, các phím mũi tên để kéo và phím 0 để vừa khung.`);this.canvas.dataset.nodeCount=this.nodes.length;this.canvas.dataset.edgeCount=this.edges.length;this.state.textContent=this.nodes.length?(this.done?'Kéo nền để di chuyển · Kéo nút để tách · Cuộn để phóng · Rê nút/cạnh để xem thông tin':'Đang giãn khoảng cách giữa các nút…'):'Không có thực thể hoặc quan hệ phù hợp với bộ lọc.'}
 reindex(){this.byId=new Map(this.nodes.map(n=>[n.id,n]));this.tree=d3.quadtree(this.nodes,n=>n.x,n=>n.y);if(this.selectedId)this.highlight(this.selectedId,false)}
 bounds(){return this.nodes.reduce((b,n)=>({x0:Math.min(b.x0,n.x-n.r),y0:Math.min(b.y0,n.y-n.r),x1:Math.max(b.x1,n.x+n.r),y1:Math.max(b.y1,n.y+n.r)}),{x0:Infinity,y0:Infinity,x1:-Infinity,y1:-Infinity})}
 fit(paint=true){
  this.clearHover();
  if(!this.width||!this.height){this.pendingFit=true;return}if(!this.nodes.length){this.camera={x:0,y:0,k:1};this.schedule();return}
  const b=this.bounds(),k=Math.max(.025,Math.min(2,(this.width-70)/Math.max(120,b.x1-b.x0),(this.height-120)/Math.max(100,b.y1-b.y0)));
  this.camera={k,x:this.width/2-(b.x0+b.x1)/2*k,y:(this.height+20)/2-(b.y0+b.y1)/2*k};this.schedule();
 }
 zoom(factor,x=this.width/2,y=this.height/2){this.clearHover();const c=this.camera,k=Math.max(.025,Math.min(8,c.k*factor)),ratio=k/c.k;c.x=x-(x-c.x)*ratio;c.y=y-(y-c.y)*ratio;c.k=k;this.schedule()}
 focus(id){this.clearHover();const n=this.byId.get(id);if(!n)return false;this.camera={k:1.8,x:this.width/2-n.x*1.8,y:this.height/2-n.y*1.8};this.highlight(id);return true}
 highlight(id,paint=true){this.selectedId=id;this.neighbors=new Set(id?[id]:[]);if(id)for(const e of this.edges){if(e.source.id===id)this.neighbors.add(e.target.id);if(e.target.id===id)this.neighbors.add(e.source.id)}if(paint)this.schedule()}
 reset(){if(this.options.overview){const originals=new Map(this.original.map(n=>[n.id,n]));this.nodes.forEach(n=>Object.assign(n,originals.get(n.id)));this.reindex();this.highlight(null);this.fit()}else this.setData(this.nodes,this.edges.map(e=>({...e,source:e.source.id,target:e.target.id})),{focus:this.focusId})}
 expand(force){const next=force??!this.expanded;if(next&&GraphView.expanded&&GraphView.expanded!==this)GraphView.expanded.expand(false);this.expanded=next;this.host.classList.toggle('graph-expanded',next);if(next){this.oldOverflow=document.body.style.overflow;document.body.style.overflow='hidden';GraphView.expanded=this}else{document.body.style.overflow=this.oldOverflow||'';GraphView.expanded=null}this.host.querySelector('[data-tool="expand"]').textContent=next?'Thu gọn':'Mở rộng';this.pendingFit=true;this.resize()}
 local(e){const r=this.canvas.getBoundingClientRect();return {x:e.clientX-r.left,y:e.clientY-r.top}}
 world(p){return {x:(p.x-this.camera.x)/this.camera.k,y:(p.y-this.camera.y)/this.camera.k}}
 screen(n){return {x:n.x*this.camera.k+this.camera.x,y:n.y*this.camera.k+this.camera.y}}
 hit(p){if(!this.tree)return null;const w=this.world(p),n=this.tree.find(w.x,w.y,Math.max(24,22/this.camera.k));return n&&Math.hypot(w.x-n.x,w.y-n.y)<=n.r+5/this.camera.k?n:null}
 down(e){
  if(!this.done){this.layoutToken++;this.simulation?.stop();this.done=true;this.reindex();this.describe()}
  const p=this.local(e);this.pointers.set(e.pointerId,p);this.canvas.setPointerCapture(e.pointerId);this.clearHover();
  if(this.pointers.size===2){const [a,b]=[...this.pointers.values()];const mid={x:(a.x+b.x)/2,y:(a.y+b.y)/2};this.pinch={distance:Math.hypot(a.x-b.x,a.y-b.y),k:this.camera.k,world:this.world(mid)};this.drag=null;return}
  const n=this.hit(p);this.drag={id:e.pointerId,node:n,start:p,base:{...this.camera},moved:false};this.canvas.style.cursor=n?'grabbing':'grabbing';
 }
 move(e){
  const p=this.local(e);if(this.pointers.has(e.pointerId))this.pointers.set(e.pointerId,p);
  if(this.pinch&&this.pointers.size===2){const [a,b]=[...this.pointers.values()],mid={x:(a.x+b.x)/2,y:(a.y+b.y)/2};const k=Math.max(.025,Math.min(8,this.pinch.k*Math.hypot(a.x-b.x,a.y-b.y)/Math.max(1,this.pinch.distance)));this.camera={k,x:mid.x-this.pinch.world.x*k,y:mid.y-this.pinch.world.y*k};this.schedule();return}
  if(this.drag?.id===e.pointerId){const d=this.drag,dx=p.x-d.start.x,dy=p.y-d.start.y;if(Math.hypot(dx,dy)>4)d.moved=true;if(d.moved){if(d.node){const w=this.world(p);d.node.x=w.x;d.node.y=w.y;d.node.fx=w.x;d.node.fy=w.y}else{this.camera.x=d.base.x+dx;this.camera.y=d.base.y+dy}this.schedule()}return}
  const n=this.hit(p),id=n?.id||null,edges=n?[]:this.findEdges(p),previous=this.hoverEdges||[];
  if(id!==this.hoverId||edges.length!==previous.length||edges.some((edge,i)=>edge!==previous[i])){this.hoverId=id;this.hoverEdges=edges;this.schedule()}
  this.canvas.style.cursor=n||edges.length?'pointer':'grab';
  if(n)this.showTip(n.name+' · '+(n.country||n.kind.replace('Wartime',''))+' · Bậc '+n.degree,p);
  else if(edges.length)this.showTip(edges.slice(0,3).map(edge=>this.edgeText(edge)).join('\n\n')+(edges.length>3?'\n… Còn '+(edges.length-3)+' quan hệ khác giữa hai nút.':''),p);
  else this.tip.hidden=true;
 }
 up(e,cancelled=false){
  this.pointers.delete(e.pointerId);if(this.pinch){this.pinch=null;this.drag=null;this.reindex();return}
  const d=this.drag;if(!d||d.id!==e.pointerId)return;this.drag=null;this.canvas.style.cursor='grab';
  if(!cancelled&&!d.moved){if(d.node){this.highlight(d.node.id);this.options.onSelect?.(d.node.id)}else{this.highlight(null);this.pickEdge(this.local(e))}}
  this.reindex();if(!cancelled)this.move(e);this.schedule();
 }
 clearHover(){this.hoverId=null;this.hoverEdges=[];this.tip.hidden=true}
 findEdges(p){return GraphModel.edgesAtPoint(this.edges,p,n=>this.screen(n))}
 edgeText(e){const type=this.options.relations?.[e.relation]||e.relation;return type+' ('+e.relation+')\n'+e.source.name+(e.symmetric?' ↔ ':' → ')+e.target.name+'\n'+(e.start_year!=null?'Giai đoạn '+e.start_year+'–'+e.end_year+' · ':e.year?'Năm '+e.year+' · ':'')+(e.sign===1?'Dấu +1':e.sign===-1?'Dấu −1':'Bối cảnh')}
 showTip(text,p){this.tip.textContent=text;this.tip.hidden=false;this.tip.style.left=Math.max(8,Math.min(this.width-this.tip.offsetWidth-8,p.x+14))+'px';this.tip.style.top=Math.max(48,Math.min(this.height-this.tip.offsetHeight-8,p.y+16))+'px'}
 pickEdge(p){const edge=this.findEdges(p)[0];if(edge)this.options.onEdge?.(edge)}
 schedule(){if(this.frame)return;this.frame=requestAnimationFrame(()=>{this.frame=null;this.paint()})}
 color(n){return this.colorMode==='community'?`hsl(${(n.community*137.508)%360} 48% 46%)`:(colors[n.kind]||'#748d97')}
 paint(){
  const c=this.ctx,w=this.width,h=this.height;if(!w||!h)return;c.setTransform(this.ratio,0,0,this.ratio,0,0);c.clearRect(0,0,w,h);c.fillStyle='#fbfdfc';c.fillRect(0,0,w,h);
  const k=this.camera.k,hoveredEdges=this.hoverEdges||[],active=this.hoverId||(hoveredEdges.length?null:this.selectedId);let neighborhood=hoveredEdges.length?new Set(hoveredEdges.flatMap(e=>[e.source.id,e.target.id])):null;if(active){neighborhood=new Set([active]);for(const e of this.edges){if(e.source.id===active)neighborhood.add(e.target.id);if(e.target.id===active)neighborhood.add(e.source.id)}}
  if(this.groups?.length&&this.options.overview){for(const g of this.groups){const p=this.screen(g),r=g.r*k;if(r<35)continue;c.beginPath();c.arc(p.x,p.y,r,0,Math.PI*2);c.fillStyle='#1e5c4706';c.fill()}}
  const visible=new Map();for(const n of this.nodes){const p=this.screen(n);if(p.x>-40&&p.x<w+40&&p.y>30&&p.y<h+40)visible.set(n.id,{...p,r:Math.max(1.2,n.r*k),node:n})}
  for(const e of this.edges){const a=this.screen(e.source),b=this.screen(e.target);if(Math.max(a.x,b.x)<0||Math.min(a.x,b.x)>w||Math.max(a.y,b.y)<40||Math.min(a.y,b.y)>h)continue;const emphasized=hoveredEdges.length?hoveredEdges.includes(e):active&&(e.source.id===active||e.target.id===active);c.globalAlpha=(active||hoveredEdges.length)?(emphasized?.85:.025):(this.nodes.length>300?.13:.3);c.strokeStyle=e.sign===1?'#398566':e.sign===-1?'#b66659':'#899ca7';c.lineWidth=emphasized?1.8:.8;c.beginPath();c.moveTo(a.x,a.y);c.lineTo(b.x,b.y);c.stroke();if(!e.symmetric&&k>.8&&(emphasized||this.edges.length<500)){const angle=Math.atan2(b.y-a.y,b.x-a.x),r=e.target.r*k+2,x=b.x-Math.cos(angle)*r,y=b.y-Math.sin(angle)*r;c.fillStyle=c.strokeStyle;c.beginPath();c.moveTo(x,y);c.lineTo(x-Math.cos(angle-.5)*7,y-Math.sin(angle-.5)*7);c.lineTo(x-Math.cos(angle+.5)*7,y-Math.sin(angle+.5)*7);c.closePath();c.fill()}}
  c.globalAlpha=1;const occupied=new Boxes();
  for(const p of visible.values()){
   const n=p.node,r=p.r+(n.id===this.focusId?3:0);c.globalAlpha=neighborhood&&!neighborhood.has(n.id)?.16:1;c.fillStyle=this.color(n);c.strokeStyle=n.id===active?'#142c2b':'#ffffff';c.lineWidth=n.id===active?2:1;c.beginPath();
   if(n.kind==='WartimeParty')c.rect(p.x-r,p.y-r,r*2,r*2);else if(n.kind==='WartimeGovernment'){c.moveTo(p.x,p.y-r*1.2);c.lineTo(p.x+r,p.y);c.lineTo(p.x,p.y+r*1.2);c.lineTo(p.x-r,p.y);c.closePath()}else if(n.kind==='WartimeEvent'){c.moveTo(p.x,p.y-r*1.2);c.lineTo(p.x+r,p.y+r);c.lineTo(p.x-r,p.y+r);c.closePath()}else c.arc(p.x,p.y,r,0,Math.PI*2);
   c.fill();if(r>2)c.stroke();occupied.add({x:p.x-r-1,y:p.y-r-1,w:r*2+2,h:r*2+2});
  }
  c.globalAlpha=1;
  if(this.labels){
   const candidates=[...visible.values()].sort((a,b)=>{const score=p=>p.node.id===active?1e9:p.node.id===this.focusId?1e8:neighborhood?.has(p.node.id)?1e7+(p.node.degree||0):p.node.pagerank||0;return score(b)-score(a)});
   let count=0;const cap=this.nodes.length>300?(k>.8?110:25):90;c.font='13px Inter,Arial';
   for(const p of candidates){if(count>=cap)break;if(neighborhood&&!neighborhood.has(p.node.id))continue;const text=p.node.name.length>30?p.node.name.slice(0,28)+'…':p.node.name,width=c.measureText(text).width+10,box=GraphModel.placeLabel(p.x,p.y,p.r,width,20,occupied,w,h-22);if(!box)continue;occupied.add(box);c.fillStyle='#ffffffed';c.fillRect(box.x,box.y,box.w,box.h);c.fillStyle='#203832';c.fillText(text,box.x+5,box.y+14);count++}
  }
  c.globalAlpha=1;c.fillStyle='#647b72';c.font='12px Inter,Arial';c.fillText(Math.round(k*100)+'%',12,h-12);
 }
}
root.GraphView=GraphView;
})(globalThis);
