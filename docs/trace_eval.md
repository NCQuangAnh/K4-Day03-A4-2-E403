# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)
*Dành cho Role 5: Observability & Reviewer*

---

## 📍 0. MỐC 1 — ĐỊNH HÌNH BÀI TOÁN (Chủ đề #10)

**Chủ đề đã chọn**: *Trợ Lý Tìm & Đặt Lịch Xem Nhà Trọ / Căn Hộ Cho Thuê*

Người dùng cần tìm phòng trọ/căn hộ theo tiêu chí (khu vực, ngân sách, loại phòng), xem chi tiết tin đăng, kiểm tra khung giờ còn trống và đặt lịch hẹn xem nhà trực tiếp với chủ nhà.

### 🛠️ Danh sách Tool dự kiến (`src/tools.py` — Role 2)

| # | Tên Tool | Chức năng |
| :---: | :--- | :--- |
| 1 | `search_listings` | Tìm phòng trọ/căn hộ theo khu vực, ngân sách, loại phòng |
| 2 | `get_listing_detail` | Lấy chi tiết một tin đăng (giá, diện tích, tiện ích, chủ nhà) |
| 3 | `check_viewing_slots` | Kiểm tra các khung giờ còn trống để xem nhà |
| 4 | `book_viewing` | Đặt lịch hẹn xem nhà (side-effect: ghi nhận booking) |
| 5 | `cancel_viewing` | Hủy lịch hẹn đã đặt trước đó |

### ⚠️ Failure Modes dự kiến (Role 3)

| Tình huống lỗi | Cách tool nên phản hồi |
| :--- | :--- |
| Khu vực/quận không có trong dữ liệu | Trả chuỗi lỗi: *"Không tìm thấy khu vực '...'"* |
| Ngân sách quá thấp, không có tin phù hợp | Trả chuỗi: *"Không có tin đăng phù hợp ngân sách"* |
| `listing_id` không tồn tại | Trả chuỗi: *"Tin đăng không tồn tại"* |
| Khung giờ đã có người đặt / nằm trong quá khứ | Trả chuỗi: *"Khung giờ không khả dụng, vui lòng chọn giờ khác"* |
| Thiếu thông tin liên hệ khi đặt lịch | Trả chuỗi yêu cầu bổ sung, không crash chương trình |

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

| Tiêu chí | Điểm (1-5) | Lý do đánh giá |
| :--- | :---: | :--- |
| 🧠 **Multi-step Reasoning** | `4/5` | Cần suy luận từ tìm phòng đúng tiêu chí đến chọn khung giờ và xác nhận đặt lịch. |
| 🛠️ **Tool Interaction** | `5/5` | Cần tra cứu dữ liệu tin đăng thời gian thực và ghi nhận đặt lịch (có side-effect). |
| 🔀 **Dynamic Decision** | `4/5` | Kết quả tìm kiếm (có/không có phòng phù hợp) quyết định bước tiếp theo (đổi tiêu chí hay đặt lịch). |
| ⏳ **Long Horizon** | `4/5` | Quy trình gồm 3-4 bước: tìm kiếm ➔ xem chi tiết ➔ kiểm tra lịch trống ➔ đặt lịch. |
| **TỔNG ĐIỂM FIT** | **17/20** | **KẾT LUẬN: BÀI TOÁN RẤT NÊN DÙNG REACT AGENT!** |

---

## 🔍 2. SO SÁNH PHẢN HỒI (TEST CASE #3)

**Câu hỏi**: *"Thời tiết ở Hà Nội hôm nay thế nào và tôi nên mặc gì đi chơi?"*

### 🤖 Chatbot Baseline:
* **Phản hồi**: *"Tôi không có truy cập Internet thời gian thực nên không biết thời tiết hôm nay ở Hà Nội."*
* **Nhận xét**: An toàn nhưng không giải quyết được nhu cầu thực tế của người dùng.

### 🧠 ReAct Agent:
* **Thought 1**: Cần tra cứu thời tiết Hà Nội.
* **Action 1**: `get_weather['Hà Nội']`
* **Observation 1**: `Thời tiết Hà Nội: 28°C, Nắng nhẹ, Độ ẩm 65%.`
* **Thought 2**: Đã có thông tin 28°C nắng nhẹ, đưa ra lời khuyên trang phục.
* **Final Answer**: *"Thời tiết Hà Nội hôm nay 28°C, nắng nhẹ. Bạn nên mặc quần áo thoáng mát!"*
* **Nhận xét**: Hoàn thành xuất sắc nhiệm vụ nhờ sự kết hợp giữa suy luận và công cụ.