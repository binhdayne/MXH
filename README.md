# Mạng chính trị thời Thế chiến II · Entity Atlas

Đồ án Phân tích mạng xã hội từ Wikipedia tiếng Anh về chính khách, đảng phái, chính phủ và sự kiện liên quan giai đoạn 1939–1945.

| Sinh viên | MSSV |
| --- | --- |
| Dương Thanh Bình | 23020516 |
| Nguyễn Hải Dương | 23020523 |

## Ứng dụng chân dung thực thể

[Mở Entity Atlas](https://wwii-entity-atlas.brightgrass5.chatgpt.site) · [Hướng dẫn đầy đủ](entity-atlas/README.md) · [Báo cáo PDF 13 trang](reports/Bao-cao-Entity-Atlas-The-chien-II.pdf)

Snapshot bàn giao có **2.750 nút, 6.642 cạnh và 17 loại quan hệ**. Ứng dụng gồm tìm kiếm, đồ thị có dấu 1–3 bước, nguồn từng cạnh, thời gian, PageRank, cộng đồng, k-core, xuất JSON và GraphRAG theo đường đi tối đa 4 bước.

```powershell
cd entity-atlas
python server.py
```

Mở http://127.0.0.1:8765. Phần xem và truy xuất dùng thư viện chuẩn Python, chạy từ snapshot có sẵn; không cần Neo4j đang chạy. Bản Sites là giao diện và dữ liệu tĩnh; Qwen chạy ở bản cục bộ.

```powershell
python setup_model.py
.\Start-App.ps1
```

Qwen2.5-3B-Instruct có 3,09 tỷ tham số, dùng GGUF Q4_K_M / llama.cpp CPU hoặc Ollama. Tải khoảng 2,13 GB, có kiểm tra SHA-256. Trọng số không lưu trong repo. CPU có thể cần vài phút cho một đoạn.

## Kết quả và giới hạn

| Chỉ số snapshot | Giá trị |
| --- | ---: |
| Thành phần liên thông | 14 |
| Thành phần lớn nhất | 1.966 nút |
| Khoảng cách trung bình LCC | 2,856 |
| Cộng đồng Louvain, seed 1945 | 59 |
| Modularity | 0,723 |
| σ so đối chứng bảo toàn bậc | 1,035 |

[Số liệu đầy đủ](entity-atlas/analysis.json). Mạng rời nhau nên không báo khoảng cách trung bình hữu hạn trên mọi cặp. Kết quả so ER rất khác so đối chứng giữ bậc; chưa đủ bằng chứng mạnh để kết luận thế giới nhỏ. Các thuật toán cấu trúc dùng phép chiếu đơn vô hướng; PageRank cạnh dương được tính riêng.

Audit 200/200 chỉ thuộc hai loại cạnh bảng, không chứng minh NLP hay toàn mạng vượt 90%. Đã chạy Qwen trên một đoạn phát triển và phát hiện lỗi kiểu thực thể, loại quan hệ. Kiểm tra mới loại 4/4 đề xuất của ca này; không coi đó là điểm ngoài mẫu. Kết quả RAG có mã citation hợp lệ vẫn có thể sai ngữ nghĩa. Các bản sinh có lỗi đã phát hiện được thay bằng bằng chứng truy xuất, giữ raw để đánh giá.

Tập gold do hai sinh viên gán nhãn độc lập chưa hoàn tất. Xem [quy trình đánh giá](entity-atlas/evaluation/annotation_guidelines.md). Hai cạnh văn bản mới đã được trợ lý đối chiếu nguồn, được đánh dấu chờ sinh viên kiểm chứng độc lập. Vị trí PageRank phản ánh corpus, không thay thế đánh giá ảnh hưởng lịch sử.

## Nạp lại vào Neo4j

```powershell
cd wwii
python -m pip install -r requirements.txt
python load_wwii.py --http http://127.0.0.1:17474 --database neo4j
```

Loader nạp CSV, lớp ngoại giao và hai cạnh làm giàu trong entity_atlas_enrichment.cypher bằng MERGE. Nếu dùng cổng mặc định, đổi HTTP thành http://127.0.0.1:7474. Khi cần xác thực, đặt NEO4J_PASSWORD và NEO4J_USERNAME trong môi trường.

```cypher
MATCH p = (h:WWII:WartimePolitician {name:'Adolf Hitler'})-[*1..3]-(n:WWII)
WHERE all(x IN nodes(p) WHERE x:WWII)
RETURN p
```

## Tái lập và kiểm thử

Trong entity-atlas, chạy `python -m unittest test_graph.py` và `python verify_snapshot.py`. Muốn tính lại SNA, cài requirements.txt rồi chạy `python analyze.py --recompute`. Thứ tự node/cạnh được cố định trước thuật toán có seed. Cache null model chỉ dùng lại khi hash của LCC, phiên bản phép đo và NetworkX trùng khớp.

Trong wwii, chạy `python build_wwii.py --cache cache --output rebuilt`, rồi `python audit_wwii.py --cache cache --data rebuilt`. Phiên bản Wikipedia và SHA-256 được lưu để đối chiếu. Xem [danh sách nguồn](wwii/data/sources.json).

## Mã nguồn

- entity-atlas: giao diện, snapshot, SNA, corpus, SLM, GraphRAG và đánh giá.
- wwii: pipeline bảng/luật, nạp Neo4j, nguồn và audit nền.
- reports: báo cáo bàn giao.

Văn bản Wikipedia giữ ghi công và điều kiện sử dụng theo [NOTICE](entity-atlas/NOTICE.md). Mỗi cạnh giữ URL nguồn; các giới hạn và định nghĩa chỉ số nằm trong README ứng dụng và báo cáo.
