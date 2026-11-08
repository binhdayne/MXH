# Mạng chính trị thời Thế chiến II

Phạm vi 1939–1945. Lớp ngoại giao nối các nhân vật, chính phủ và sự kiện tại châu Âu, châu Á và Bắc Mỹ. Lớp bầu cử bổ sung ứng viên và đảng từ Mỹ, Anh và Úc trong thời chiến. Danh sách ứng viên mở rộng bối cảnh chính trị và không phải một bảng xếp hạng ảnh hưởng.

## Chạy lại

Cần Python 3.10 trở lên, lxml và Neo4j Community 5.26. Chạy từ thư mục wwii.

```sh
python -m pip install -r requirements.txt
python build_wwii.py
python audit_wwii.py
python load_wwii.py --http http://127.0.0.1:17474 --database neo4j
```

Trình tải dùng Neo4j HTTP transactional endpoint trên máy cục bộ. Nếu dùng cổng mặc định của Neo4j, đặt `--http http://127.0.0.1:7474`. Trình tải dùng nhãn `WWII`, hợp nhất lại theo khóa và tải lớp ngoại giao từ `diplomacy_seed.cypher`. Mọi thao tác ghi nằm trong một giao dịch. Bản chạy này dùng kết nối cục bộ đã cấu hình sẵn.

`build_wwii.py` cố định revision Wikipedia cho các bảng và đoạn văn. Dùng `--cache` để chạy với bản HTML ngoại tuyến. Các tệp cache có thể có HTML khác nhau khi Wikipedia đổi trình kết xuất, vì vậy bản kê ghi cả SHA-256. `data/nodes.csv` và `data/edges.csv` chứa đầu ra tự động. Thống kê cuối của Neo4j gồm cả dữ liệu từ tệp hạt giống.

## Xem trong Neo4j Browser

```cypher
MATCH (a:WWII)-[r]->(b:WWII)
WHERE r.method IN ['nlp', 'manual']
RETURN a, r, b
```

Cạnh dương thể hiện liên kết, ủng hộ hoặc hợp tác cụ thể. Cạnh âm thể hiện đối lập, cạnh tranh hoặc rời đảng. Các cạnh bối cảnh như dự hội nghị chỉ mô tả sự kiện và để trống dấu. Quan hệ chuyển đảng có chung thuộc tính event. Từng cạnh mang nguồn wiki_url và mốc thời gian. Cạnh đối xứng được lưu một lần.

## Kiểm định

`data/audit_checked.csv` là mẫu phân tầng, gồm 100 cạnh đề cử, 100 cạnh tranh cử và các cạnh NLP. Mẫu bảng được đối chiếu bằng một lượt đọc lại HTML theo vị trí nguồn. Cạnh NLP được kiểm tra vị trí bằng chứng và rà soát trên các tài liệu đã dùng xây luật. Kết quả đối chiếu bảng không phải phép đo precision NLP ngoài mẫu. Xem `data/audit_stats.json` và báo cáo để biết giới hạn của phép đo.

Mỗi trang Wikipedia được dẫn bằng URL phiên bản trong `data/sources.json`. Lịch sử từng trang ghi tác giả. Xem [điều khoản Wikimedia](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use).
