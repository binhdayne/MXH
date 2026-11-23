(function(root){
'use strict';
const normalize=s=>String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').replace(/[^a-z0-9]+/g,' ').trim();
const relations={ATTENDED:'tham dự',SIGNED:'ký kết',REPRESENTED:'đại diện',ORDERED_INVASION_OF:'ra lệnh xâm lược',DECLARED_WAR_ON:'tuyên chiến với',INVADED:'xâm lược',MILITARY_PACT:'có hiệp ước quân sự với',NON_AGGRESSION_PACT:'có hiệp ước bất tương xâm với',JOINT_DECLARATION:'ra tuyên bố chung với',NOMINATES_CANDIDATE:'đề cử',ELECTORAL_RIVAL:'tranh cử cùng ghế với',LEAVES_PARTY:'rời đảng',JOINS_PARTY_AFTER_SWITCH:'gia nhập đảng sau chuyển',DEMANDS_SURRENDER:'yêu cầu đầu hàng',DIRECTED_AID_TO:'viện trợ cho',CALLED_FOR_RESISTANCE_AGAINST:'kêu gọi kháng cự',EXPRESSED_SUPPORT_FOR:'bày tỏ ủng hộ'};
class GraphQA{
 constructor(data){
  this.data=data;this.nodes=new Map(data.nodes.map(n=>[n.id,n]));this.adj=new Map(data.nodes.map(n=>[n.id,[]]));this.names=new Map();
  for(const n of data.nodes){const key=normalize(n.name);if(!this.names.has(key))this.names.set(key,[]);this.names.get(key).push(n.id)}
  for(const e of data.edges){this.adj.get(e.source)?.push(e);if(e.target!==e.source)this.adj.get(e.target)?.push(e)}
  const aliases={hitler:'Adolf Hitler',stalin:'Joseph Stalin',churchill:'Winston Churchill',roosevelt:'Franklin D. Roosevelt',truman:'Harry S. Truman',attlee:'Clement Attlee',tojo:'Hideki Tōjō','lien xo':'Soviet Union','hoa ky':'United States','nuoc my':'United States','duc quoc xa':'Nazi Germany','nuoc duc':'Nazi Germany','nhat ban':'Empire of Japan','vuong quoc anh':'United Kingdom','nuoc anh':'United Kingdom','tuong gioi thach':'Chiang Kai-shek'};
  for(const [alias,name] of Object.entries(aliases)){const ids=this.names.get(normalize(name));if(ids)this.names.set(alias,ids)}
  this.terms=[...this.names.keys()].filter(s=>s.length>=4).sort((a,b)=>b.length-a.length||a.localeCompare(b));
 }
 mentions(question){
  const namesText=String(question).replace(/(^|[^\p{L}])mỹ(?=$|[^\p{L}])/giu,'$1Hoa Kỳ').replace(/(^|[^\p{L}])đức(?=$|[^\p{L}])/giu,'$1Nazi Germany');
  const q=' '+normalize(namesText)+' ',occupied=[],matches=new Map();let ambiguous=[];
  for(const term of this.terms){let at=q.indexOf(' '+term+' ');while(at>=0){const end=at+term.length+2;if(!occupied.some(([a,b])=>at<b&&end>a)){const ids=this.names.get(term);if(ids.length>1)ambiguous.push(...ids);else matches.set(ids[0],Math.min(matches.get(ids[0])??Infinity,at));occupied.push([at,end-1])}at=q.indexOf(' '+term+' ',at+1)}}
  return {ids:[...matches].sort((a,b)=>a[1]-b[1]).map(x=>x[0]),ambiguous:[...new Set(ambiguous)]};
 }
 context(edges){return edges.map((e,i)=>({citation:i+1,edge_id:e.id,source:this.nodes.get(e.source).name,target:this.nodes.get(e.target).name,relation:e.relation,year:e.year,sign:e.sign??null,url:e.wiki_url,evidence:e.evidence||null,event:e.event||null}))}
 fact(e){return `${e.source} ${relations[e.relation]||e.relation} ${e.target}${e.year?' năm '+e.year:''} [${e.citation}].`}
 path(start,target,filter=()=>true){
  const queue=[start],seen=new Map([[start,{depth:0}]]);
  for(let i=0;i<queue.length;i++){const id=queue[i],p=seen.get(id);if(id===target)break;if(p.depth===4)continue;for(const e of this.adj.get(id)||[]){if(!filter(e))continue;const other=e.source===id?e.target:e.source;if(!seen.has(other)){seen.set(other,{depth:p.depth+1,node:id,edge:e});queue.push(other)}}}
  if(!seen.has(target))return null;const result=[];for(let id=target;id!==start;){const p=seen.get(id);result.unshift(p.edge);id=p.node}return result;
 }
 answer(question,selectedId,targetId){
  if(!this.nodes.has(selectedId))return {kind:'error',title:'Dữ liệu chưa sẵn sàng',text:'Hãy đợi tải dữ liệu rồi thử lại.',context:[]};
  const q=normalize(question),m=this.mentions(question),selected=this.nodes.get(selectedId);
  const result=(kind,title,text,extra={})=>({kind,title,text,context:[],...extra});
  if(m.ambiguous.length)return result('clarify','Tên thực thể bị trùng','Tên trong câu hỏi khớp nhiều node. Chọn đúng thực thể theo quốc gia ở ô tìm kiếm rồi hỏi lại.',{choices:m.ambiguous.map(id=>this.nodes.get(id))});
  if(m.ids.length>2)return result('clarify','Hãy hỏi tối đa hai thực thể','Có nhiều hơn hai thực thể trong câu hỏi. Hãy tách câu hỏi để truy xuất bằng chứng rõ ràng.');
  if(/tai sao|vi sao|nguyen nhan|why|sinh ngay|ngay sinh|born|vo cua|chong cua|o dau|where|bao nhieu tuoi|qua doi|died/.test(q))return result('unsupported','Chưa đủ dữ liệu để trả lời','Snapshot chưa lưu dữ liệu cần thiết cho câu hỏi này. Có thể hỏi về quan hệ, năm, PageRank, cộng đồng hoặc dòng thời gian.');
  const id=m.ids[0]||selectedId,n=this.nodes.get(id),yearMatch=q.match(/\b(?:18|19|20)\d{2}\b/),year=yearMatch?Number(yearMatch[0]):null;
  if(year&&(year<1939||year>1945))return result('unsupported','Năm nằm ngoài phạm vi','Bản dữ liệu này tập trung vào giai đoạn 1939–1945.');
  if(/the gioi nho|khoang cach|small world|bao nhieu nut|bao nhieu canh|quy mo|thong ke toan/.test(q)){
   const s=this.data.stats;return result('statistics','Thống kê mạng',`Snapshot có ${s.nodes} nút, ${s.edges} cạnh và ${s.components} thành phần liên thông. Khoảng cách trung bình của thành phần lớn nhất là ${s.average_shortest_path_lcc.toFixed(3)}. Toàn mạng rời nhau; chưa đủ bằng chứng mạnh để kết luận thế giới nhỏ.`);
  }
  if(/pagerank|xep hang|anh huong nhat|quan trong nhat/.test(q)){
   const ranked=this.data.nodes.slice().sort((a,b)=>b.pagerank-a.pagerank);
   if(!m.ids.length&&/cao nhat|dau|top|nhat/.test(q)){const people=/chinh khach|nhan vat|politician|person|^ai\b/.test(q),list=people?ranked.filter(x=>x.kind==='WartimePolitician'):ranked;return result('ranking',people?'PageRank của chính khách / ứng viên':'Xếp hạng PageRank',list.slice(0,10).map((x,i)=>`${i+1}. ${x.name}: ${x.pagerank.toFixed(6)}`).join('\n')+'\nĐiểm số phản ánh vị trí trong corpus, không phải mức ảnh hưởng lịch sử.');}
   return result('ranking','PageRank của '+n.name,`${n.name} có PageRank ${n.pagerank.toFixed(6)}, hạng ${ranked.findIndex(x=>x.id===id)+1}/${ranked.length}. Chỉ số tính trên đồ thị đơn vô hướng của snapshot.`);
  }
  if(/cong dong|community|hat nhan|k core|loi cau truc/.test(q)){
   if(!m.ids.length&&/toan mang|mang co|bao nhieu cong dong/.test(q))return result('community','Cộng đồng toàn mạng',`Louvain tìm được ${this.data.stats.communities} cộng đồng, modularity ${this.data.stats.modularity.toFixed(3)}.`);
   const group=this.data.nodes.filter(x=>x.community===n.community).sort((a,b)=>b.pagerank-a.pagerank);
   return result('community','Cộng đồng của '+n.name,`${n.name} thuộc cộng đồng ${n.community+1}, gồm ${group.length} thực thể. Hạt nhân theo PageRank là ${group[0].name}. Chỉ số k-core của ${n.name} là ${n.core}.`);
  }
  const positive=/dong minh|ung ho|ho tro|lien minh|canh duong|allies|support/.test(q),negative=/doi lap|doi thu|ke thu|canh am|oppos|rival/.test(q);
  if(m.ids.length===1&&/\b(va|and|vs)\b/.test(q)&&/lien he|quan he|giua|between/.test(q))return result('clarify','Chưa xác định đủ hai thực thể','Một tên trong câu hỏi chưa khớp với node. Hãy chọn đúng tên trong ô tìm kiếm hoặc dùng tên đầy đủ.');
  const subject=q.match(/^(.{3,45}?)\s+(?:co |thuoc |tuyen chien |tham du |la ai)/);
  if(!m.ids.length&&subject&&!['node nay','thuc the nay','nhan vat nay','ong ay','mang','toan mang'].includes(subject[1]))return result('clarify','Chưa nhận diện được thực thể','Không tìm thấy tên này trong snapshot. Hãy tìm và chọn một thực thể trước khi hỏi.');
  const filter=e=>(!year||Number(e.year)===year)&&(!positive||e.sign===1)&&(!negative||e.sign===-1);
  const wantsList=/voi ai|nhung ai|gom ai|quan he nao|su kien nao|bao nhieu quan he/.test(q);
  const pair=m.ids.length===2||!q||(!wantsList&&/giua|between|lien he.*voi|quan he.*voi/.test(q));
  if(pair){
   let start=m.ids.length===2?m.ids[0]:selectedId,target=m.ids.length===2?m.ids[1]:m.ids.length===1&&m.ids[0]!==selectedId?m.ids[0]:targetId;
   if(q&&m.ids.length===1&&m.ids[0]===selectedId)return result('clarify','Chưa xác định đủ hai thực thể','Hãy dùng tên của cả hai thực thể. Hoặc chọn thực thể đích và để trống câu hỏi để tìm đường đi.');
   if(!this.nodes.has(target))return result('clarify','Chưa có thực thể đích','Hãy chọn một thực thể đích để tìm đường đi.');
   if(start===target)return result('same_entity','Hai đầu mút trùng nhau','Hãy chọn hai thực thể khác nhau.');
   const path=this.path(start,target,filter),a=this.nodes.get(start).name,b=this.nodes.get(target).name;
   if(!path)return result('not_found','Chưa tìm được bằng chứng',`Không có đường đi phù hợp trong tối đa 4 bước giữa ${a} và ${b}${year?' ở năm '+year:''}. Điều này không khẳng định hai thực thể chưa từng có quan hệ trong lịch sử.`);
   const context=this.context(path);
   return result('path',`Mối liên hệ ${path.length} bước`,context.map(e=>this.fact(e)).join('\n')+'\nĐường đi giữ chiều cạnh gốc. Chuỗi liên hệ không tự chứng minh liên minh hoặc quan hệ nhân quả giữa hai đầu mút.',{context,path,start,target});
  }
  const timeline=/dong thoi gian|dien bien|timeline|theo nam/.test(q);
  const profile=/la ai|ho so|chan dung|thong tin|profile/.test(q);
  const links=timeline||positive||negative||profile||year||/quan he|lien he|ket noi|tuyen chien|xam luoc|tham du|ky ket|chuyen dang|roi dang|gia nhap|declare|invasion/.test(q);
  if(!links)return result('unsupported','Các dạng câu hỏi đang hỗ trợ','Có thể hỏi: “Hitler tuyên chiến với ai năm 1941?”, “Hitler và Stalin có mối liên hệ gì?”, “PageRank của Hitler là bao nhiêu?” hoặc “Hitler thuộc cộng đồng nào?”.');
  let edges=(this.adj.get(id)||[]).filter(filter),relationFilter=null;
  if(/tuyen chien|declare war/.test(q))relationFilter=['DECLARED_WAR_ON'];
  else if(/xam luoc|invasion/.test(q))relationFilter=['INVADED','ORDERED_INVASION_OF'];
  else if(/tham du/.test(q))relationFilter=['ATTENDED'];
  else if(/ky ket/.test(q))relationFilter=['SIGNED'];
  else if(/chuyen dang|roi dang|gia nhap/.test(q))relationFilter=['LEAVES_PARTY','JOINS_PARTY_AFTER_SWITCH'];
  if(relationFilter){edges=edges.filter(e=>relationFilter.includes(e.relation));const incoming=/^ai\b/.test(q)||n.kind==='WartimeEvent';edges=edges.filter(e=>incoming?e.target===id:e.source===id)}
  edges.sort((a,b)=>(a.year||0)-(b.year||0)||String(a.id).localeCompare(String(b.id)));
  if(!edges.length)return result('not_found','Chưa có cạnh phù hợp',`Snapshot chưa ghi nhận cạnh phù hợp cho ${n.name}${year?' ở năm '+year:''}. Không suy ra rằng quan hệ này không tồn tại trong lịch sử.`);
  const context=this.context(edges.slice(0,20));
  const prefix=profile?`${n.name} có ${n.degree} láng giềng trực tiếp, k-core ${n.core}.\n`:'';
  return result(timeline?'timeline':'relations',timeline?'Dòng thời gian của '+n.name:'Quan hệ của '+n.name,prefix+context.map(e=>this.fact(e)).join('\n')+(edges.length>20?`\nHiển thị 20/${edges.length} cạnh phù hợp. Có thể thêm năm hoặc loại quan hệ để lọc.`:'')+(positive?'\nCạnh dương thể hiện hỗ trợ/liên kết đã lưu; không tự xác nhận mọi quan hệ đồng minh cá nhân.':''),{context});
 }
}
if(typeof module!=='undefined'&&module.exports)module.exports=GraphQA;else root.GraphQA=GraphQA;
})(typeof globalThis!=='undefined'?globalThis:this);
