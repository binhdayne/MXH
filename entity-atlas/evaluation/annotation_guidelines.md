# Quy trình gán nhãn và đánh giá

1. Giữ tách biệt bài của Stalin và Roosevelt với bài Hitler và Churchill dùng phát triển pipeline. Không chỉnh prompt dựa trên nhãn đánh giá rồi tiếp tục gọi đó là tập giữ riêng.
2. Hai sinh viên đọc độc lập từng đoạn, gán toàn bộ thực thể Person, Party, Government, Event và toàn bộ cạnh được nói rõ. Giữ một bản nhãn riêng cho mỗi người rồi giải quyết bất đồng. Không gán nhãn từ kết quả mô hình.
3. Chỉ nhận quan hệ thuộc ontology graph_core.RELATIONS. Co-occurrence hoặc cùng phe không đủ chứng minh hỗ trợ. Giữ chiều, dấu và năm. Nếu không có năm rõ, dùng null; ghi riêng phạm vi thời gian ngoài 1939–1945.
4. Chuẩn hóa tên theo tên đầy đủ xuất hiện trong đoạn. Lưu alias và quyết định liên kết riêng. Tên đảng giống nhau ở hai nước không được hợp nhất chỉ từ chuỗi tên.
5. Điền entities, relations vào gold_template.jsonl, đặt annotated=true sau khi hoàn tất. Ghi reviewer và adjudicator đúng người thực hiện. Chưa gán nhãn thì giữ false. Tập nhỏ chỉ dùng kiểm thử thăm dò; mở rộng ít nhất hàng trăm ví dụ phân tầng cho báo cáo độ chính xác.
6. Chạy evaluate.py trên raw của mô hình. Báo precision, recall, F1 và cận dưới Wilson theo loại. Phần kiểm tra quote nguyên văn chỉ chứng minh tồn tại chuỗi, không chứng minh suy diễn đúng.
7. Đánh giá RAG trên câu hỏi có đường đi, không có đường đi, chiều ngược, năm khác nhau và phủ định. Kiểm tra mỗi trích dẫn hỗ trợ nhận định, không chỉ đúng số citation. Ghi tỷ lệ đường đi hợp lệ, độ đầy đủ bằng chứng, faithfulness và tỷ lệ từ chối đúng.

Không dùng 200/200 cạnh bảng để tuyên bố toàn bộ NLP, SLM hoặc GraphRAG vượt 90%. Không đánh dấu hoàn tất công việc gán nhãn của con người thay họ.
