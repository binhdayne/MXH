# Entity Atlas · Chân dung thực thể trên đồ thị Thế chiến II

Ứng dụng phân tích chính khách, đảng, chính phủ và sự kiện trong corpus Wikipedia về giai đoạn 1939–1945. Snapshot được xuất từ nhãn `WWII` trong Neo4j. Các ứng viên bầu cử được giữ theo nguồn. Vị trí trong đồ thị không thể thay thế đánh giá ảnh hưởng lịch sử.

**Sinh viên:** Dương Thanh Bình — 23020516; Nguyễn Hải Dương — 23020523.

## Chạy ngay

Cần Python 3.10+. Giao diện và dữ liệu đã tính sẵn dùng thư viện chuẩn, không cần Neo4j hoặc mô hình để xem.

```powershell
python server.py
```

Mở http://127.0.0.1:8765. Tìm tên hoặc bấm một nút để xem hồ sơ. Lọc 1–3 bước và dấu quan hệ; chọn giới hạn 90, 180 hoặc 350 nút cho mạng lân cận. Các số liệu chính xác nằm trong `analysis.json`.

## Khám phá đồ thị

- **Mạng quan hệ:** bố trí bằng lực đẩy và chống va chạm giữa các nút. Nhãn tự chọn vị trí đủ chỗ; rê chuột lên nút để đọc tên đầy đủ. Rê chuột lên đường nối để xem loại quan hệ (tiếng Việt và mã cạnh), hai đầu mút, chiều, năm và dấu. Nếu nhiều bản ghi cùng nối hai nút, tooltip liệt kê tối đa ba bản ghi và thông báo số còn lại. Kéo một nút để tách vị trí, kéo nền để di chuyển, cuộn chuột hoặc dùng nút +/− để phóng to, thu nhỏ.
- **Toàn cảnh mạng:** mặc định hiển thị đủ 2.750 nút và 6.643 cạnh, gồm cả nút cô lập. Có thể lọc loại thực thể, cộng đồng, loại quan hệ, dấu và năm; số nút/cạnh đang hiển thị luôn được cập nhật. Khi lọc quan hệ hoặc năm, chỉ giữ các nút tham gia cạnh phù hợp.
- Tìm tên trong toàn cảnh để đưa nút vào giữa màn hình. Nếu nút nằm ngoài bộ lọc, ứng dụng xóa bộ lọc để hiển thị nút đó. Bấm nút để xem chỉ số và láng giềng; bấm **Mở hồ sơ** hoặc bấm đúp nút để mở hồ sơ chi tiết. Bấm cạnh để đọc quan hệ và nguồn.
- **Vừa khung** đưa mạng vào khung nhìn; **Bố trí lại** khôi phục bố cục; **Mở rộng** mở khung lớn, Escape để thu gọn. Khi canvas được chọn, dùng +/−, các phím mũi tên và phím 0 để điều khiển.

