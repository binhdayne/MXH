# Mạng chính trị thời Thế chiến II

Đồ án Phân tích mạng xã hội xây dựng đồ thị có dấu về chính khách, đảng phái, chính phủ và sự kiện trong giai đoạn 1939–1945. Dữ liệu đến từ Wikipedia tiếng Anh, gồm kết quả bầu cử ở Mỹ, Anh và Úc cùng các bài về ngoại giao và chính trị thời chiến. Kết quả bầu cử cung cấp các cạnh đề cử và tranh cử. Các bài viết cung cấp bằng chứng về hợp tác, đối lập và chuyển đảng.

| Sinh viên | MSSV |
| --- | --- |
| Dương Thanh Bình | 23020516 |
| Nguyễn Hải Dương | 23020523 |

| Chỉ số | Số lượng |
| --- | ---: |
| Nút trong Neo4j | 2.750 |
| Quan hệ trong Neo4j | 6.640 |
| Loại quan hệ | 16 |
| Loại quan hệ có dấu | 13 |

Số liệu gồm 6.584 cạnh từ bảng bầu cử, 10 cạnh từ luật văn bản và 46 cạnh ngoại giao đã đối chiếu thủ công. [Thống kê Neo4j](wwii/data/neo4j_stats.json)

## Nạp và xem đồ thị

Cài Python 3.10 trở lên và khởi động Neo4j Community 5.26. Repo có sẵn CSV, nên có thể nạp trực tiếp mà chưa cần tải lại Wikipedia. Chạy các lệnh sau từ thư mục gốc của repo.

```sh
cd wwii
python -m pip install -r requirements.txt
python load_wwii.py --http http://127.0.0.1:7474 --database neo4j
```

`--http` dùng cổng HTTP của Neo4j. Bỏ tùy chọn này nếu máy đang chạy cấu hình của đồ án ở cổng `17474`. Nếu Neo4j yêu cầu đăng nhập, đặt `NEO4J_PASSWORD` trong môi trường và đặt `NEO4J_USERNAME` nếu tên người dùng khác `neo4j`.

Mở Neo4j Browser, chọn cơ sở dữ liệu vừa nạp và chạy truy vấn sau để xem lớp ngoại giao.

```cypher
MATCH (a:WWII)-[r]->(b:WWII)
WHERE r.method IN ['nlp', 'manual']
RETURN a, r, b
```

Để xem các quan hệ trong phạm vi tối đa ba bước quanh Adolf Hitler, chạy truy vấn sau.

```cypher
MATCH p = (h:WWII:WartimePolitician {name: 'Adolf Hitler'})-[*1..3]-(n:WWII)
WHERE all(x IN nodes(p) WHERE x:WWII)
RETURN p
```

Trong chế độ **Graph**, chọn một cạnh để xem kiểu quan hệ, thời gian, dấu và nguồn `wiki_url`. [Các truy vấn kiểm tra](wwii/verify.cypher)

## Tái tạo dữ liệu từ Wikipedia

Chạy trong thư mục `wwii/`. Script dựng đồ thị tải HTML theo phiên bản đã cố định và lưu trong `cache/`. Có thể dùng một thư mục đầu ra khác để đối chiếu với CSV trong repo.

```sh
python build_wwii.py --cache cache --output rebuilt
python audit_wwii.py --cache cache --data rebuilt
```

Dùng HTML trong gói bàn giao để chạy ngoại tuyến và đối chiếu đúng các bản đã dùng. Wikipedia có thể kết xuất HTML khác cho cùng một phiên bản, nên bản kê nguồn lưu cả URL cố định và SHA-256. [Danh sách nguồn](wwii/data/sources.json)

## Cấu trúc mã nguồn

| Thành phần | Vai trò |
| --- | --- |
| [wikipedia_sources.py](wwii/wikipedia_sources.py) | Tải phiên bản Wikipedia và đọc bảng bầu cử theo định dạng từng nước. |
| [build_wwii.py](wwii/build_wwii.py) | Định danh thực thể, áp dụng luật văn bản và sinh CSV cùng mẫu kiểm định. |
| [audit_wwii.py](wwii/audit_wwii.py) | Đối chiếu cạnh mẫu với HTML và ghi kết quả. |
| [load_wwii.py](wwii/load_wwii.py) | Kiểm tra ID và đầu mút trước khi nạp, rồi tính thống kê từ Neo4j. |
| [diplomacy_seed.cypher](wwii/diplomacy_seed.cypher) | Nạp các sự kiện và quan hệ ngoại giao đã đối chiếu thủ công. |
| [data/](wwii/data) | CSV nút và cạnh tự động, bản kê nguồn, mẫu kiểm định và thống kê. |

Dấu `+1` thể hiện quan hệ hỗ trợ hoặc liên kết. Dấu `-1` thể hiện đối lập, cạnh tranh hoặc rời đảng. Các cạnh bối cảnh như tham dự hội nghị để trống dấu. Hai cạnh của một lần chuyển đảng dùng chung mã sự kiện. [Mô hình và các tệp dữ liệu](wwii/README.md)

## Kết quả kiểm định

Cả 100 cạnh đề cử và 100 cạnh tranh cử trong mẫu đều khớp với bảng Wikipedia. Mười cạnh trích theo luật văn bản đều truy được đoạn bằng chứng trong các bài dùng để xây luật. Độ chính xác NLP trên văn bản ngoài mẫu chưa được đo. [Mẫu đã đối chiếu](wwii/data/audit_checked.csv) · [Thống kê kiểm định](wwii/data/audit_stats.json)
