# Tài liệu Dịch vụ API Hệ thống Sinh Viên

Dưới đây là tài liệu mô tả chi tiết các dịch vụ API hiện tại đang hoạt động trong mã nguồn, dựa trên Controller `StudentsController` và `WeatherForecastController`.

---

## 1. API Lấy thông tin cá nhân sinh viên

- **Route API:** `GET /api/Students/{studentCode}`
- **Summary:** Lấy thông tin chi tiết của sinh viên dựa vào mã sinh viên (StudentCode). Dữ liệu bao gồm thông tin cá nhân, thông tin chuyên ngành và khoa trực thuộc.
- **Input:**
  - `studentCode` (Path parameter, kiểu `string`): **Bắt buộc phải có**.
  - **Hành vi:** 
    - Nếu *truyền* mã hợp lệ: API sẽ truy vấn database để lấy thông tin.
    - Nếu *không truyền* hoặc truyền chuỗi rỗng/khoảng trắng: API sẽ chặn lại và trả về lỗi `400 BadRequest` ("Mã sinh viên không được để trống.").
- **Output:**
  - Trả về dữ liệu kiểu `StudentDetailDto` hoặc mã lỗi `404 NotFound` nếu không tìm thấy sinh viên trong cơ sở dữ liệu.
  - **Mô tả các trường:**
    - `StudentID`, `StudentCode`: ID hệ thống và Mã sinh viên.
    - `LastName`, `FirstName`: Họ đệm và Tên.
    - `Email`, `Mobile`, `Ngaysinh`: Thông tin liên lạc và ngày sinh.
    - `MajorID`, `MajorCode`, `MajorTitle`: ID, mã và tên của Chuyên ngành.
    - `DepartmentID`, `DepartmentCode`, `DepartmentTitle`: ID, mã và tên của Khoa.
  - **Ví dụ cấu trúc trả về:**
    ```json
    {
      "StudentID": 101,
      "StudentCode": "SV12345",
      "LastName": "Nguyễn Văn",
      "FirstName": "A",
      "Email": "nva@example.com",
      "Mobile": "0901234567",
      "Ngaysinh": "2000-01-01T00:00:00",
      "MajorID": 2,
      "MajorCode": "CNPM",
      "MajorTitle": "Công nghệ phần mềm",
      "DepartmentID": 1,
      "DepartmentCode": "CNTT",
      "DepartmentTitle": "Công nghệ thông tin"
    }
    ```

---

## 2. API Lấy danh sách môn học đã đăng ký của sinh viên

- **Route API:** `GET /api/Students/{studentCode}/courses`
- **Summary:** Lấy danh sách tất cả các môn học mà sinh viên đã đăng ký, được gom nhóm theo từng học kỳ một cách tự động.
- **Input:**
  - `studentCode` (Path parameter, kiểu `string`): **Bắt buộc phải có**.
  - **Hành vi:**
    - Nếu *truyền* hợp lệ: Truy vấn các môn học không bị xóa mềm, gom nhóm theo ID học kỳ, sắp xếp từ mới đến cũ.
    - Nếu *không truyền*: Trả về lỗi `400 BadRequest` ("Mã sinh viên không được để trống.").
- **Output:**
  - Mảng các nhóm môn học đại diện cho từng học kỳ (`SemesterCoursesDto[]`). Báo `404 NotFound` nếu không có dữ liệu.
  - **Mô tả các trường:**
    - `HocKyID`, `MaHocKy`, `TenHocKy`, `NamHoc`: Thông tin định danh học kỳ và năm học.
    - `MonHocs`: Mảng chứa các môn học thuộc học kỳ đó, mỗi môn học có `MonHocID`, `MaMonHoc`, `TenMonHoc`, `SoTinChi`.
  - **Ví dụ cấu trúc trả về:**
    ```json
    [
      {
        "HocKyID": 3,
        "MaHocKy": "HK1_2023",
        "TenHocKy": "Học kỳ 1",
        "NamHoc": "2023-2024",
        "MonHocs": [
          {
            "MonHocID": 10,
            "MaMonHoc": "CS101",
            "TenMonHoc": "Nhập môn lập trình",
            "SoTinChi": 3
          }
        ]
      }
    ]
    ```

---

## 3. API Lấy điểm số của sinh viên

