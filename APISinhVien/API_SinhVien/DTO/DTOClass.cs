namespace API_SinhVien.DTO;
public class StudentDetailDto
{
    public int StudentID { get; set; }
    public string StudentCode { get; set; } = string.Empty;
    public string LastName { get; set; } = string.Empty;
    public string FirstName { get; set; } = string.Empty;
    public string FullName => $"{LastName} {FirstName}";
    public string? Email { get; set; }
    public string? Mobile { get; set; }
    public DateTime? Ngaysinh { get; set; }

    public int MajorID { get; set; }
    public string MajorCode { get; set; } = string.Empty;
    public string MajorTitle { get; set; } = string.Empty;

    public int DepartmentID { get; set; }
    public string DepartmentCode { get; set; } = string.Empty;
    public string DepartmentTitle { get; set; } = string.Empty;
}

// 1. Model để hứng dữ liệu phẳng từ câu query SQL Server
public class StudentCourseFlatDto
{
    public int HocKyID { get; set; }
    public string MaHocKy { get; set; } = string.Empty;
    public string TenHocKy { get; set; } = string.Empty;
    public string NamHoc { get; set; } = string.Empty;

    public int MonHocID { get; set; }
    public string MaMonHoc { get; set; } = string.Empty;
    public string TenMonHoc { get; set; } = string.Empty;
    public short SoTinChi { get; set; }
}

// 2. Model cấu trúc đầu ra (Response) gửi về cho Client - Gom theo học kỳ
public class SemesterCoursesDto
{
    public int HocKyID { get; set; }
    public string MaHocKy { get; set; } = string.Empty;
    public string TenHocKy { get; set; } = string.Empty;
    public string NamHoc { get; set; } = string.Empty;
    public List<CourseDto> MonHocs { get; set; } = new();
}

// 3. Model chi tiết môn học nằm trong học kỳ
public class CourseDto
{
    public int MonHocID { get; set; }
    public string MaMonHoc { get; set; } = string.Empty;
    public string TenMonHoc { get; set; } = string.Empty;
    public short SoTinChi { get; set; }
}

public class StudentScoreDto
{
    public int HocKyID { get; set; }
    public string MaHocKy { get; set; } = string.Empty;
    public string TenHocKy { get; set; } = string.Empty;
    public string NamHoc { get; set; } = string.Empty;

    public int MonHocID { get; set; }
    public string MaMonHoc { get; set; } = string.Empty;
    public string TenMonHoc { get; set; } = string.Empty;
    public short SoTinChi { get; set; }

    // Các trường điểm số từ bảng Tbl_DiemSinhVien
    public decimal? DiemChuyenCan { get; set; }
    public decimal? DiemGiuaKy { get; set; }
    public decimal? DiemCuoiKy { get; set; }
    public decimal? DiemTongKet { get; set; }
    public string? DiemChu { get; set; }
    public string? GhiChu { get; set; }
}

// DTO cho danh sách học kỳ
public class HocKyDto
{
    public int HocKyID { get; set; }
    public string MaHocKy { get; set; } = string.Empty;
    public string TenHocKy { get; set; } = string.Empty;
    public string NamHoc { get; set; } = string.Empty;
    public DateTime? TuNgay { get; set; }
    public DateTime? DenNgay { get; set; }
    public short? SoThuTu { get; set; }
}

// DTO cho danh sách môn học
public class MonHocDto
{
    public int MonHocID { get; set; }
    public string MaMonHoc { get; set; } = string.Empty;
    public string TenMonHoc { get; set; } = string.Empty;
    public string? TenTiengAnh { get; set; }
    public short SoTinChi { get; set; }
    public short? SoTietLyThuyet { get; set; }
    public short? SoTietThucHanh { get; set; }
    public int? KhoaQuanLy { get; set; }
    public string? KhoaQuanLyTitle { get; set; }
}


// Model hứng dữ liệu chuẩn đầu ra cấp Ngành (PLO)
public class PloDto
{
    public int PLOID { get; set; }
    public int NganhID { get; set; }
    public string MaPLO { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
    public string? Description { get; set; }
}

// Model hứng dữ liệu chuẩn đầu ra cấp Môn học (CLO)
public class CloDto
{
    public int CLOID { get; set; }
    public int MonHocID { get; set; }
    public string MaCLO { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
    public string? Description { get; set; }
}

// Model hứng cấu hình hình thức đánh giá cho từng CLO
public class CloEvaluationDto
{
    public int ID { get; set; }
    public int CLOID { get; set; }
    public string MaCLO { get; set; } = string.Empty;
    public string CloTitle { get; set; } = string.Empty;
    public int DanhGiaID { get; set; }
    public string EvaluationCode { get; set; } = string.Empty;
    public string EvaluationTitle { get; set; } = string.Empty;
    public double TyLePhanTram { get; set; }
}

// Model hứng ma trận ánh xạ đóng góp giữa CLO và PLO
public class CloPloMappingDto
{
    public int ID { get; set; }
    public int CLOID { get; set; }
    public string MaCLO { get; set; } = string.Empty;
    public string CloTitle { get; set; } = string.Empty;
    public int PLOID { get; set; }
    public string MaPLO { get; set; } = string.Empty;
    public string PloTitle { get; set; } = string.Empty;
    public byte MucDoDongGop { get; set; }

    // Thuộc tính bổ sung để hiển thị text dễ đọc (Introduce / Reinforce / Master)
    public string MucDoDongGopText => MucDoDongGop switch
    {
        1 => "Introduce (I)",
        2 => "Reinforce (R)",
        3 => "Master (M)",
        _ => "Unknown"
    };
}

// Model kết quả điểm CLO của sinh viên cho 1 môn học
public class StudentCloScoreDto
{
    public int CLOID { get; set; }
    public string MaCLO { get; set; } = string.Empty;
    public string CloTitle { get; set; } = string.Empty;

    // Điểm đạt được của CLO (hệ 10)
    public decimal CloScore { get; set; }
}

// Model đánh giá mức độ đạt PLO toàn khóa của sinh viên
public class StudentPloAchievementDto
{
    public int PLOID { get; set; }
    public string MaPLO { get; set; } = string.Empty;
    public string PloTitle { get; set; } = string.Empty;

    // Mức độ đạt chuẩn đầu ra ngành (hệ 10)
    public decimal PloScore { get; set; }

    // Tổng trọng số đóng góp của các CLO tạo nên điểm số này
    public int TotalWeight { get; set; }
}