Giao diện dùng Canvas và [D3 7.9.0](https://d3js.org/d3-force) được lưu trong `dist/vendor/`, không phụ thuộc CDN khi chạy. Bố cục toàn mạng được tính sẵn theo các cộng đồng để tránh chạy mô phỏng lớn khi mở trang; vị trí và khoảng cách trên hình chỉ phục vụ hiển thị, không thay đổi cạnh hay các chỉ số phân tích.

Sau khi xuất lại `dist/graph.json`, cần Node.js 18+ để tạo lại bố cục khớp snapshot và chạy kiểm thử:

```powershell
node build_layout.cjs
node --test test_network.cjs test_qa.cjs
```

`dist/layout.json` chứa tọa độ, ID và SHA-256 của graph gốc. Kiểm thử kiểm tra toàn bộ nút/cạnh, tính nhất quán của bộ lọc, bố cục, nhãn và các câu hỏi GraphRAG hiện có.

## Triển khai theo đề cuối kỳ

| Yêu cầu | Triển khai | Bằng chứng / giới hạn |
| --- | --- | --- |
| Corpus làm giàu | 24 đoạn từ 4 bài Wikipedia, URL phiên bản và SHA-256 | Tách theo bài trong corpus/paragraphs.jsonl |
| Nhận dạng thực thể | Qwen trích Person, Party, Government, Event | JSON có cấu trúc; đối chiếu ID trước khi liên kết |
| Nhận dạng cạnh | Ontology có dấu, năm và đoạn trích | Kiểm tra quote, endpoint, loại, dấu và năm |
| Đánh giá | Audit bảng, công cụ precision/recall/F1 NER và RE | 200/200 chỉ thuộc hai loại cạnh bảng |
| Thế giới nhỏ | Khoảng cách chính xác, ER và đối chứng bảo toàn bậc | Chưa đủ bằng chứng kết luận chắc chắn |
| PageRank | α=0,85, toàn mạng và chỉ cạnh dương | Đồ thị đơn vô hướng, không dùng trọng số âm |
| Cộng đồng / hạt nhân | Louvain seed 1945, modularity, k-core | Hạt nhân theo PageRank trong cộng đồng |
| SLM ≤9B | Qwen2.5-3B-Instruct, 3,09B, Q4_K_M | llama.cpp CPU hoặc Ollama |
| GraphRAG, multi-hop | BFS tối đa 4 bước → bằng chứng cạnh → Qwen diễn giải | Giữ chiều, nguồn và năm |
| Hồ sơ node | Chỉ số, đồ thị, thời gian, nguồn, JSON | Không tự bổ sung tiểu sử không có nguồn |

## Qwen 3B trên Windows x64

Tải khoảng 2,13 GB từ các kho chính thức; kiểm tra SHA-256 của runtime và trọng số. Không cài toàn cục.

```powershell
python setup_model.py
.\Start-App.ps1
```

Nếu PowerShell không cho chạy script, dùng hai terminal với các lệnh sau, không cần đổi chính sách hệ thống.

```powershell
.\runtime\bin\llama-server.exe -m .\runtime\qwen2.5-3b-instruct-q4_k_m.gguf --host 127.0.0.1 --port 18080 -c 4096 -t 4 --jinja
```

```powershell
$env:ATLAS_LLM_BACKEND = 'llama'
python server.py
```

Có thể thay bằng Ollama:

```powershell
ollama pull qwen2.5:3b
$env:ATLAS_LLM_BACKEND = 'ollama'
python server.py
```

Bản Sites phục vụ giao diện và snapshot tĩnh. Trích xuất và sinh câu trả lời Qwen dùng bản cục bộ qua server.py. Trọng số không đưa lên Git hoặc ZIP. `Start-App.ps1 -RuntimeDirectory 'đường dẫn runtime'` cho phép dùng lại trọng số đã tải. Log ở `.logs/`.

## Pipeline chạy lại

```powershell
python -m pip install -r requirements.txt
python collect_corpus.py
python enrich_batch.py --split development --limit 3
python enrich_batch.py --split held_out --limit 3
python -m unittest test_graph.py
```

Kết quả batch lưu raw của mô hình, đề xuất qua kiểm tra, đề xuất bị loại và thời gian. Không tự ghi đề xuất vào Neo4j. `apply_reviewed.py` chỉ nhận tệp có người duyệt, ID hai đầu và bằng chứng. Sau khi nạp chạy `python export_graph.py`, rồi `python analyze.py`. Endpoint mặc định HTTP 127.0.0.1:17474, database neo4j, theo cấu hình cục bộ đã có của đồ án. Instance khác cần cấu hình endpoint và xác thực tương ứng.

## Định nghĩa chỉ số

- Đồ thị đơn vô hướng không trọng số gộp cạnh song song, bỏ self-loop để phân tích cấu trúc. Snapshot giữ đầy đủ dấu và chiều gốc.
- PageRank dùng power iteration, teleportation đều, phân phối lại dangling, α=0,85 và tolerance 10⁻¹². Nhánh cạnh dương vẫn giữ mọi nút.
- BFS từ mọi nút tính khoảng cách chính xác. Mạng rời nhau nên báo riêng LCC, các cặp đến được và tỷ lệ cặp đến được.
- ER gồm 3 G(n,m), seed 41–43; khoảng cách trên LCC của từng mẫu. Đối chứng bảo toàn bậc dùng LCC gốc, giữ liên thông, seed 1941–1943, đề nghị 5m swaps, lưu số thành công. Đây là đối chiếu thăm dò, chưa là kiểm định ý nghĩa thống kê.
- Louvain seed 1945. Hạt nhân là nút PageRank cao nhất của cộng đồng. k-core mô tả lõi cấu trúc, không phải điểm ảnh hưởng chính trị.

## GraphRAG và tính kiểm chứng

### Hỏi đáp ngay trên web

Nút **Trả lời từ đồ thị** xử lý trực tiếp snapshot trong trình duyệt, hoạt động trên cả Sites và localhost. Có thể nhập câu hỏi có dấu hoặc không dấu, nhấn Enter hoặc chọn câu hỏi mẫu. Shift+Enter để xuống dòng.

- “Hitler tuyên chiến với ai năm 1941?” lọc đúng loại cạnh, chiều và năm.
- “Hitler và Stalin có mối liên hệ gì?” truy xuất tối đa bốn bước, giữ chiều gốc và nguồn.
- “PageRank của Hitler là bao nhiêu?”, “Hitler thuộc cộng đồng nào?” đọc chỉ số đã tính.
- “Dòng thời gian của Hitler năm 1941” lọc bằng chứng theo năm.

Có thể hỏi ngắn như “Stalin với Soviet”, “Germany với Soviet năm 1941” hoặc “Quan hệ của Hiter là Germany”. Trong phạm vi corpus Thế chiến II, Germany được liên kết với Nazi Germany; Soviet/USSR với Soviet Union; Hiter/Hitller với Adolf Hitler. Chương trình chỉ dùng những biến thể tên đã khai báo, không tự đoán mọi lỗi chính tả.

Kết quả phân biệt cạnh trực tiếp với đường liên hệ gián tiếp. Khi có nhiều bản ghi trực tiếp giữa cùng cặp nút, hiển thị các loại quan hệ và năm khác nhau (tối đa 20). Đã bổ sung cạnh Hitler → LED_GOVERNMENT → Nazi Germany từ Wikipedia (infobox nhiệm kỳ Thủ tướng 1933–1945), lưu bằng chứng trong evaluation/leadership_additions.json. Cạnh có start_year/end_year và ngày bắt đầu/kết thúc; year=1939 chỉ là mốc đầu phạm vi nghiên cứu. Bộ lọc năm xét cả nhiệm kỳ. Nguồn được trợ lý kiểm tra; vẫn chờ hai sinh viên kiểm chứng độc lập.

Đây là hỏi đáp theo các mẫu truy vấn có kiểm soát trên graph, không phải mô hình sinh ngôn ngữ trên cloud. Các câu chưa hỗ trợ, tên trùng và đường đi thiếu bằng chứng được thông báo rõ. Nhập tên hai thực thể trực tiếp trong câu hỏi, ví dụ “Hitler và Stalin có mối liên hệ gì?”. Có thể hỏi “Quan hệ với Stalin” để dùng thực thể hồ sơ đang mở làm đầu còn lại. Câu hỏi trống sẽ yêu cầu nhập nội dung.


Nút **Diễn giải với Qwen** chỉ hiện trên localhost sau khi có kết quả đường đi. Bản web không hiển thị nút gọi dịch vụ cục bộ không thể truy cập. Kiểm thử hỏi đáp: `node --test test_qa.cjs` (Node.js 18+).

Client truy xuất đường ngắn nhất tối đa 4 cạnh. Server tự truy xuất lại bằng ID trong snapshot, không tin context client gửi. Cạnh giữ chiều gốc ngay cả khi BFS đi ngược. Qwen nhận bằng chứng truy xuất; server kiểm tra số citation có thuộc context. Kiểm tra số citation không bảo đảm đúng ngữ nghĩa. Khi không có đường đi, server từ chối trả lời dựa trên graph.

Đây là GraphRAG theo đường đi trên đồ thị tri thức cục bộ, không phải toàn bộ pipeline Microsoft GraphRAG. Hai đầu của đường liên hệ được xác định từ các tên nhận diện trong câu hỏi.

## Đánh giá trung thực

Audit đã có gồm 100 NOMINATES_CANDIDATE và 100 ELECTORAL_RIVAL. Mỗi loại khớp nguồn 100/100, cận dưới Wilson 95% khoảng 96,3%. Kết quả này chưa chứng minh NLP hay toàn đồ thị vượt 90%, và chưa đo recall của trình thu thập.

Hai sinh viên cần gán nhãn độc lập tập bài giữ riêng theo `evaluation/annotation_guidelines.md`, giải quyết bất đồng rồi lưu gold. Không đặt annotated=true khi chưa gán nhãn. Chạy:

```powershell
python evaluate.py --gold evaluation/gold.jsonl --pred evaluation/qwen_held_out.jsonl
```

Công cụ chấm raw, exact match tên/type thực thể và source/target/type/sign/year. Tập nhỏ chỉ đủ thăm dò. RAG cần chấm thêm faithfulness, đầy đủ bằng chứng, từ chối đúng và trích dẫn hỗ trợ từng nhận định.

## Cấu trúc

`dist/`: giao diện và snapshot. `graph_core.py`: truy xuất và validation. `server.py`: HTTP/API model bridge. `analyze.py`: SNA. `collect_corpus.py`, `enrich_batch.py`, `evaluate.py`: corpus và đánh giá. `apply_reviewed.py`, `export_graph.py`: Neo4j. `test_graph.py`: kiểm tra giới hạn bước, đường đi ngược, thành phần rời và kiểm định bằng chứng.

## Nguồn

- Đồ án nền: https://github.com/binhdayne/MXH
- Model card: https://huggingface.co/Qwen/Qwen2.5-3B-Instruct
- Trọng số: https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF
- Runtime: https://github.com/ggml-org/llama.cpp
- Thuật toán: https://networkx.org/documentation/stable/reference/algorithms/index.html
- Ghi công Wikipedia: `NOTICE.md`, URL phiên bản trên bản ghi và `evaluation/sources.json`.
