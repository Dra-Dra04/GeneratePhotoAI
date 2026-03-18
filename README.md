# AiDaPhuongTien

## Mô tả dự án
AiDaPhuongTien là phần mềm ứng dụng các mô hình trí tuệ nhân tạo vào việc phân tích và xử lý các tệp dữ liệu đa phương tiện (hình ảnh, âm thanh, video). Hệ thống được xây dựng để nhận đầu vào từ người dùng, thực thi các thuật toán AI tương ứng và trả về kết quả phân tích. Giao diện chương trình được phân chia thành các Tab để quản lý từng luồng công việc cụ thể.

## Cấu trúc chức năng chính
* **Xử lý đa định dạng:** Chấp nhận và trích xuất dữ liệu từ nhiều loại tệp tin đa phương tiện tiêu chuẩn.
* **Giao diện phân mảnh (Tab-based):** Tổ chức các chức năng theo nhóm, bao gồm khu vực nạp dữ liệu, khu vực cấu hình thông số và khu vực thực thi mô hình AI.

## Quản lý tài nguyên và Xử lý tác vụ nặng (Logic Tab 3)

Tab 3 là phân hệ đảm nhiệm việc chạy các mô hình AI. Đây là quá trình tính toán cường độ cao, tiêu thụ lượng lớn tài nguyên phần cứng (CPU, GPU, RAM). Nếu không được kiểm soát, việc này có thể dẫn đến hiện tượng thắt cổ chai, khiến giao diện người dùng bị đơ (Not Responding) hoặc treo toàn bộ hệ thống.

Để khắc phục vấn đề tràn tài nguyên và giảm tải cho hệ thống tại Tab 3, dự án áp dụng các phương pháp phân bổ sau:

1. **Xử lý Đa luồng (Multithreading) và Bất đồng bộ (Asynchronous):**
   Logic tính toán AI được tách hoàn toàn khỏi luồng xử lý giao diện (UI Thread). Toàn bộ khối lượng công việc nặng tại Tab 3 được đẩy sang các luồng công nhân (Worker Threads) chạy ngầm. Điều này đảm bảo giao diện phần mềm vẫn nhận phản hồi và tương tác bình thường trong khi máy đang xử lý dữ liệu.

2. **Phân mảnh dữ liệu xử lý (Data Chunking / Batching):**
   Thay vì tải toàn bộ tệp đa phương tiện lớn (như video) vào RAM cùng một thời điểm, hệ thống chia nhỏ dữ liệu thành các đoạn (chunk) hoặc lô (batch) có kích thước cố định. Các đoạn này được đưa vào mô hình AI xử lý tuần tự, giúp duy trì mức sử dụng RAM ở ngưỡng an toàn.

3. **Thu hồi bộ nhớ chủ động:**
   Cơ chế giải phóng bộ nhớ được gọi ngay lập tức sau khi hoàn tất xử lý từng đoạn dữ liệu (chunk). Các biến tạm và bộ nhớ đệm của mô hình AI không còn sử dụng sẽ bị xóa bỏ nhằm ngăn chặn rò rỉ bộ nhớ (memory leak) trong các phiên làm việc kéo dài.

4. **Kiểm soát chu kỳ tính toán (Throttling):**
   Cấu trúc lặp của thuật toán tại Tab 3 được chèn các khoảng nghỉ ngắn (sleep intervals). Việc này nhằm tránh tình trạng CPU bị ép hoạt động ở mức 100% liên tục, tạo không gian cho hệ điều hành xử lý các tác vụ nền khác của máy tính.
