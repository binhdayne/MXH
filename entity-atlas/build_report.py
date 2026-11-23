"""Generate the 13-page course report from the delivered snapshot."""
import json,math,sys
from pathlib import Path
from collections import Counter
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing,Rect,String,Line,Circle
from graph_core import GraphStore

ROOT=Path(__file__).parent
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'Bao-cao-Entity-Atlas.pdf'
pdfmetrics.registerFont(TTFont('Arial','C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('ArialBold','C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='ArialBold',italic='Arial',boldItalic='ArialBold')
INK=colors.HexColor('#183b35');MUTED=colors.HexColor('#52616d');LINE=colors.HexColor('#d9e2df')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyVN',fontName='Arial',fontSize=10.3,leading=16,spaceAfter=10,textColor=MUTED))
styles.add(ParagraphStyle(name='SmallVN',parent=styles['BodyVN'],fontSize=8.5,leading=12))
styles.add(ParagraphStyle(name='TitleVN',fontName='ArialBold',fontSize=29,leading=37,textColor=INK,spaceAfter=22))
styles.add(ParagraphStyle(name='HeadVN',fontName='ArialBold',fontSize=19,leading=25,textColor=INK,spaceAfter=17))
styles.add(ParagraphStyle(name='SubVN',fontName='ArialBold',fontSize=12,leading=17,textColor=INK,spaceAfter=9,spaceBefore=8))
story=[];g=GraphStore();data=g.data;s=data['stats'];nodes=g.nodes
def fmt(x,d=3):return f'{x:,.{d}f}' if isinstance(x,float) else f'{x:,}' if isinstance(x,int) else str(x)
def p(text,style='BodyVN'):story.append(Paragraph(text,styles[style]))
def h(text):p(text,'SubVN')
def page(number,title):
 if story:story.append(PageBreak())
 p(f'ENTITY ATLAS / {number:02d}','SmallVN');p(title,'HeadVN')
def table(headers,rows,widths=None):
 content=[[Paragraph(escape(str(x)),styles['SmallVN']) for x in headers]]+[[Paragraph(escape(str(x)),styles['SmallVN']) for x in row] for row in rows]
 t=Table(content,colWidths=widths or [475/len(headers)]*len(headers),repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7efeb')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.4,LINE),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
 story.append(t);story.append(Spacer(1,14))
def footer(c,doc):
 c.setStrokeColor(LINE);c.line(60,48,535,48);c.setFont('Arial',8);c.setFillColor(MUTED)
 c.drawString(60,34,'Dương Thanh Bình 23020516 · Nguyễn Hải Dương 23020523')
 c.drawRightString(535,34,str(doc.page))
def bar_chart(items,title):
 d=Drawing(475,230);d.add(String(0,215,title,fontName='ArialBold',fontSize=10,fillColor=INK))
 peak=max(v for _,v in items) or 1
 for i,(name,value) in enumerate(items):
  y=190-i*20;d.add(String(0,y, name[:29],fontName='Arial',fontSize=8,fillColor=MUTED))
  d.add(Rect(170,y-2,230*value/peak,9,fillColor=INK,strokeColor=None))
  d.add(String(410,y,fmt(value,5),fontName='Arial',fontSize=8,fillColor=MUTED))
 story.append(d)

page(1,'CHÂN DUNG THỰC THỂ\nTRÊN ĐỒ THỊ THẾ CHIẾN II')
p('Báo cáo ứng dụng, làm giàu văn bản và phân tích mạng xã hội','TitleVN')
p('Phạm vi nghiên cứu: các thực thể chính trị liên quan giai đoạn 1939–1945. Nguồn dữ liệu là Wikipedia tiếng Anh. Cơ sở lưu trữ chính là Neo4j; ứng dụng phân tích dùng một snapshot có dẫn nguồn.')
table(['Sinh viên','Mã sinh viên'],[['Dương Thanh Bình','23020516'],['Nguyễn Hải Dương','23020523']],[290,185])
table(['Quy mô snapshot','Kết quả'],[['Nút',fmt(s['nodes'])],['Bản ghi cạnh',fmt(s['edges'])],['Loại quan hệ',len(set(e['relation'] for e in data['edges']))],['Thành phần liên thông',s['components']],['Cộng đồng Louvain',s['communities']]],[290,185])
p('Ngày bàn giao: 23/11/2026. Các số liệu trong báo cáo được đọc trực tiếp từ snapshot đi kèm. Không quy đổi số cạnh khớp bảng thành độ chính xác của toàn bộ hệ thống NLP.','SmallVN')

page(2,'Mục tiêu, phạm vi và tiêu chí cuối kỳ')
p('Entity Atlas trả lời một nhu cầu cụ thể: chọn một thực thể, đọc các quan hệ có bằng chứng xung quanh nó, xác định vị trí cấu trúc và truy vết mối liên hệ với một thực thể khác. Mỗi mối quan hệ được hiểu theo loại, chiều, dấu và thời gian.')
table(['Tiêu chí','Sản phẩm kiểm tra được'],[
 ['Thu thập và chọn corpus','24 đoạn / 4 bài; URL phiên bản, hash HTML, split theo bài'],
 ['Nhận dạng node và cạnh','Qwen 3B sinh cấu trúc; bộ kiểm tra ontology và quote'],
 ['Đánh giá','Audit bảng, dữ liệu thô model và công cụ exact-match NER/RE'],
 ['Thế giới nhỏ','BFS chính xác, clustering, 2 loại null model'],
 ['Xếp hạng và cộng đồng','PageRank, Louvain, modularity và k-core'],
 ['SLM ≤9B','Qwen2.5-3B-Instruct, 3,09 tỷ tham số'],
 ['GraphRAG và multi-hop','Đường đi tối đa 4 bước, nguồn mỗi cạnh, Qwen diễn giải'],
 ['Chân dung thực thể','Ego graph, chỉ số, dòng thời gian, bằng chứng, JSON']],[145,330])
h('Giới hạn của phạm vi ảnh hưởng')
p('Quy mô mạng được mở rộng bằng ứng viên bầu cử thời chiến tại Mỹ, Anh và Úc. Không phải mọi ứng viên đều là lãnh tụ có ảnh hưởng quốc tế. Lớp hội nghị, hiệp ước và chính sách đối ngoại bổ sung bối cảnh các nước tham chiến. Những độ phủ khác nhau này phải được xem xét khi đọc PageRank và cộng đồng.')

page(3,'Dữ liệu nguồn và quy trình tiền xử lý')
table(['Loại node','Số lượng'],sorted(Counter(n['kind'] for n in data['nodes']).items()),[310,165])
table(['Phương pháp tạo cạnh','Số lượng'],sorted(s['method_counts'].items()),[310,165])
p('Pipeline nền đọc các bảng Wikipedia và liên kết nội bộ, giữ tên người/đảng, vị trí bảng, khu vực tranh cử và năm. Lớp văn bản sử dụng đoạn tiểu sử và chính sách đối ngoại. Lớp ngoại giao bổ sung hội nghị và hiệp ước theo nguồn cụ thể.')
h('Làm sạch có kiểm soát')
p('Thu thập HTML, ghi URL phiên bản và SHA-256; loại script, style và ký hiệu tham khảo; chuẩn hóa khoảng trắng; giữ ranh giới đoạn. Không bỏ phủ định, tên riêng hoặc biểu thức thời gian. Khi hai đảng cùng tên thuộc hai nước khác nhau, không được hợp nhất chỉ vì chuỗi giống nhau.')
h('Corpus làm giàu bổ sung')
p('collect_corpus.py chọn 24 đoạn từ bốn bài Adolf Hitler, Winston Churchill, Joseph Stalin và Franklin D. Roosevelt. Hitler và Churchill thuộc tập phát triển. Stalin và Roosevelt được dành cho đánh giá giữ riêng theo bài, giảm rò rỉ giữa các đoạn gần giống nhau. Mỗi đoạn có ID, URL và hash của HTML.')
p('Các câu trong corpus không mặc nhiên tạo thành cạnh. Mô hình có thể bỏ sót, đồng nhất sai tên hoặc suy diễn vượt văn bản; vì vậy đề xuất phải qua kiểm định và quy trình duyệt trước khi sử dụng.','SmallVN')

page(4,'Mô hình nhận dạng và liên kết thực thể')
p('Chọn Qwen2.5-3B-Instruct, 3,09 tỷ tham số, đáp ứng giới hạn không quá 9 tỷ. Bản cục bộ dùng trọng số GGUF Q4_K_M và llama.cpp CPU. Hệ thống cũng hỗ trợ Ollama qwen2.5:3b. Lượng tử hóa làm giảm bộ nhớ cần thiết nhưng vẫn phải đánh giá chất lượng thực nghiệm.')
table(['Nhãn trích xuất','Ý nghĩa và quy tắc'],[['Person','Tên người, phân biệt với chức vụ hoặc tập thể'],['Party','Đảng hoặc tổ chức chính trị được nói rõ'],['Government','Nhà nước/chính phủ theo đúng bối cảnh lịch sử'],['Event','Hội nghị, hiệp ước hoặc sự kiện xác định']],[120,355])
h('Liên kết với node có sẵn')
p('Trích xuất một chuỗi tên chưa đồng nghĩa xác định được node. Cần chuẩn hóa tên đầy đủ, đối chiếu bí danh, quốc gia và loại thực thể. Việc nhập cạnh yêu cầu ID chính xác của hai đầu. apply_reviewed.py không tự hợp nhất theo tên, tránh nối nhầm các ứng viên hay tổ chức trùng tên.')
h('Đầu ra có thể kiểm tra')
p('Mô hình trả entities và relations trong JSON. Mỗi thực thể có name và type. Raw của mô hình được giữ cùng bản qua kiểm tra để tránh che giấu lỗi bằng bước hậu xử lý. Bộ kiểm tra chỉ nhận các nhãn đã khai báo; đề xuất không hợp lệ được đưa vào rejected kèm lý do.')
p('Nhận dạng đại từ và đồng tham chiếu là điểm khó. Ví dụ “he” có thể chỉ nhân vật của câu trước; không được gán người nói hoặc người ký chỉ vì họ cùng xuất hiện trong một đoạn. NER cần đánh giá exact match hoặc span match riêng với bước liên kết ID.')

page(5,'Ontology quan hệ và đồ thị có dấu')
p('Mỗi cạnh lưu source, target, relation, sign, year, wiki_url, method và bằng chứng nếu có. Cạnh đối xứng có symmetric=true; chiều lưu trữ không làm thay đổi nghĩa đối xứng. Bối cảnh tham dự/ký kết không được gán dấu dương thay cho liên minh.')
counts=Counter(e['relation'] for e in data['edges'])
table(['Quan hệ trong snapshot','Số cạnh','Ý nghĩa dấu'],[[r,c,'Theo từng bản ghi; bối cảnh có sign null' if r in ('ATTENDED','SIGNED','REPRESENTED','LED_GOVERNMENT','LED_PARTY') else ('Dương / hỗ trợ' if next(e for e in data['edges'] if e['relation']==r).get('sign')==1 else 'Âm / đối lập')] for r,c in sorted(counts.items())],[225,60,190])
p('Chuyển đảng biểu diễn bằng cạnh rời đảng và gia nhập đảng sau chuyển, không suy ra mọi lần đổi tên đảng đều là chuyển đảng. Thời gian và nguồn là điều kiện để diễn giải dấu hợp lý.','SmallVN')

page(6,'Đánh giá chất lượng và những gì chưa được chứng minh')
table(['Tầng audit bảng','Khớp / mẫu','Cận dưới Wilson 95%'],[['NOMINATES_CANDIDATE','100 / 100','96,3%'],['ELECTORAL_RIVAL','100 / 100','96,3%']],[230,90,155])
p('Kết quả trên là đối chiếu với nguồn của mẫu cạnh bảng đã có. Nó không phải đánh giá độc lập của NER hoặc RE, không đo recall của trình thu thập và không thể dùng để khẳng định toàn bộ đồ thị vượt 90%. Các cạnh NLP nền đã được dùng khi xây luật nên không phải tập ngoài mẫu.')
h('Đánh giá NER và RE')
p('Hai sinh viên nên gán nhãn độc lập các đoạn giữ riêng, giải quyết bất đồng và giữ lịch sử nhãn. evaluate.py từ chối bản gold còn annotated=false. NER chấm tên và loại thực thể. RE chấm đồng thời source, target, type, sign và year. Báo precision, recall, F1 theo từng quan hệ, micro toàn tập và cỡ mẫu.')
p('Precision = TP/(TP+FP); Recall = TP/(TP+FN); F1 = 2TP/(2TP+FP+FN). Khi mẫu số bằng 0, công cụ ghi null thay vì tự coi là điểm hoàn hảo. Cận dưới Wilson cần được đọc cùng thiết kế lấy mẫu; các cạnh phụ thuộc trong cùng bảng không tạo bằng chứng độc lập hoàn toàn.')
h('Đánh giá GraphRAG')
p('Kiểm tra đường đi có tồn tại; chiều và năm có được giữ; mỗi citation có hỗ trợ nhận định; câu trả lời có thừa suy diễn; trường hợp thiếu dữ liệu có từ chối đúng. Chỉ kiểm tra số citation hợp lệ là chưa đủ chứng minh faithfulness.')

page(7,'Khoảng cách ngắn nhất và giả thuyết thế giới nhỏ')
table(['Chỉ số cấu trúc','Giá trị'],[['Cạnh đơn vô hướng',s['simple_edges']],['Số thành phần',s['components']],['Kích thước LCC',s['largest_component']],['Khoảng cách trung bình LCC',fmt(s['average_shortest_path_lcc'])],['Đường kính LCC',s['diameter_lcc']],['Trung bình cặp đến được',fmt(s['reachable_pair_mean'])],['Tỷ lệ cặp đến được',fmt(s['reachable_fraction']*100)+'%']],[310,165])
p('Tính chính xác bằng BFS từ mỗi node. Toàn mạng rời nhau nên khoảng cách trung bình trên mọi cặp, bao gồm cặp không thể đến nhau, không có một giá trị hữu hạn. Báo riêng LCC và tập cặp đến được tránh bỏ qua các thành phần nhỏ.')
ds=s.get('degree_baselines',[])
er=s['baselines'];avg=lambda xs,k:sum(x[k] for x in xs)/len(xs)
table(['Đối tượng','Khoảng cách TB','Clustering'],[['LCC quan sát',fmt(s['average_shortest_path_lcc']),fmt(s['clustering_lcc'])],['G(n,m), 3 mẫu',fmt(avg(er,'path_length')),fmt(avg(er,'clustering'))],['Giữ bậc, 3 mẫu',fmt(avg(ds,'path_length')) if ds else '-',fmt(avg(ds,'clustering')) if ds else '-']],[210,130,135])
p('σ so ER = '+fmt(s['sigma_er'])+'; σ so đối chứng bảo toàn bậc = '+fmt(s.get('sigma_degree',0))+'. Đối chứng giữ bậc có clustering gần mạng quan sát. Chưa có bằng chứng mạnh để khẳng định tính thế giới nhỏ. Cần nhiều mẫu đổi cạnh hơn, kiểm tra hội tụ và kiểm định thống kê. ER không giữ phân phối bậc nên dễ cho kết luận quá mạnh.')

page(8,'PageRank và cách đọc kết quả xếp hạng')
p('PageRank dùng α=0,85, teleportation đều và phân phối lại xác suất của dangling node. Power iteration dừng khi tổng sai khác nhỏ hơn n × 10⁻¹². Toàn mạng được chiếu đơn vô hướng; phiên bản chỉ cạnh dương được tính riêng, không đưa sign=-1 thành trọng số âm.')
ranking=sorted(data['nodes'],key=lambda n:n['pagerank'],reverse=True)
bar_chart([(n['name'],n['pagerank']) for n in ranking[:9]],'PageRank cao nhất trong toàn corpus')
people=[n for n in ranking if n['kind']=='WartimePolitician'][:7]
table(['Chính khách / ứng viên','PageRank'],[[n['name'],fmt(n['pagerank'],6)] for n in people],[330,145])
p('Các đảng có nhiều ứng viên thường đứng cao vì có nhiều cạnh đề cử. Đây là tính chất của mô hình hóa và độ phủ dữ liệu. Không kết luận một đảng hay ứng viên có ảnh hưởng lịch sử lớn hơn Hitler hoặc Stalin chỉ dựa vào bảng xếp hạng này.','SmallVN')

page(9,'Phát hiện cộng đồng và tìm hạt nhân')
p('Louvain tối ưu modularity trên đồ thị đơn vô hướng, seed 1945. Kết quả có '+str(s['communities'])+' cộng đồng và modularity '+fmt(s['modularity'])+'. Hạt nhân được định nghĩa rõ là node có PageRank toàn mạng cao nhất trong cộng đồng đó; đây là lựa chọn thao tác, không phải kết luận về lãnh tụ chính trị.')
groups={}
for n in data['nodes']:groups.setdefault(n['community'],[]).append(n)
table(['Cộng đồng','Số node','Hạt nhân theo PageRank'],[[i+1,len(v),max(v,key=lambda n:n['pagerank'])['name']] for i,v in sorted(groups.items(),key=lambda x:len(x[1]),reverse=True)[:8]],[80,80,315])
h('Lõi k-core')
core_counts=Counter(n['core'] for n in data['nodes'])
table(['Khoảng k-core','Số node'],[[label,sum(c for k,c in core_counts.items() if lo<=k<=hi)] for label,lo,hi in [('0',0,0),('1',1,1),('2',2,2),('3–5',3,5),('6–10',6,10),('Trên 10',11,10000)]],[220,255])
p('k-core đo mức bậc tối thiểu khi bóc các node bậc thấp lặp lại. Cộng đồng phản ánh cụm kết nối; k-core phản ánh lõi kết nối; PageRank phản ánh xác suất đi ngẫu nhiên. Ba khái niệm bổ sung nhau và không nên dùng thay thế nhau.','SmallVN')

page(10,'Chân dung Adolf Hitler và bằng chứng lân cận')
hitler=next(n for n in data['nodes'] if n['name']=='Adolf Hitler');incident=g.adj[hitler['id']]
table(['Chỉ số hồ sơ','Giá trị'],[['Láng giềng trực tiếp',hitler['degree']],['Bản ghi quan hệ',len(incident)],['PageRank',fmt(hitler['pagerank'],7)],['Cộng đồng',hitler['community']+1],['k-core',hitler['core']]],[290,185])
table(['Nguồn → đích','Quan hệ / năm'],[[nodes[e['source']]['name']+' → '+nodes[e['target']]['name'],e['relation']+' / '+str(e.get('year','?'))] for e in incident[:9]],[305,170])
p('Ứng dụng cho phép đổi số bước, lọc dấu, chọn node lân cận để chuyển hồ sơ và đọc URL nguồn. Mỗi bằng chứng văn bản hiển thị qua mục “Đọc bằng chứng”. Quan hệ tham dự một hiệp ước không được diễn giải thành chữ ký cá nhân hoặc một liên minh trực tiếp giữa mọi người tham dự.')
h('Khả năng truy vết tới Stalin')
stalin=next(n for n in data['nodes'] if n['name']=='Joseph Stalin')
path=g.path(hitler['id'],stalin['id'])
p('Snapshot '+('có đường đi '+str(len(path))+' bước trong giới hạn truy xuất.' if path is not None else 'chưa có đường đi tới Stalin trong 4 bước. Ứng dụng phải thông báo thiếu đường đi thay vì suy diễn.'))
if path:
 for i,e in enumerate(path):p(f"[{i+1}] {escape(nodes[e['source']]['name'])} — {e['relation']} — {escape(nodes[e['target']]['name'])}; năm {e.get('year','?')}.",'SmallVN')

page(11,'GraphRAG và suy luận nhiều bước')
p('Luồng xử lý: chọn node đầu và đích → BFS tối đa 4 cạnh → tạo context gồm cạnh, chiều, năm, dấu và nguồn → Qwen diễn giải → kiểm tra citation và đọc bằng chứng. Client hiển thị truy xuất cục bộ; server tự dựng lại context từ snapshot để tránh dùng dữ liệu tùy ý từ phía trình duyệt.')
d=Drawing(475,110)
for i,label in enumerate(['Thực thể','BFS / đường đi','Bằng chứng','Qwen 3B']):
 x=i*120;d.add(Rect(x,35,110,50,fillColor=colors.HexColor('#e7efeb'),strokeColor=LINE));d.add(String(x+55,56,label,textAnchor='middle',fontName='ArialBold',fontSize=9,fillColor=INK))
 if i<3:d.add(Line(x+110,60,x+120,60,strokeColor=INK))
story.append(d)
h('Giữ nghĩa của cạnh khi multi-hop')
p('BFS được phép đi ngược chiều để tìm liên hệ trong mạng, nhưng bằng chứng vẫn trình bày source và target gốc. Một đường A–B–C chỉ thể hiện chuỗi liên hệ. Nó không chứng minh A hỗ trợ C, không bảo đảm hai sự kiện đồng thời và không tự tạo quan hệ nhân quả.')
h('Giới hạn của truy xuất')
p('Hệ thống hiện ưu tiên một đường ngắn nhất giữa hai thực thể được chọn. Chưa xếp hạng nhiều đường, chưa xử lý đầy đủ phủ định lịch sử hoặc tự liên kết thực thể trong câu hỏi tự do. Có thể mở rộng bằng lọc thời gian, nhiều đường độc lập, truy xuất theo loại quan hệ và bộ reranker nhỏ.')
model_status=ROOT/'evaluation/model_run.json'
if model_status.exists():
 ms=json.loads(model_status.read_text(encoding='utf8'));p('Đã chạy Qwen 3B trên 1 đoạn phát triển, mất '+fmt(ms['elapsed_seconds'])+' giây. Mô hình đề xuất 4 quan hệ; sau khi bổ sung kiểm tra kiểu hai đầu, 0 đề xuất qua kiểm tra và 4 bị loại. Mô hình nhầm quốc gia với sự kiện và nhầm xâm lược thành hiệp ước. Bộ kiểm tra đã được sửa trên ví dụ phát triển này, không phải một phép đo chất lượng ngoài mẫu. Raw và bản kiểm tra lại được lưu trong evaluation/.','SmallVN')
else:p('Bản ghi chạy thực tế của mô hình, nếu có, được lưu trong evaluation/. Không coi việc tích hợp API là bằng chứng về chất lượng câu trả lời.','SmallVN')

page(12,'Stack, vận hành và phân công đề xuất')
table(['Thành phần','Vai trò'],[['Wikipedia + bộ thu thập Python','Corpus và nguồn có thể truy vết'],['Neo4j 5.x','Lưu trữ node và cạnh có dấu'],['Python + NetworkX 3.4.2','BFS, PageRank, Louvain, k-core và null model'],['HTML/CSS/JavaScript + SVG','Ứng dụng trực quan, không cần bước build'],['HTTP server thư viện chuẩn','Phục vụ giao diện, truy xuất và model bridge'],['Qwen 3B + llama.cpp / Ollama','Trích xuất cấu trúc và diễn giải có bằng chứng']],[215,260])
h('Chạy và tái lập')
p('python server.py mở ứng dụng tại 127.0.0.1:8765. python setup_model.py tải runtime/trọng số chính thức và kiểm tra checksum. Start-App.ps1 chạy mô hình ở loopback 18080. Trọng số không đóng trong ZIP hoặc Git. requirements.txt chỉ cần khi tính lại phân tích NetworkX; kết quả tính sẵn xem được bằng thư viện chuẩn.')
p('Bản Sites phục vụ giao diện và snapshot tĩnh. Các thao tác trích xuất, sinh câu trả lời cần server cục bộ. Dữ liệu nghiên cứu không tự gửi tới một dịch vụ mô hình bên ngoài.')
h('Phân công đề xuất để nhóm xác nhận')
table(['Sinh viên','Phần phụ trách đề xuất'],[['Dương Thanh Bình','Thu thập corpus, Neo4j, ontology, kiểm tra nguồn và dữ liệu'],['Nguyễn Hải Dương','SNA, ứng dụng profiling, GraphRAG, kiểm thử và báo cáo'],['Cả hai','Gán nhãn độc lập, giải quyết bất đồng, kiểm tra kết quả và thuyết trình']],[165,310])
p('Đây là đề xuất tổ chức công việc, không phải xác nhận hai sinh viên đã thực hiện các bước gán nhãn hoặc kiểm chứng độc lập.','SmallVN')

page(13,'Kết luận, hạn chế và tài liệu tham khảo')
p('Ứng dụng đã kết hợp một snapshot Neo4j có dấu với hồ sơ thực thể, nguồn từng cạnh, khoảng cách chính xác, hai phiên bản PageRank, cộng đồng, k-core và truy xuất nhiều bước. Pipeline làm giàu có lưu raw, kiểm tra cấu trúc và quote, bảo toàn nguồn để duyệt trước khi nhập.')
p('Những điểm chưa đạt kết luận cuối cùng: chưa có tập gold NLP đầy đủ do hai người gán nhãn độc lập; chưa chứng minh độ chính xác toàn mạng vượt 90%; corpus còn lệch về bầu cử ở ba nước; lớp ngoại giao nhỏ; đối chứng giữ bậc chưa cho bằng chứng mạnh về thế giới nhỏ; chất lượng suy luận ngôn ngữ cần đánh giá riêng.')
p('Ưu tiên tiếp theo là bổ sung các đoạn chính sách đối ngoại thuộc Đức, Liên Xô, Nhật, Trung Quốc và Ý; gán nhãn tập giữ riêng; đánh giá các quan hệ hiếm; đo liên kết thực thể và RAG; mở rộng null model để kiểm tra độ ổn định. Không thêm cạnh chỉ để đạt số lượng.')
h('Tài liệu và mã nguồn')
sources=[('Kho mã đồ án nền','https://github.com/binhdayne/MXH'),('Qwen2.5-3B-Instruct model card','https://huggingface.co/Qwen/Qwen2.5-3B-Instruct'),('GGUF của Qwen chính thức','https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF'),('llama.cpp','https://github.com/ggml-org/llama.cpp'),('NetworkX algorithms','https://networkx.org/documentation/stable/reference/algorithms/index.html'),('Wikipedia: Adolf Hitler','https://en.wikipedia.org/wiki/Adolf_Hitler'),('Ghi công Wikipedia','https://en.wikipedia.org/wiki/Wikipedia:Copyrights')]
for title,url in sources:p(f'<b>{escape(title)}</b><br/><link href="{url}" color="#1e5c47">{escape(url)}</link>','SmallVN')
p('Nguồn chi tiết cho mỗi cạnh nằm trong graph.json. Phiên bản bài và hash nằm trong corpus/paragraphs.jsonl, evaluation/sources.json. Mã nguồn ứng dụng và bộ dữ liệu đi kèm gói bàn giao.','SmallVN')

OUT.parent.mkdir(parents=True,exist_ok=True)
SimpleDocTemplate(str(OUT),pagesize=(595.276,841.89),leftMargin=60,rightMargin=60,topMargin=48,bottomMargin=62,title='Entity Atlas - Báo cáo cuối kỳ',author='Dương Thanh Bình; Nguyễn Hải Dương').build(story,onFirstPage=footer,onLaterPages=footer)
print(OUT)
