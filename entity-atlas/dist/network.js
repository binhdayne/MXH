(function(root){
'use strict';
const $=id=>document.getElementById(id),safe=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const kindName={WartimePolitician:'Chính khách / ứng viên',WartimeParty:'Đảng phái',WartimeGovernment:'Chính phủ',WartimeEvent:'Sự kiện'};
const norm=s=>String(s).normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').toLowerCase();
class NetworkOverview{
 constructor(data,options={}){this.data=data;this.options=options;this.nodes=new Map(data.nodes.map(n=>[n.id,n]));this.ready=this.load()}
 async load(){
  const r=await fetch('layout.json?v=lead1',{cache:'no-store'});if(!r.ok)throw Error('Không đọc được bố cục toàn mạng. Vui lòng tải lại trang.');const layout=await r.json();
  this.positions=new Map(layout.nodes.map(n=>[n.id,n]));if(this.data.nodes.some(n=>!this.positions.has(n.id)))throw Error('Bố cục chưa khớp snapshot dữ liệu.');this.groups=layout.groups;
  $('overview-community').innerHTML='<option value="">Tất cả cộng đồng</option>'+Object.entries(this.data.stats.community_sizes).map(([id,size])=>'<option value="'+id+'">Cộng đồng '+(+id+1)+' · '+size+' nút</option>').join('');
  $('overview-relation').innerHTML='<option value="">Tất cả quan hệ</option>'+[...new Set(this.data.edges.map(e=>e.relation))].sort().map(t=>'<option value="'+t+'">'+safe(this.options.relations[t]||t)+'</option>').join('');
  this.view=new GraphView($('overview-graph'),{overview:true,relations:this.options.relations,onSelect:id=>this.showNode(id),onOpen:id=>this.options.openProfile(id),onEdge:e=>this.showEdge(e)});
  for(const id of ['overview-kind','overview-community','overview-relation','overview-sign','overview-year'])$(id).onchange=()=>this.apply();
  $('overview-color').onchange=()=>{this.view.colorMode=$('overview-color').value;this.view.schedule()};
  $('overview-reset').onclick=()=>this.reset();$('overview-search').disabled=false;$('overview-search').oninput=()=>this.search();
  $('overview-search').onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();$('overview-results').querySelector('button')?.click()}};
  this.apply();return this;
 }
 async open(){try{await this.ready;this.view.resize();this.view.fit()}catch(e){$('overview-count').textContent=e.message}}
 filters(){return {kind:$('overview-kind').value,community:$('overview-community').value,relation:$('overview-relation').value,sign:$('overview-sign').value,year:$('overview-year').value}}
 apply(){
 const filtered=GraphModel.filterGraph(this.data,this.filters());this.filtered=filtered;
  this.view.setData(filtered.nodes,filtered.edges,{positions:this.positions,groups:this.groups.filter(g=>filtered.nodes.some(n=>n.community===g.id))});
  $('overview-count').textContent=filtered.nodes.length.toLocaleString('vi-VN')+' / '+this.data.nodes.length.toLocaleString('vi-VN')+' nút · '+filtered.edges.length.toLocaleString('vi-VN')+' / '+this.data.edges.length.toLocaleString('vi-VN')+' quan hệ';
  $('overview-selection').innerHTML='<h2>Khám phá thực thể</h2><p>Bấm một nút để xem thông tin tại đây. Bấm đúp hoặc chọn “Mở hồ sơ” để phân tích chi tiết.</p><p>Rê chuột để đọc tên đầy đủ. Khi phóng to, các nhãn được hiển thị thêm ở những vị trí đủ chỗ.</p>';
 }
 reset(){for(const id of ['overview-kind','overview-community','overview-relation','overview-sign','overview-year'])$(id).value='';$('overview-search').value='';$('overview-results').innerHTML='';this.apply()}
 search(){
  const q=norm($('overview-search').value.trim());if(!q){$('overview-results').innerHTML='';return}
  let found=this.data.nodes.filter(n=>norm(n.name).includes(q));
  if(!found.length&&this.options.resolve)found=this.options.resolve($('overview-search').value).map(id=>this.nodes.get(id)).filter(Boolean);
  $('overview-results').innerHTML=found.length?found.slice(0,12).map(n=>'<button type="button" data-focus="'+safe(n.id)+'">'+safe(n.name)+'<small>'+safe(n.country||kindName[n.kind])+'</small></button>').join(''):'<div class="empty">Không tìm thấy thực thể phù hợp.</div>';
  $('overview-results').querySelectorAll('[data-focus]').forEach(b=>b.onclick=()=>{const id=b.dataset.focus;if(!this.view.byId.has(id))this.reset();$('overview-results').innerHTML='';$('overview-search').value=this.nodes.get(id).name;this.view.focus(id);this.showNode(id)});
 }
 showNode(id){
  const n=this.nodes.get(id),edges=this.filtered.edges.filter(e=>e.source===id||e.target===id),neighbors=new Set(edges.map(e=>e.source===id?e.target:e.source));
  $('overview-selection').innerHTML='<span class="eyebrow">THỰC THỂ ĐANG CHỌN</span><h2>'+safe(n.name)+'</h2><p>'+safe(kindName[n.kind])+' · '+safe(n.country||'Lớp ngoại giao')+'</p><dl class="node-facts"><dt>Bậc toàn mạng</dt><dd>'+n.degree+'</dd><dt>PageRank</dt><dd>'+n.pagerank.toFixed(6)+'</dd><dt>Cộng đồng</dt><dd>'+(n.community+1)+'</dd><dt>k-core</dt><dd>'+n.core+'</dd><dt>Cạnh trong bộ lọc</dt><dd>'+edges.length+'</dd></dl><button type="button" id="overview-open" class="primary">Mở hồ sơ</button><h3>Láng giềng trong bộ lọc</h3>'+[...neighbors].slice(0,15).map(other=>'<button class="neighbor-chip" data-neighbor="'+safe(other)+'">'+safe(this.nodes.get(other).name)+'</button>').join('')+(neighbors.size>15?'<p>Hiển thị 15 / '+neighbors.size+' láng giềng.</p>':'');
  $('overview-open').onclick=()=>this.options.openProfile(id);
  $('overview-selection').querySelectorAll('[data-neighbor]').forEach(b=>b.onclick=()=>{this.view.focus(b.dataset.neighbor);this.showNode(b.dataset.neighbor)});
 }
 showEdge(e){
  let link='';try{const u=new URL(e.wiki_url);if(['en.wikipedia.org','vi.wikipedia.org'].includes(u.hostname))link='<a href="'+safe(u.href)+'" target="_blank" rel="noreferrer">Đọc nguồn Wikipedia</a>'}catch{}
  $('overview-selection').innerHTML='<span class="eyebrow">QUAN HỆ ĐANG CHỌN</span><h2>'+safe(this.options.relations[e.relation]||e.relation)+'</h2><p><b>'+safe(e.source.name)+'</b> '+(e.symmetric?'↔':'→')+' <b>'+safe(e.target.name)+'</b></p><p>Năm '+safe(e.start_year!=null?e.start_year+'–'+e.end_year:e.year||'chưa rõ')+' · Dấu '+(e.sign===1?'+1':e.sign===-1?'−1':'bối cảnh')+'</p>'+link+(e.evidence?'<p>'+safe(e.evidence)+'</p>':'')+'<p>Chiều ở đây là chiều cạnh gốc; vị trí trên hình chỉ dùng cho trình bày.</p>';
 }
}
root.NetworkOverview=NetworkOverview;
})(globalThis);
