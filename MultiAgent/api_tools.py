import requests
from langchain_core.tools import tool

# Cấu hình địa chỉ Backend của bạn (Thay đổi port cho đúng với máy của bạn)
BASE_URL = "https://localhost:44326/api"

# -------------------------------------------------------------------------
# TOOL 1: LẤY THÔNG TIN CÁ NHÂN
# -------------------------------------------------------------------------
@tool
def tra_cuu_thong_tin_sinh_vien(student_code: str) -> str:
    """
    Sử dụng công cụ này KHI VÀ CHỈ KHI cần lấy thông tin chi tiết của sinh viên 
    (Họ tên, ngày sinh, chuyên ngành, khoa, email, số điện thoại...).
    
    Tham số:
    - student_code (str): Mã sinh viên (BẮT BUỘC). Nếu sinh viên chưa cung cấp, phải hỏi lại.
    """
    # print(f"\n[🔧 Tool API] -> Lấy thông tin cá nhân cho MSSV: {student_code}...")
    url = f"{BASE_URL}/Students/{student_code}"
    
    try:
        response = requests.get(url, timeout=10, verify=False)
        if response.status_code == 200:
            return f"Thông tin sinh viên: {str(response.json())}"
        elif response.status_code == 404:
            return "Không tìm thấy sinh viên này trong cơ sở dữ liệu hệ thống."
        else:
            return f"Lỗi hệ thống ({response.status_code}): {response.text}"
    except Exception as e:
        return f"Lỗi kết nối Backend: {str(e)}"

# -------------------------------------------------------------------------
# TOOL 2: LẤY DANH SÁCH MÔN ĐÃ ĐĂNG KÝ
# -------------------------------------------------------------------------
@tool
def tra_cuu_mon_hoc_da_dang_ky(student_code: str) -> str:
    """
    Sử dụng công cụ này KHI VÀ CHỈ KHI sinh viên hỏi về các môn học họ ĐÃ ĐĂNG KÝ 
    hoặc TKB/lịch học của cá nhân họ trong các học kỳ.
    
    Tham số:
    - student_code (str): Mã sinh viên (BẮT BUỘC). Nếu sinh viên chưa cung cấp, phải hỏi lại.
    """
    # print(f"\n[🔧 Tool API] -> Lấy danh sách môn học đã đăng ký của MSSV: {student_code}...")
    url = f"{BASE_URL}/Students/{student_code}/courses"
    
    try:
        response = requests.get(url, timeout=10, verify=False)
        if response.status_code == 200:
            return f"Danh sách môn đã đăng ký (theo học kỳ): {str(response.json())}"
        elif response.status_code == 404:
            return "Không tìm thấy dữ liệu đăng ký môn học của sinh viên này."
        else:
            return f"Lỗi hệ thống ({response.status_code}): {response.text}"
    except Exception as e:
        return f"Lỗi kết nối Backend: {str(e)}"

# -------------------------------------------------------------------------
# TOOL 3: LẤY ĐIỂM SỐ
# -------------------------------------------------------------------------
@tool
def tra_cuu_diem_sinh_vien(student_code: str, hoc_ky_id: int = 0) -> str:
    """
    Sử dụng công cụ này KHI VÀ CHỈ KHI sinh viên yêu cầu tra cứu điểm số, 
    kết quả học tập, điểm thi, hoặc GPA.
    
    Tham số:
    - student_code (str): Mã sinh viên (BẮT BUỘC). Nếu sinh viên chưa cung cấp, phải hỏi lại.
    - hoc_ky_id (int): ID của học kỳ (TÙY CHỌN). Trả về 0 nếu sinh viên muốn xem điểm toàn khóa.
    """
    # print(f"\n[🔧 Tool API] -> Lấy điểm số cho MSSV: {student_code} (Học kỳ ID: {hoc_ky_id})...")
    url = f"{BASE_URL}/Students/{student_code}/scores"
    params = {}
    if hoc_ky_id > 0:
        params['hocKyId'] = hoc_ky_id

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return f"Bảng điểm chi tiết: {str(response.json())}"
        elif response.status_code == 404:
            return "Không tìm thấy dữ liệu điểm của sinh viên này."
        else:
            return f"Lỗi hệ thống ({response.status_code}): {response.text}"
    except Exception as e:
        return f"Lỗi kết nối Backend: {str(e)}"

# -------------------------------------------------------------------------
# TOOL 4: LẤY DANH SÁCH HỌC KỲ (DỮ LIỆU TỪ ĐIỂN)
# -------------------------------------------------------------------------
import datetime
hom_nay = datetime.datetime.now().strftime("%d-%m-%Y")
@tool
def lay_danh_sach_hoc_ky() -> str:
    """
    Sử dụng công cụ này KHI CẦN TÌM 'ID' CỦA MỘT HỌC KỲ CỤ THỂ. 
    (Ví dụ: Sinh viên hỏi 'điểm học kỳ 1 năm 2023', bạn cần gọi hàm này trước để biết 
    HocKyID của nó là số mấy, sau đó mới truyền vào hàm tra_cuu_diem_sinh_vien).
    """
    # print(f"\n[🔧 Tool API] -> Lấy danh mục tất cả Học kỳ...")
    url = f"{BASE_URL}/Students/semesters"
    
    try:
        response = requests.get(url, timeout=10, verify=False)
        if response.status_code == 200:
            return f"Danh mục học kỳ: {str(response.json())}"
        else:
            return f"Lỗi hệ thống ({response.status_code}): {response.text}"
    except Exception as e:
        return f"Lỗi kết nối Backend: {str(e)}"

# -------------------------------------------------------------------------
# TOOL 5: LẤY DANH MỤC MÔN HỌC (DỮ LIỆU TỪ ĐIỂN)
# -------------------------------------------------------------------------
@tool
def lay_danh_muc_mon_hoc(khoa_quan_ly_id: int = 0) -> str:
    """
    Sử dụng công cụ này KHI sinh viên hỏi thông tin chung về MỘT MÔN HỌC BẤT KỲ 
    trong trường (Ví dụ: môn này mấy tín chỉ, do khoa nào dạy...).
    Không dùng hàm này để xem môn sinh viên đã đăng ký.
    
    Tham số:
    - khoa_quan_ly_id (int): ID của Khoa quản lý (TÙY CHỌN). Truyền 0 nếu tìm toàn trường.
    """
    # print(f"\n[🔧 Tool API] -> Lấy danh mục Môn học toàn trường (Khoa ID: {khoa_quan_ly_id})...")
    url = f"{BASE_URL}/Students/subjects"
    params = {}
    if khoa_quan_ly_id > 0:
        params['khoaQuanLy'] = khoa_quan_ly_id

    try:
        response = requests.get(url, params=params, timeout=10, verify=False)
        if response.status_code == 200:
            return f"Danh mục môn học: {str(response.json())}"
        else:
            return f"Lỗi hệ thống ({response.status_code}): {response.text}"
    except Exception as e:
        return f"Lỗi kết nối Backend: {str(e)}"