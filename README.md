# Mạng quan hệ chính trị Vương quốc Anh

Đồ thị có dấu từ Wikipedia tiếng Anh, giai đoạn 2010–2024. Bộ dữ liệu có 3.326 nút, 10.380 cạnh và 10 loại cạnh. Lõi dữ liệu gồm các cột đảng có tên riêng trong bảng ứng viên bầu cử Hạ viện 2024. Tám cạnh bổ sung được trích bằng luật văn bản theo mục và phiên bản.

## Tái lập

Cần Python 3.10+ và lxml. Với Neo4j Community 5.26, cần Java 21 hoặc bản Java mà Neo4j hỗ trợ.

```bash
python -m pip install -r requirements.txt
python build_graph.py
python audit_table.py
python neo4j_csv.py data import
```

Tải HTML theo revision qua MediaWiki REST API. Khi chạy ngoại tuyến, dùng `--cache` trỏ tới thư mục `cache` trong gói bàn giao. Mỗi tệp nguồn được kiểm tra revision. CSV dùng UTF-8. `data/sources.json` ghi URL cố định và SHA-256 của bản HTML đã dùng. Xem [điều khoản Wikimedia](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use) và ghi công qua lịch sử của từng trang khi tái sử dụng nội dung nguồn.

## Neo4j

Trong một cài đặt Neo4j riêng và đang dừng, nhập vào database mới. Điền đường dẫn tuyệt đối tới hai CSV do `neo4j_csv.py` tạo. Trên Windows dùng các lệnh có hậu tố `.bat` nếu thư mục `bin` có trên PATH.

```bash
neo4j-admin database import full neo4j --nodes=/path/to/import/nodes.neo.csv --relationships=/path/to/import/edges.neo.csv
neo4j console
cypher-shell -d neo4j -f verify.cypher
```

Hoặc giải nén tệp `neo4j.dump` đi kèm vào database mới bằng `neo4j-admin database load neo4j --from-path=/path/to/dump-directory` khi Neo4j dừng. Có thể mở Neo4j Browser và dán các truy vấn trong `verify.cypher`.

## Dữ liệu và kiểm định

- `data/nodes.csv` lưu định danh, loại, tên, tiêu đề wiki và khu vực nếu có.
- `data/edges.csv` lưu đầu mút, loại cạnh, nhóm, dấu, chiều, ngày, sự kiện và bằng chứng.
- `data/stats.json` lưu thống kê đồ thị, thành phần liên thông yếu và bậc theo dấu.
- `data/audit_sample.csv` là phiếu chấm với mẫu 150 cạnh bảng và toàn bộ 8 cạnh NLP.
- `data/audit_table_checked.csv` lưu kiểm tra tự động đối chiếu bảng nguồn, 150/150 khớp.
- `data/audit_nlp_review.csv` ghi đối chiếu ngữ nghĩa từng cạnh NLP trên chính các trang thiết kế luật. Đây là kiểm tra nội bộ. Chưa có tập văn bản ngoài mẫu hoặc lượt chấm mù độc lập.

Các loại cạnh đối xứng được lưu một lần và truy vấn theo cả hai hướng. `LEAVES_PARTY` và `JOINS_PARTY_AFTER_SWITCH` dùng cùng mã sự kiện. Các cột `Others` và `Incumbent` nằm ngoài phạm vi trích xuất bảng. Dấu âm trong cuộc bầu cử biểu thị cạnh tranh trực tiếp tại một ghế.
