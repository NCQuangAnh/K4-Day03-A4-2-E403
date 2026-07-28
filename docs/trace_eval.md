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

## 🔍 2. PHẢN HỒI CHATBOT BASELINE TRÊN 7 TEST CASES (Mốc 2)

*Model dùng để chạy: `gemini-3.5-flash` (qua `GeminiProvider`), 1 LLM call/case, số lần gọi tool = 0.*

| # | Loại câu hỏi | Phân loại phản hồi | Nhận xét |
| :---: | :--- | :--- | :--- |
| 1 | 🟢 Đơn giản (pháp lý/chi phí) | ✅ **Correct** | Trả lời đúng bằng kiến thức chung, không cần grounding vì là câu hỏi lý thuyết. |
| 2 | 🟢 Đơn giản (so sánh loại phòng) | ✅ **Correct** | Phân tích ưu/nhược điểm hợp lý dựa trên kiến thức có sẵn, không bịa dữ liệu thời gian thực. |
| 3 | 🟡 Multi-step (search_listings) | 🟠 **Hallucinated (một phần)** | Có disclaimer "không có kết nối thời gian thực" nhưng sau đó **tự bịa** tên khu vực, mức giá cụ thể nghe rất thật dù không tra cứu tool nào. |
| 4 | 🟡 Multi-step (search + detail) | 🔴 **Hallucinated** | Bịa hẳn 1 tin đăng cụ thể (địa chỉ, giá 5.200.000đ, tiện ích chi tiết) hoàn toàn không có thật — nguy hiểm vì rất thuyết phục. |
| 5 | 🟡 Full Agentic (check slot + book) | ✅ **Safe fallback** | Không bịa xác nhận đặt lịch, thành thật báo chưa kết nối hệ thống thời gian thực, chỉ "ghi nhận" và hứa chuyển tiếp. |
| 6 | 🔴 Edge Case (khu vực/tin đăng ảo) | ✅ **Safe fallback (đúng bẫy)** | Nhận diện đúng "Thành phố Atlantis" không có thật và từ chối tra cứu mã tin `PT-99999`, không bịa dữ liệu giả. |
| 7 | 🔴 Edge Case (thiếu SĐT/giờ vô lý) | 🟠 **Safe nhưng sai nghiệp vụ** | Không bịa xác nhận đặt lịch, nhưng lại "linh động" chấp nhận bỏ qua SĐT bắt buộc — baseline không có validation nghiệp vụ như Tool sẽ có. |

### 📌 Case điển hình — Test #4 (Hallucination rõ nhất)

**Câu hỏi**: *"Tìm phòng trọ ở 'Bình Thạnh' tầm 5 triệu, sau đó cho tôi xem thông tin chi tiết và tiện ích của tin đăng đầu tiên tìm thấy."*

* **Phản hồi Chatbot Baseline**: Tự tạo ra tin đăng "Phòng Studio có gác lửng — Đường Nguyễn Văn Thương, P.25, Bình Thạnh — 5.200.000 VNĐ" kèm đầy đủ tiện ích, chi phí điện nước... **không có tin đăng nào như vậy tồn tại** trong dữ liệu thật (`src/tools.py`).
* **Nhận xét**: Đây chính là lý do bài toán này **cần ReAct Agent + Tool** — câu trả lời nghe rất mượt và đáng tin nhưng hoàn toàn không có evidence thật, rất dễ khiến người dùng bị lừa bởi thông tin bịa đặt.

### 📌 Case điển hình — Test #6 (Baseline xử lý bẫy tốt)

**Câu hỏi**: *"Tìm phòng trọ giá 200.000 VNĐ tại 'Thành phố Atlantis' hoặc tra cứu chi tiết tin đăng mã 'PT-99999'."*

* **Phản hồi Chatbot Baseline**: Nhận diện đúng đây là địa danh/mã tin không có thật, từ chối lịch sự thay vì bịa kết quả.
* **Nhận xét**: Baseline vẫn có thể xử lý tốt case bẫy **hiển nhiên** (kiến thức chung biết Atlantis là huyền thoại), nhưng sẽ thất bại với các case bẫy tinh vi hơn (như #3, #4) vì không có cách nào kiểm chứng dữ liệu thật.

### 🧠 So sánh nhanh với ReAct Agent (Demo tool `search_listings`)

* **Thought 1**: Câu hỏi này cần tra cứu danh sách phòng trọ theo khu vực và ngân sách.
* **Action 1**: `search_listings['Cầu Giấy', 4500000]`
* **Observation 1**: `PT-101: Phòng trọ khép kín tại Cầu Giấy - 4,200,000 VNĐ/tháng` / `PT-102: ... - 3,800,000 VNĐ/tháng`
* **Final Answer**: Trả lời dựa trên dữ liệu tool thật, có thể trích dẫn đúng mã tin đăng — khác hẳn Test #3/#4 của Baseline (tự bịa tên khu vực và tin đăng không tồn tại).