- **Route API:** `GET /api/Students/{studentCode}/scores`
- **Summary:** Lấy bảng điểm chi tiết của sinh viên theo mã sinh viên. Có thể xem toàn bộ bảng điểm hoặc lọc chi tiết theo một học kỳ cụ thể.
- **Input:**
  - `studentCode` (Path parameter, kiểu `string`): **Bắt buộc phải có**.
  - `hocKyId` (Query parameter, kiểu `int?`): **Không bắt buộc**.
  - **Hành vi:**
    - Nếu *không truyền* `studentCode`: Báo lỗi `400 BadRequest`.
    - Nếu *không truyền* `hocKyId` (hoặc truyền bằng `0`): API sẽ trả về toàn bộ điểm số của sinh viên ở **tất cả** các học kỳ.
    - Nếu *có truyền* `hocKyId` hợp lệ (VD: `?hocKyId=3`): API sẽ chỉ lọc ra điểm số thuộc đúng học kỳ có ID tương ứng.
- **Output:**
  - Mảng điểm số chi tiết từng môn (`StudentScoreDto[]`). Báo lỗi `404 NotFound` nếu không tìm thấy điểm (kèm theo thông báo chi tiết lỗi do học kỳ hay do sinh viên).
  - **Mô tả các trường:** Các thông tin định danh học kỳ, môn học cộng thêm chi tiết điểm (`DiemChuyenCan`, `DiemGiuaKy`, `DiemCuoiKy`, `DiemTongKet`, `DiemChu`, `GhiChu`).
  - **Ví dụ cấu trúc trả về:**
    ```json
    [
      {
        "HocKyID": 3,
        "TenHocKy": "Học kỳ 1",
        "NamHoc": "2023-2024",
        "MonHocID": 10,
        "TenMonHoc": "Nhập môn lập trình",
        "SoTinChi": 3,
        "DiemChuyenCan": 10.0,
        "DiemGiuaKy": 8.5,
        "DiemCuoiKy": 9.0,
        "DiemTongKet": 9.0,
        "DiemChu": "A",
        "GhiChu": "Giỏi"
      }
    ]
    ```

---

## 4. API Lấy danh sách tất cả học kỳ

- **Route API:** `GET /api/Students/semesters`
- **Summary:** Truy xuất danh sách toàn bộ các học kỳ có trong hệ thống (không bị xóa mềm), sắp xếp từ mới nhất xuống cũ nhất.
- **Input:** 
  - **Không có** (Không yêu cầu truyền bất kì tham số nào).
- **Output:**
  - Mảng các đối tượng học kỳ (`HocKyDto[]`).
  - **Mô tả các trường:** Định danh học kỳ (`HocKyID`, `MaHocKy`, `TenHocKy`, `NamHoc`), mốc thời gian (`TuNgay`, `DenNgay`) và thứ tự sắp xếp (`SoThuTu`).
  - **Ví dụ cấu trúc trả về:**
    ```json
    [
      {
        "HocKyID": 4,
        "MaHocKy": "HK2_2023",
        "TenHocKy": "Học kỳ 2",
        "NamHoc": "2023-2024",
        "TuNgay": "2024-02-01T00:00:00",
        "DenNgay": "2024-06-30T00:00:00",
        "SoThuTu": 2
      }
    ]
    ```

---

## 5. API Lấy danh sách tất cả môn học

- **Route API:** `GET /api/Students/subjects`
- **Summary:** Lấy danh mục tất cả môn học hiện có. Hỗ trợ lọc danh sách môn học theo Khoa quản lý.
- **Input:**
  - `khoaQuanLy` (Query parameter, kiểu `int?`): **Không bắt buộc**.
  - **Hành vi:**
    - Nếu *không truyền*: Sẽ trả về danh sách **toàn bộ** tất cả các môn học trong hệ thống.
    - Nếu *có truyền* (VD: `?khoaQuanLy=1`): Sẽ chỉ trả về các môn học do Khoa có ID = 1 quản lý.
- **Output:**
  - Mảng các môn học (`MonHocDto[]`).
  - **Mô tả các trường:** Thông tin định danh môn (`MonHocID`, `MaMonHoc`, `TenMonHoc`, `TenTiengAnh`), số lượng tín chỉ/tiết học (`SoTinChi`, `SoTietLyThuyet`, `SoTietThucHanh`) và thông tin bộ phận quản lý (`KhoaQuanLy`, `KhoaQuanLyTitle`).
  - **Ví dụ cấu trúc trả về:**
    ```json
    [
      {
        "MonHocID": 10,
        "MaMonHoc": "CS101",
        "TenMonHoc": "Nhập môn C#",
        "TenTiengAnh": "Intro to C#",
        "SoTinChi": 3,
        "SoTietLyThuyet": 30,
        "SoTietThucHanh": 15,
        "KhoaQuanLy": 1,
        "KhoaQuanLyTitle": "Công nghệ thông tin"
      }
    ]
    ```