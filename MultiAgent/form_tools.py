from langchain_core.tools import tool
import time

# Cấu hình địa chỉ Backend của bạn (Thay đổi port cho đúng với máy của bạn)
BASE_URL = "https://localhost:44326/api"

# Mock Database lưu trữ Link biểu mẫu
KHO_BIEU_MAU = {
    "BM_ĐH/01/ĐT": f"{BASE_URL}/Upload/BieuMau/bm01-phieu-de-nghi-duoc-tam-dung-ket-qua-hoc-tap.docx",
    "BM_ĐH/02/ĐT": f"{BASE_URL}/Upload/BieuMau/bm02_phieu-dang-ky-tro-lai-hoc-tap.docx",
    "BM_ĐH/03/ĐT": f"{BASE_URL}/Upload/BieuMau/bm03_phieu-de-nghi-chuyen-nganh-dao-tao.docx",
    "BM_ĐH/04/ĐT": f"{BASE_URL}/Upload/BieuMau/bm04_phieu-dang-ky-hoc-cung-luc-hai-chuong-trinh.docx",
    "BM_ĐH/05/ĐT": f"{BASE_URL}/Upload/BieuMau/bm05_phieu-de-nghi-chuyen-truong-den.docx",
    "BM_ĐH/06/ĐT": f"{BASE_URL}/Upload/BieuMau/bm06_phieu-de-nghi-chuyen-truong-di.docx",
    "BM_ĐH/07/ĐT": f"{BASE_URL}/Upload/BieuMau/bm07_phieu-de-nghi-duoc-thoi-hoc.docx",
    "BM_ĐH/08/ĐT": f"{BASE_URL}/Upload/BieuMau/bm08_phieu-de-nghi-chuyen-he-dao-tao.docx",
    "BM_ĐH/09/ĐT": f"{BASE_URL}/Upload/BieuMau/bm09_phieu-dang-ky-hoan-thi-do-vang-thi-cuoi-ky.docx",
    "BM_ĐH/10/ĐT": f"{BASE_URL}/Upload/BieuMau/bm10_phieu-de-nghi-huy-hoc-phan.docx",
    "BM_ĐH/11/ĐT": f"{BASE_URL}/Upload/BieuMau/bm11_phieu-dang-ky-xet-mien-giam-va-cong-nhan-diem.docx",
    "BM_ĐH/12/ĐT": f"{BASE_URL}/Upload/BieuMau/bm12_phieu-dang-ky-xet-tot-nghiep.docx",
    "BM_ĐH/MIEN-NGOAINGU/ĐT": f"{BASE_URL}/Upload/BieuMau/bieu_mau_mienhoc_mienthi_ngoaingu.docx"
}

@tool
def lay_link_bieu_mau(ma_bieu_mau: str) -> str:
    """
    Sử dụng công cụ này KHI VÀ CHỈ KHI sinh viên yêu cầu lấy đơn từ, biểu mẫu, 
    phiếu đăng ký. 
    Tham số:
    - ma_bieu_mau (str): BẮT BUỘC phải là mã biểu mẫu chính xác (Ví dụ: BM_ĐH/01/ĐT).
    Nếu chưa biết mã biểu mẫu, HÃY GỌI tool tra_cuu_quy_che trước để tìm mã.
    """
    time.sleep(5)
    # print(f"\n[🔧 Tool Biểu Mẫu] -> Đang trích xuất link cho mã: {ma_bieu_mau}...")
    
    # Lấy link từ DB, loại bỏ khoảng trắng thừa nếu có
    ma_bieu_mau = ma_bieu_mau.strip()
    link = KHO_BIEU_MAU.get(ma_bieu_mau)
    
    if link:
        return f"Link tải file biểu mẫu {ma_bieu_mau} là: {link}"
    else:
        return f"Xin lỗi, hệ thống chưa cập nhật link tải cho biểu mẫu {ma_bieu_mau}."