"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
Chủ đề: Trợ Lý Tìm & Đặt Lịch Xem Nhà Trọ / Căn Hộ Cho Thuê
"""

# Dữ liệu tin đăng mẫu (giả lập database phòng trọ/căn hộ cho thuê)
_LISTINGS_DB = {
    "PT-101": {"location": "Cầu Giấy", "price": 4200000, "type": "Phòng trọ khép kín",
               "area_m2": 22, "amenities": ["Máy lạnh", "Gác lửng", "Chỗ để xe"]},
    "PT-102": {"location": "Cầu Giấy", "price": 3800000, "type": "Phòng trọ khép kín",
               "area_m2": 18, "amenities": ["Máy lạnh", "Wifi miễn phí"]},
    "PT-201": {"location": "Bình Thạnh", "price": 5000000, "type": "Căn hộ mini",
               "area_m2": 30, "amenities": ["Máy lạnh", "Bếp riêng", "Ban công", "Thang máy"]},
}

# Khung giờ xem nhà còn trống theo từng tin đăng (giả lập lịch)
_AVAILABLE_SLOTS = {
    "PT-101": ["09:00", "14:00", "16:30"],
    "PT-102": ["10:00", "15:00"],
    "PT-201": ["09:30", "13:00"],
}

# Lưu các lịch hẹn đã đặt trong phiên chạy hiện tại
_BOOKINGS = []


def search_listings(location: str, max_budget: int) -> str:
    """
    Tìm phòng trọ/căn hộ theo khu vực và ngân sách tối đa.

    Args:
        location (str): Khu vực cần tìm (Ví dụ: 'Cầu Giấy', 'Bình Thạnh')
        max_budget (int): Ngân sách tối đa mỗi tháng (VNĐ)

    Returns:
        str: Danh sách tin đăng phù hợp (mã tin, giá, loại phòng), hoặc thông báo lỗi nếu không có kết quả.
    """
    loc_lower = location.lower().strip()
    matches = [
        f"{listing_id}: {info['type']} tại {info['location']} - {info['price']:,} VNĐ/tháng"
        for listing_id, info in _LISTINGS_DB.items()
        if loc_lower in info["location"].lower() and info["price"] <= max_budget
    ]
    if not matches:
        return f"LỖI: Không có tin đăng phù hợp tại khu vực '{location}' với ngân sách {max_budget:,} VNĐ."
    return "Tìm thấy các tin đăng phù hợp:\n" + "\n".join(matches)


def get_listing_detail(listing_id: str) -> str:
    """
    Lấy thông tin chi tiết của một tin đăng.

    Args:
        listing_id (str): Mã tin đăng (Ví dụ: 'PT-101')

    Returns:
        str: Chi tiết diện tích, giá, tiện ích, hoặc thông báo lỗi nếu mã không tồn tại.
    """
    info = _LISTINGS_DB.get(listing_id.strip().upper())
    if not info:
        return f"LỖI: Tin đăng mã '{listing_id}' không tồn tại."
    return (
        f"Chi tiết {listing_id}: {info['type']} tại {info['location']}, "
        f"diện tích {info['area_m2']}m², giá {info['price']:,} VNĐ/tháng. "
        f"Tiện ích: {', '.join(info['amenities'])}."
    )


def check_viewing_slots(listing_id: str) -> str:
    """
    Kiểm tra các khung giờ còn trống để xem nhà của một tin đăng.

    Args:
        listing_id (str): Mã tin đăng (Ví dụ: 'PT-101')

    Returns:
        str: Danh sách khung giờ còn trống, hoặc thông báo lỗi nếu mã không tồn tại/hết chỗ.
    """
    listing_id = listing_id.strip().upper()
    if listing_id not in _LISTINGS_DB:
        return f"LỖI: Tin đăng mã '{listing_id}' không tồn tại."
    slots = _AVAILABLE_SLOTS.get(listing_id, [])
    if not slots:
        return f"LỖI: Tin đăng '{listing_id}' hiện không còn khung giờ trống để xem nhà."
    return f"Khung giờ còn trống cho {listing_id}: {', '.join(slots)}."


def book_viewing(listing_id: str, time_slot: str, full_name: str, phone_number: str) -> str:
    """
    Đặt lịch hẹn xem nhà cho một tin đăng vào khung giờ còn trống.

    Args:
        listing_id (str): Mã tin đăng (Ví dụ: 'PT-101')
        time_slot (str): Khung giờ muốn đặt (Ví dụ: '09:00')
        full_name (str): Họ tên người đặt lịch
        phone_number (str): Số điện thoại liên hệ

    Returns:
        str: Xác nhận đặt lịch thành công, hoặc thông báo lỗi nếu khung giờ không khả dụng/thiếu thông tin.
    """
    listing_id = listing_id.strip().upper()
    if listing_id not in _LISTINGS_DB:
        return f"LỖI: Tin đăng mã '{listing_id}' không tồn tại."
    if not full_name or not phone_number:
        return "LỖI: Thiếu họ tên hoặc số điện thoại liên hệ, không thể đặt lịch."
    if time_slot not in _AVAILABLE_SLOTS.get(listing_id, []):
        return f"LỖI: Khung giờ '{time_slot}' không khả dụng cho tin đăng '{listing_id}'. Vui lòng chọn giờ khác."

    _AVAILABLE_SLOTS[listing_id].remove(time_slot)
    booking = {"listing_id": listing_id, "time_slot": time_slot, "full_name": full_name, "phone_number": phone_number}
    _BOOKINGS.append(booking)
    return f"Đặt lịch thành công: {full_name} ({phone_number}) xem nhà '{listing_id}' lúc {time_slot}."


def cancel_viewing(listing_id: str, time_slot: str) -> str:
    """
    Hủy một lịch hẹn xem nhà đã đặt trước đó.

    Args:
        listing_id (str): Mã tin đăng (Ví dụ: 'PT-101')
        time_slot (str): Khung giờ đã đặt cần hủy (Ví dụ: '09:00')

    Returns:
        str: Xác nhận hủy thành công, hoặc thông báo lỗi nếu không tìm thấy lịch hẹn tương ứng.
    """
    listing_id = listing_id.strip().upper()
    for booking in _BOOKINGS:
        if booking["listing_id"] == listing_id and booking["time_slot"] == time_slot:
            _BOOKINGS.remove(booking)
            _AVAILABLE_SLOTS.setdefault(listing_id, []).append(time_slot)
            return f"Đã hủy lịch xem nhà '{listing_id}' lúc {time_slot}."
    return f"LỖI: Không tìm thấy lịch hẹn '{listing_id}' lúc {time_slot} để hủy."


# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "search_listings": search_listings,
    "get_listing_detail": get_listing_detail,
    "check_viewing_slots": check_viewing_slots,
    "book_viewing": book_viewing,
    "cancel_viewing": cancel_viewing,
}
