# Mô hình dữ liệu

Xem [README của dự án](../README.md) để nạp dữ liệu, chạy lại pipeline và mở đồ thị trong Neo4j Browser.

## Nút và cạnh

| Nhãn nút | Đại diện cho |
| --- | --- |
| `WartimePolitician` | Chính khách, đại diện hoặc ứng viên được ghi tên trong nguồn. |
| `WartimeParty` | Đảng hoặc tổ chức tranh cử. |
| `WartimeGovernment` | Chính phủ hoặc nhà nước theo bối cảnh lịch sử. |
| `WartimeEvent` | Hội nghị, hiệp ước hoặc sự kiện ngoại giao. |

Tất cả nút dự án có thêm nhãn `WWII`. Với cạnh có chiều, `source` và `target` lần lượt là điểm đầu và điểm cuối. Cạnh đối xứng lưu một lần và có `symmetric=True`. Năm và sự kiện là thuộc tính của cạnh. Khi có thể, trình trích xuất lưu vị trí nguồn và đoạn bằng chứng để đối chiếu.

## Các tệp trong data

| Tệp | Nội dung |
| --- | --- |
| `nodes.csv`, `edges.csv` | Nút và cạnh từ bảng bầu cử và luật văn bản. |
| `sources.json` | Tiêu đề, URL phiên bản và SHA-256 của HTML dùng để trích xuất. |
| `audit_sample.csv`, `audit_checked.csv` | Mẫu phân tầng và kết quả đối chiếu theo cạnh. |
| `audit_stats.json` | Số cạnh bảng khớp nguồn và cận dưới Wilson 95% theo từng tầng. |
| `stats.json`, `neo4j_stats.json` | Thống kê đầu ra tự động và thống kê sau khi nạp cả lớp ngoại giao thủ công. |

Các cạnh ngoại giao thủ công lưu trong [diplomacy_seed.cypher](diplomacy_seed.cypher) và mang URL Wikipedia. Khi nạp lại, chương trình hợp nhất theo khóa. Số liệu bầu cử phản ánh những khu vực đọc được từ corpus. Lịch sử phiên bản Wikipedia ghi công tác giả. [Điều khoản Wikimedia](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use)
