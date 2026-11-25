const $=id=>document.getElementById(id);
const safe=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=n=>Number(n).toLocaleString('vi-VN',{maximumFractionDigits:3});
const kind={WartimePolitician:'Chính khách / ứng viên',WartimeParty:'Đảng phái',WartimeGovernment:'Chính phủ',WartimeEvent:'Sự kiện'};
const rel={ATTENDED:'tham dự',SIGNED:'ký kết',LED_GOVERNMENT:'lãnh đạo chính phủ',LED_PARTY:'lãnh đạo đảng',ORDERED_INVASION_OF:'ra lệnh xâm lược',REPRESENTED:'đại diện',MILITARY_PACT:'hiệp ước quân sự',NON_AGGRESSION_PACT:'bất tương xâm',INVADED:'xâm lược',DECLARED_WAR_ON:'tuyên chiến',JOINT_DECLARATION:'tuyên bố chung',NOMINATES_CANDIDATE:'đề cử',ELECTORAL_RIVAL:'tranh cử cùng ghế',LEAVES_PARTY:'rời đảng',JOINS_PARTY_AFTER_SWITCH:'gia nhập đảng',DEMANDS_SURRENDER:'yêu cầu đầu hàng',DIRECTED_AID_TO:'viện trợ',CALLED_FOR_RESISTANCE_AGAINST:'kêu gọi kháng cự',EXPRESSED_SUPPORT_FOR:'bày tỏ ủng hộ'};
let data,nodes,adj,selected,lastContext=[],lastPath=[],requestToken=0,modelBusy=false,qaEngine,qaRequest=null,egoView,overview;
function edgePeriod(e){return e.start_year!=null&&e.end_year!=null?e.start_year+'–'+e.end_year:e.year||'Chưa rõ năm'}
function sourceLink(e){try{const u=new URL(e.wiki_url);if(u.hostname==='en.wikipedia.org'||u.hostname==='vi.wikipedia.org')return '<a href="'+safe(u.href)+'" target="_blank" rel="noreferrer">Wikipedia · '+safe(e.method)+'</a>'}catch{}return ''}
function metric(label,value,note=''){return '<div class="metric"><label>'+safe(label)+'</label><strong>'+safe(value)+'</strong><span>'+safe(note)+'</span></div>'}
function go(page){document.querySelectorAll('.page').forEach(p=>p.hidden=p.id!==page);document.querySelectorAll('[data-page]').forEach(b=>b.classList.toggle('active',b.dataset.page===page));if(page==='overview'&&data){if(!overview)overview=new NetworkOverview(data,{relations:rel,openProfile:id=>{go('profile');select(id);window.scrollTo({top:180,behavior:'smooth'})},resolve:q=>qaEngine.mentions(q).ids});overview.open()}}
document.querySelectorAll('[data-page]').forEach(b=>b.onclick=()=>go(b.dataset.page));
function select(id){
 selected=nodes.get(id);if(!selected)return;requestToken++;qaRequest=null;$('slm').disabled=true;
 $('results').innerHTML='';$('search').value='';$('answer').innerHTML='';$('slmanswer').textContent='';lastContext=[];lastPath=[];
 const n=selected, incident=adj.get(id)||[], degree=n.degree;
 $('entity').innerHTML='<div class="entitybar"><div class="monogram">'+safe(n.name.split(' ').map(x=>x[0]).slice(0,2).join(''))+'</div><div><h2>'+safe(n.name)+'</h2><small>'+safe(kind[n.kind])+' · '+safe(n.country||'Lớp ngoại giao')+'</small></div><span class="tag">Cộng đồng '+(n.community+1)+'</span></div>';
 const ranked=[...data.nodes].sort((a,b)=>b.pagerank-a.pagerank);
 $('metrics').innerHTML=metric('Láng giềng trực tiếp',degree,'Đồ thị đơn vô hướng')+metric('Quan hệ có dấu + / −',incident.filter(e=>e.sign===1).length+' / '+incident.filter(e=>e.sign===-1).length,'Theo các bản ghi cạnh')+metric('Hạng PageRank',ranked.findIndex(x=>x.id===id)+1,'Trong '+fmt(data.nodes.length)+' thực thể')+metric('Chỉ số k-core',n.core,'Mức kết nối trong lõi mạng');
 const community=data.nodes.filter(x=>x.community===n.community).sort((a,b)=>b.pagerank-a.pagerank);
 $('insights').innerHTML='<p>'+safe(n.name)+' có '+degree+' láng giềng trực tiếp và '+incident.length+' bản ghi quan hệ. Thuộc cộng đồng '+(n.community+1)+' với '+community.length+' thực thể.</p><p>Hạt nhân cộng đồng theo PageRank: <button data-entity="'+community[0].id+'">'+safe(community[0].name)+'</button>.</p><small>PageRank mô tả vị trí trong mạng dữ liệu. Dấu, chiều và thời gian cần đọc trên từng cạnh.</small>';
 $('evidence').innerHTML=incident.slice().sort((a,b)=>(a.year||0)-(b.year||0)).slice(0,80).map(e=>'<div class="evidence"><button data-entity="'+(e.source===id?e.target:e.source)+'">'+safe(nodes.get(e.source===id?e.target:e.source).name)+'</button><small>'+safe(rel[e.relation]||e.relation)+' · '+safe(edgePeriod(e))+' · '+(e.source===id?'Đi ra':'Đi vào')+' · '+(e.sign===1?'+1':e.sign===-1?'−1':'Bối cảnh')+'</small>'+sourceLink(e)+(e.human_review_pending?'<small>Chờ sinh viên kiểm chứng độc lập</small>':'')+(e.evidence?'<details><summary>Đọc bằng chứng</summary><p>'+safe(e.evidence)+'</p><small>'+safe(e.section||'')+' '+safe(e.locator||'')+'</small></details>':'')+'</div>').join('')||'<p>Chưa có quan hệ.</p>';
 const years=[...new Set(incident.flatMap(e=>e.start_year!=null&&e.end_year!=null?Array.from({length:Math.max(0,Math.min(1945,e.end_year)-Math.max(1939,e.start_year)+1)},(_,i)=>Math.max(1939,e.start_year)+i):e.year?[e.year]:[]))].sort();
 $('timeline').innerHTML=years.map(y=>'<div class="timeline"><strong>'+y+'</strong>'+incident.filter(e=>GraphModel.matchesYear(e,y)).slice(0,15).map(e=>'<div>'+safe(nodes.get(e.source).name)+' · '+safe(rel[e.relation])+' · '+safe(nodes.get(e.target).name)+(e.start_year!=null?' ('+safe(edgePeriod(e))+')':'')+'</div>').join('')+'</div>').join('');
 draw();bindEntities();
}
function bindEntities(){document.querySelectorAll('[data-entity]').forEach(b=>b.onclick=()=>{go('profile');select(b.dataset.entity);window.scrollTo({top:160,behavior:'smooth'})})}
function allowed(e){const v=$('sign').value;return v==='all'||(v==='0'?e.sign==null:e.sign===Number(v))}
function neighborhood(){
 const dist=new Map([[selected.id,0]]),q=[selected.id],max=Number($('hops').value);let truncated=false;
 for(let i=0;i<q.length;i++){let id=q[i];if(dist.get(id)>=max)continue;for(const e of adj.get(id)||[]){if(!allowed(e))continue;let v=e.source===id?e.target:e.source;if(!dist.has(v)){if(dist.size>=Number($('neighborlimit').value)){truncated=true;continue}dist.set(v,dist.get(id)+1);q.push(v)}}}
 return {dist,edges:data.edges.filter(e=>dist.has(e.source)&&dist.has(e.target)&&allowed(e)),truncated};
}
function draw(){
 const {dist,edges,truncated}=neighborhood(),items=[...dist.keys()].map(id=>nodes.get(id));
 $('networkcount').textContent=items.length+' nút · '+edges.length+' quan hệ'+(truncated?' · Đang giới hạn '+$('neighborlimit').value+' nút; xem toàn cảnh để khám phá đầy đủ':'');
 if(!egoView)egoView=new GraphView($('graph'),{relations:rel,onSelect:id=>select(id),onOpen:id=>select(id),onEdge:e=>{$('ego-detail').innerHTML='<b>'+safe(nodes.get(e.source.id).name)+'</b> · '+safe(rel[e.relation]||e.relation)+' · <b>'+safe(nodes.get(e.target.id).name)+'</b> · '+safe(edgePeriod(e))+' '+sourceLink(e)}});
 egoView.setData(items,edges,{focus:selected.id});$('ego-detail').textContent='Bấm nút để mở hồ sơ; rê chuột lên cạnh để xem loại quan hệ, bấm để đọc nguồn. Nhãn tự ẩn khi thiếu chỗ.';
}
function answerQuestion(){
 if(!qaEngine){$('answer').textContent='Đang tải dữ liệu đồ thị, vui lòng thử lại sau vài giây.';return}
 requestToken++;$('slmanswer').textContent='';
 const result=qaEngine.answer($('question').value,selected.id);
 lastContext=result.context||[];lastPath=result.path||[];qaRequest=result.kind==='path'?{start:result.start,target:result.target,question:$('question').value||'Giải thích mối liên hệ giữa hai thực thể'}:null;
 $('slm').disabled=!qaRequest||modelBusy;
 $('answer').innerHTML='<strong>'+safe(result.title)+'</strong><div class="qa-text">'+safe(result.text)+'</div>'+(lastContext.length?'<details class="qa-sources"><summary>Nguồn và bằng chứng ('+lastContext.length+')</summary>'+lastContext.map(e=>'<div class="step">['+e.citation+'] '+safe(e.source)+' · '+safe(rel[e.relation]||e.relation)+' · '+safe(e.target)+' · '+safe(edgePeriod(e))+'<br>'+sourceLink({wiki_url:e.url,method:'Bằng chứng'})+(e.evidence?'<p>'+safe(e.evidence)+'</p>':'')+'</div>').join('')+'</details>':'')+(result.choices?result.choices.map(n=>'<button class="secondary" data-entity="'+safe(n.id)+'">'+safe(n.name)+' · '+safe(n.country||kind[n.kind])+'</button>').join(''):'');
 bindEntities();
}
$('ask').onclick=answerQuestion;
$('question').onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();answerQuestion()}};
$('question').oninput=()=>{requestToken++;qaRequest=null;lastContext=[];$('slm').disabled=true};
document.querySelectorAll('[data-question]').forEach(b=>b.onclick=()=>{$('question').value=b.dataset.question;answerQuestion()});
async function localModel(route,body,out){
 if(modelBusy){out.textContent='Một yêu cầu mô hình đang chạy. Vui lòng chờ.';return}
 if(!['127.0.0.1','localhost'].includes(location.hostname)){out.textContent='Chức năng Qwen dùng bản cục bộ. Mở README trong gói mã nguồn và chạy server.py cùng mô hình đã tải.';return}
 const token=requestToken;modelBusy=true;$('slm').disabled=true;$('enrich').disabled=true;out.textContent='Đang gọi Qwen cục bộ. CPU có thể cần vài phút…';
 try{const r=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!r.ok)throw Error(await r.text());const d=await r.json();if(token===requestToken){out.textContent=d.response||JSON.stringify(d,null,2);if(d.citation_ids_valid===false)out.textContent+='\nCần kiểm tra lại: câu trả lời chưa dẫn đúng mã nguồn được truy xuất.'}}
 catch(e){if(token===requestToken)out.textContent='Không gọi được mô hình. Kiểm tra llama.cpp hoặc Ollama theo README. '+String(e.message).slice(0,160)}
 finally{modelBusy=false;$('slm').disabled=!qaRequest;$('enrich').disabled=false}
}
$('slm').onclick=()=>{if(!qaRequest){$('slmanswer').textContent='Hãy hỏi về đường liên hệ giữa hai thực thể trước.';return}localModel('/api/answer',qaRequest,$('slmanswer'))};
$('enrich').onclick=()=>localModel('/api/enrich',{text:$('enrichtext').value,url:$('sourceurl').value},$('enrichout'));
$('export').onclick=()=>{const blob=new Blob([JSON.stringify({node:selected,relations:adj.get(selected.id),retrieved_paths:lastContext},null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='entity-profile.json';a.click();URL.revokeObjectURL(a.href)};
$('search').oninput=()=>{const term=$('search').value.trim().toLocaleLowerCase();$('results').innerHTML=term?data.nodes.filter(n=>n.name.toLocaleLowerCase().includes(term)).slice(0,15).map(n=>'<button data-entity="'+n.id+'">'+safe(n.name)+'<small>'+safe(kind[n.kind])+'</small></button>').join(''):'';bindEntities()};
$('hops').onchange=draw;$('sign').onchange=draw;$('neighborlimit').onchange=draw;
function ranking(){const mode=$('rankmode').value;const ranked=data.nodes.slice().sort((a,b)=>b[mode]-a[mode]).slice(0,20);$('ranking').innerHTML=ranked.map((n,i)=>'<div class="rankrow"><span>'+String(i+1).padStart(2,'0')+'</span><button data-entity="'+n.id+'">'+safe(n.name)+'<div class="bar" style="width:'+Math.max(2,n[mode]/ranked[0][mode]*100)+'%"></div></button><small>'+n[mode].toFixed(5)+'</small></div>').join('');bindEntities()}
$('rankmode').onchange=ranking;
async function init(){
 try{
 const r=await fetch('graph.json',{cache:'no-store'});if(!r.ok)throw Error('Không đọc được graph.json');data=await r.json();qaEngine=new GraphQA(data);$('ask').disabled=false;nodes=new Map(data.nodes.map(n=>[n.id,n]));adj=new Map(data.nodes.map(n=>[n.id,[]]));data.edges.forEach(e=>{adj.get(e.source).push(e);adj.get(e.target).push(e)});
 $('loadstatus').textContent=fmt(data.nodes.length)+' nút · '+fmt(data.edges.length)+' quan hệ · Bản xuất Neo4j';
 const s=data.stats;$('globalmetrics').innerHTML=metric('Thành phần liên thông',s.components,'Toàn mạng')+metric('Khoảng cách TB',fmt(s.average_shortest_path_lcc),'Thành phần lớn nhất')+metric('Cộng đồng Louvain',s.communities,'Seed 1945')+metric('Modularity',fmt(s.modularity),'Đồ thị đơn vô hướng');
 $('smallworld').innerHTML='<p>Mạng có '+s.components+' thành phần rời nhau. Khoảng cách trung bình toàn mạng khi tính cả cặp không thể đến nhau không xác định. Chỉ '+(s.reachable_fraction*100).toFixed(1)+'% cặp nút có đường đi. Trung bình trên các cặp đến được là '+fmt(s.reachable_pair_mean)+'.</p><table><thead><tr><th>Chỉ số</th><th>Mạng quan sát</th><th>Đối chứng G(n,m), trung bình 3 lần</th></tr></thead><tbody><tr><td>Khoảng cách trung bình</td><td>'+fmt(s.average_shortest_path_lcc)+'</td><td>'+fmt(s.baselines.reduce((a,b)=>a+b.path_length,0)/3)+'</td></tr><tr><td>Hệ số phân cụm</td><td>'+fmt(s.clustering_lcc)+'</td><td>'+fmt(s.baselines.reduce((a,b)=>a+b.clustering,0)/3)+'</td></tr></tbody></table><p>Đo trên thành phần lớn nhất ('+fmt(s.largest_component)+' nút), đường kính '+s.diameter_lcc+'. Chỉ số σ so với G(n,m) = '+fmt(s.sigma_er)+'. Đối chứng giữ số nút và cạnh, chưa giữ phân phối bậc. Kết quả này là kiểm tra định lượng bước đầu cho giả thuyết thế giới nhỏ.</p><p>PageRank và Louvain dùng đồ thị đơn vô hướng, không trọng số. PageRank cạnh dương được tính riêng. K-core cho biết mức lõi cấu trúc của một nút.</p>';
 $('communities').innerHTML=Object.entries(s.community_sizes).sort((a,b)=>Number(a[0])-Number(b[0])).map(([id,size])=>{let group=data.nodes.filter(n=>n.community===Number(id)).sort((a,b)=>b.pagerank-a.pagerank);return '<div class="rankrow"><span>'+(+id+1)+'</span><button data-entity="'+group[0].id+'">'+safe(group[0].name)+'<small> · Hạt nhân theo PageRank</small></button><b>'+size+'</b></div>'}).join('');
 $('methods').innerHTML=Object.entries(s.method_counts).map(([m,c])=>'<div class="rankrow"><span></span><span>'+safe(m)+'</span><strong>'+fmt(c)+'</strong></div>').join('');
 renderDegreeComparison(s);renderModelRun();$('search').labels[0].textContent='Tìm trong '+fmt(data.nodes.length)+' thực thể';select((data.nodes.find(n=>n.name==='Adolf Hitler')||data.nodes[0]).id);ranking();bindEntities();
 }catch(e){$('loadstatus').textContent='Lỗi tải dữ liệu';$('entity').textContent=e.message}
}
const localRuntime=['127.0.0.1','localhost'].includes(location.hostname);$('slm').hidden=!localRuntime;$('slm').disabled=true;$('qa-mode').textContent=localRuntime?'Trả lời từ đồ thị trên trình duyệt. Qwen là tùy chọn diễn giải khi mô hình cục bộ đang chạy.':'Trả lời trực tiếp từ snapshot đồ thị trên web, kèm nguồn. Phần diễn giải Qwen dùng ở bản cục bộ.';if(!localRuntime){$('enrich').disabled=true;$('enrich').textContent='Trích xuất Qwen cần bản cục bộ'}
init();

function renderDegreeComparison(s){
 const ds=s.degree_baselines;if(!ds)return;
 const c=ds.reduce((v,x)=>v+x.clustering,0)/ds.length,l=ds.reduce((v,x)=>v+x.path_length,0)/ds.length;
 $('smallworld').insertAdjacentHTML('beforeend','<h3>Đối chứng bảo toàn bậc</h3><p>Ba mạng được đổi cạnh và giữ liên thông, giữ bậc từng nút. Khoảng cách trung bình '+fmt(l)+', clustering '+fmt(c)+', σ = '+fmt(s.sigma_degree)+'. Đề nghị 5 × số cạnh phép đổi; số phép đổi thành công được lưu trong analysis.json.</p><p><strong>Clustering gần đối chứng bảo toàn bậc. Chưa có bằng chứng mạnh để khẳng định tính thế giới nhỏ.</strong> Cần nhiều lần ngẫu nhiên hóa và kiểm tra hội tụ để kết luận. Kết quả ER chịu ảnh hưởng mạnh của phân phối bậc.</p>');
}

async function renderModelRun(){try{const r=await fetch('model_status.json');if(!r.ok)return;const m=await r.json();$('modelrun').innerHTML='<h3>Kết quả thử SLM trên máy</h3><p>Đã chạy '+m.development_paragraphs+' đoạn phát triển, '+fmt(m.elapsed_seconds)+' giây. Mô hình sinh '+m.raw_relations+' đề xuất. Sau khi bổ sung kiểm tra kiểu hai đầu trên ca phát triển: '+m.validated_after_domain_range_guard+' qua, '+m.rejected_after_domain_range_guard+' bị loại.</p><p>Phát hiện nhầm quốc gia thành sự kiện và xâm lược thành hiệp ước. Đây là kiểm thử phát triển, chưa phải điểm chính xác ngoài mẫu. Không tự nhập các đề xuất lỗi.</p>'}catch{}}
