using API_SinhVien.DTO;
using Dapper;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Data.SqlClient;

namespace API_SinhVien.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class StudentsController : ControllerBase
    {
        private readonly string _connectionString;

        // Inject IConfiguration trực tiếp vào Controller
        public StudentsController(IConfiguration configuration)
        {
            // Lấy chuỗi kết nối từ appsettings.json
            _connectionString = configuration.GetConnectionString("DefaultConnection")
                                ?? throw new InvalidOperationException("Chưa cấu hình chuỗi kết nối.");
        }

        /// <summary>
        /// Get thông tin sinh viên theo mã sinh viên (StudentCode)
        /// </summary>
        /// <param name="studentCode"></param>
        /// <returns></returns>
        [HttpGet("{studentCode}")]
        public async Task<IActionResult> GetStudent(string studentCode)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(studentCode))
                {
                    return BadRequest(new { Message = "Mã sinh viên không được để trống." });
                }

                // Viết câu lệnh SQL trực tiếp
                string sqlQuery = @"SELECT s.StudentID, s.StudentCode, s.LastName, s.FirstName, s.Email, s.Mobile, s.Ngaysinh,
                    n.RowId AS MajorID, n.Code AS MajorCode, n.Title AS MajorTitle,
                    k.DepartmentID, k.Code AS DepartmentCode, k.Title AS DepartmentTitle
                FROM Tbl_Students s
                -- Dùng LEFT JOIN để lấy được cả sinh viên chưa xếp ngành
                LEFT JOIN DM_NganhDaoTao n ON s.MajorID = n.RowId AND n.IsDel = 0
                LEFT JOIN DM_Khoa k ON n.Khoa = k.DepartmentID AND k.IsDel = 0
                WHERE s.StudentCode = @StudentCode 
                  AND s.Disabled = 0";

                // Mở kết nối và thực thi SQL
                using var connection = new SqlConnection(_connectionString);

                // Dapper tự động map các cột trong SQL với các thuộc tính của StudentDetailDto
                var student = await connection.QueryFirstOrDefaultAsync<StudentDetailDto>(
                    sqlQuery,
                    new { StudentCode = studentCode } // Truyền tham số để chống SQL Injection
                );

                // Kiểm tra kết quả và trả về Response
                if (student == null)
                {
                    return NotFound(new { Message = $"Không tìm thấy thông tin sinh viên mã: {studentCode}" });
                }

                return Ok(student);
            }
            catch (Exception ex)
            {
                return NotFound(new { Message = $"Không tìm thấy thông tin sinh viên mã: {studentCode}" });
            }
        }

        /// <summary>
        /// get danh sách các môn học đã đăng ký của sinh viên theo mã sinh viên (StudentCode)
        /// </summary>
        /// <param name="studentCode"></param>
        /// <returns></returns>
        [HttpGet("{studentCode}/courses")]
        public async Task<IActionResult> GetCourses(string studentCode)
        {
            if (string.IsNullOrWhiteSpace(studentCode))
            {
                return BadRequest(new { Message = "Mã sinh viên không được để trống." });
            }

            // Câu lệnh SQL JOIN từ Sinh viên -> Bảng điểm/Môn học học kỳ -> Học kỳ -> Môn học
            // Lọc sạch các dữ liệu đã bị xóa mềm (IsDel = 0 hoặc Disabled = 0)
            string sqlQuery = @"
            SELECT 
                hk.HocKyID, hk.MaHocKy, hk.TenHocKy, hk.NamHoc,
                mh.MonHocID, mh.MaMonHoc, mh.TenMonHoc, mh.SoTinChi
            FROM Tbl_Students s
            INNER JOIN Tbl_DiemSinhVien d ON s.StudentID = d.StudentID AND d.IsDel = 0
            INNER JOIN DM_HocKy hk ON d.HocKyID = hk.HocKyID AND hk.IsDel = 0
            INNER JOIN DM_MonHoc mh ON d.MonHocID = mh.MonHocID AND mh.IsDel = 0
            WHERE s.StudentCode = @StudentCode 
              AND s.Disabled = 0
            ORDER BY hk.NamHoc DESC, hk.SoThuTu DESC, mh.MaMonHoc ASC";

            using var connection = new SqlConnection(_connectionString);

            // 1. Chạy truy vấn lấy dữ liệu phẳng từ SQL
            var flatData = await connection.QueryAsync<StudentCourseFlatDto>(
                sqlQuery,
                new { StudentCode = studentCode }
            );

            if (flatData == null || !flatData.Any())
            {
                return NotFound(new { Message = $"Không tìm thấy danh sách môn học cho sinh viên mã: {studentCode}" });
            }

            // 2. Sử dụng LINQ để nhóm dữ liệu theo từng Học kỳ một cách tự động
            var groupedResult = flatData
                .GroupBy(x => new { x.HocKyID, x.MaHocKy, x.TenHocKy, x.NamHoc })
                .Select(g => new SemesterCoursesDto
                {
                    HocKyID = g.Key.HocKyID,
                    MaHocKy = g.Key.MaHocKy,
                    TenHocKy = g.Key.TenHocKy,
                    NamHoc = g.Key.NamHoc,
                    MonHocs = g.Select(c => new CourseDto
                    {
                        MonHocID = c.MonHocID,
                        MaMonHoc = c.MaMonHoc,
                        TenMonHoc = c.TenMonHoc,
                        SoTinChi = c.SoTinChi
                    }).ToList()
                })
                .ToList();

            // 3. Trả về kết quả đã gom nhóm đẹp đẽ cho Client
            return Ok(groupedResult);
        }

        /// <summary>
        /// Get điểm số của sinh viên theo mã sinh viên (StudentCode) và học kỳ (HocKyID)
        /// </summary>
        /// <param name="studentCode"></param>
        /// <param name="hocKyId"></param>
        /// <returns></returns>
        [HttpGet("{studentCode}/scores")]
        public async Task<IActionResult> GetScores(string studentCode, [FromQuery] int? hocKyId = null)
        {
            if (string.IsNullOrWhiteSpace(studentCode))
            {
                return BadRequest(new { Message = "Mã sinh viên không được để trống." });
            }

            // Câu lệnh SQL lấy điểm số kèm thông tin Môn học và Học kỳ
            // Xử lý filter học kỳ: Nếu @HocKyID truyền vào là NULL thì bỏ qua điều kiện lọc học kỳ
            string sqlQuery = @"
            SELECT 
                hk.HocKyID, hk.MaHocKy, hk.TenHocKy, hk.NamHoc,
                mh.MonHocID, mh.MaMonHoc, mh.TenMonHoc, mh.SoTinChi,
                d.DiemChuyenCan, d.DiemGiuaKy, d.DiemCuoiKy, d.DiemTongKet, d.DiemChu, d.Note AS GhiChu
            FROM Tbl_Students s
            INNER JOIN Tbl_DiemSinhVien d ON s.StudentID = d.StudentID AND d.IsDel = 0
            INNER JOIN DM_HocKy hk ON d.HocKyID = hk.HocKyID AND hk.IsDel = 0
            INNER JOIN DM_MonHoc mh ON d.MonHocID = mh.MonHocID AND mh.IsDel = 0
            WHERE s.StudentCode = @StudentCode 
              AND s.Disabled = 0
              AND (@HocKyID IS NULL OR hk.HocKyID = @HocKyID)
            ORDER BY hk.NamHoc DESC, hk.SoThuTu DESC, mh.MaMonHoc ASC";

            using var connection = new SqlConnection(_connectionString);

            // Thực thi query bằng Dapper
            var scores = await connection.QueryAsync<StudentScoreDto>(
                sqlQuery,
                new
                {
                    StudentCode = studentCode,
                    HocKyID = (hocKyId == 0 ? null : hocKyId) // Nếu client truyền lên là 0 thì coi như null để lấy tất cả
                }
            );

            if (scores == null || !scores.Any())
            {
                string msg = hocKyId.HasValue && hocKyId > 0
                    ? $"Không tìm thấy bảng điểm học kỳ {hocKyId} của sinh viên mã: {studentCode}"
                    : $"Không tìm thấy bảng điểm của sinh viên mã: {studentCode}";

                return NotFound(new { Message = msg });
            }

            return Ok(scores);
        }

        /// <summary>
        /// Get danh sách tất cả học kỳ
        /// </summary>
        /// <returns>Danh sách học kỳ sắp xếp theo năm học và thứ tự</returns>
        [HttpGet("semesters")]
        public async Task<IActionResult> GetSemesters()
        {
            string sqlQuery = @"
            SELECT 
                HocKyID, MaHocKy, TenHocKy, NamHoc, TuNgay, DenNgay, SoThuTu
            FROM DM_HocKy
            WHERE IsDel = 0
            ORDER BY NamHoc DESC, SoThuTu ASC";

            using var connection = new SqlConnection(_connectionString);

            var semesters = await connection.QueryAsync<HocKyDto>(sqlQuery);

            if (semesters == null || !semesters.Any())
            {
                return NotFound(new { Message = "Không tìm thấy danh sách học kỳ." });
            }

            return Ok(semesters);
        }

        /// <summary>
        /// Get danh sách tất cả môn học (có thể lọc theo khoa quản lý)
        /// </summary>
        /// <param name="khoaQuanLy">Mã khoa quản lý (tùy chọn)</param>
        /// <returns>Danh sách môn học</returns>
        [HttpGet("subjects")]
        public async Task<IActionResult> GetSubjects([FromQuery] int? khoaQuanLy = null)
        {
            string sqlQuery = @"
            SELECT 
                mh.MonHocID, mh.MaMonHoc, mh.TenMonHoc, mh.TenTiengAnh,
                mh.SoTinChi, mh.SoTietLyThuyet, mh.SoTietThucHanh,
                mh.KhoaQuanLy, k.Title AS KhoaQuanLyTitle
            FROM DM_MonHoc mh
            LEFT JOIN DM_Khoa k ON mh.KhoaQuanLy = k.DepartmentID AND k.IsDel = 0
            WHERE mh.IsDel = 0
              AND (@KhoaQuanLy IS NULL OR mh.KhoaQuanLy = @KhoaQuanLy)
            ORDER BY mh.MaMonHoc ASC";

            using var connection = new SqlConnection(_connectionString);

            var subjects = await connection.QueryAsync<MonHocDto>(
                sqlQuery,
                new { KhoaQuanLy = khoaQuanLy }
            );

            if (subjects == null || !subjects.Any())
            {
                string msg = khoaQuanLy.HasValue
                    ? $"Không tìm thấy môn học thuộc khoa mã: {khoaQuanLy}"
                    : "Không tìm thấy danh sách môn học.";

                return NotFound(new { Message = msg });
            }

            return Ok(subjects);
        }

        #region CLO - PLO
        /// <summary>
        /// 1. API Lấy danh sách PLO theo Ngành học
        /// </summary>
        [HttpGet("majors/{majorId}/plos")]
        public async Task<IActionResult> GetPlosByMajor(int majorId)
        {
            string sqlQuery = @"
            SELECT PLOID, NganhID, MaPLO, Title, Description 
            FROM DM_PLO 
            WHERE NganhID = @MajorId
            ORDER BY MaPLO ASC";

            using var connection = new SqlConnection(_connectionString);
            var plos = await connection.QueryAsync<PloDto>(sqlQuery, new { MajorId = majorId });

            if (plos == null || !plos.Any())
            {
                return NotFound(new { Message = $"Không tìm thấy chuẩn đầu ra PLO nào cho ngành có ID: {majorId}" });
            }

            return Ok(plos);
        }

        /// <summary>
        /// 2. API Lấy danh sách CLO theo Môn học
        /// </summary>
        [HttpGet("courses/{courseId}/clos")]
        public async Task<IActionResult> GetClosByCourse(int courseId)
        {
            string sqlQuery = @"
            SELECT CLOID, MonHocID, MaCLO, Title, Description 
            FROM DM_CLO 
            WHERE MonHocID = @CourseId
            ORDER BY MaCLO ASC";

            using var connection = new SqlConnection(_connectionString);
            var clos = await connection.QueryAsync<CloDto>(sqlQuery, new { CourseId = courseId });

            if (clos == null || !clos.Any())
            {
                return NotFound(new { Message = $"Không tìm thấy chuẩn đầu ra CLO nào cho môn học có ID: {courseId}" });
            }

            return Ok(clos);
        }

        /// <summary>
        /// 3. API Lấy cấu hình tỷ trọng Đánh giá CLO của môn học
        /// </summary>
        [HttpGet("courses/{courseId}/clo-evaluations")]
        public async Task<IActionResult> GetCloEvaluations(int courseId)
        {
            // SQL thực hiện JOIN giữa bảng trung gian, bảng CLO và bảng Hình thức đánh giá
            string sqlQuery = @"
            SELECT 
                cd.ID, cd.CLOID, c.MaCLO, c.Title AS CloTitle,
                cd.DanhGiaID, htdg.Code AS EvaluationCode, htdg.Title AS EvaluationTitle, 
                cd.TyLePhanTram
            FROM DM_CLO_DanhGia cd
            INNER JOIN DM_CLO c ON cd.CLOID = c.CLOID
            INNER JOIN DM_HinhThucDanhGia htdg ON cd.DanhGiaID = htdg.DanhGiaID
            WHERE c.MonHocID = @CourseId
            ORDER BY c.MaCLO ASC, htdg.Code ASC";

            using var connection = new SqlConnection(_connectionString);
            var evaluations = await connection.QueryAsync<CloEvaluationDto>(sqlQuery, new { CourseId = courseId });

            if (evaluations == null || !evaluations.Any())
            {
                return NotFound(new { Message = $"Môn học ID {courseId} chưa được cấu hình tỷ trọng điểm thành phần cho CLO." });
            }

            return Ok(evaluations);
        }

        /// <summary>
        /// 4. API Lấy Ma trận Mapping giữa CLO và PLO của môn học
        /// </summary>
        [HttpGet("courses/{courseId}/clo-plo-mapping")]
        public async Task<IActionResult> GetCloPloMapping(int courseId)
        {
            // SQL thực hiện JOIN 3 bảng: DM_CLO_PLO, DM_CLO, DM_PLO để lấy ra ma trận đóng góp đầy đủ thông tin tên/mã chuẩn đầu ra
            string sqlQuery = @"
            SELECT 
                cp.ID, cp.CLOID, c.MaCLO, c.Title AS CloTitle,
                cp.PLOID, p.MaPLO, p.Title AS PloTitle, 
                cp.MucDoDongGop
            FROM DM_CLO_PLO cp
            INNER JOIN DM_CLO c ON cp.CLOID = c.CLOID
            INNER JOIN DM_PLO p ON cp.PLOID = p.PLOID
            WHERE c.MonHocID = @CourseId
            ORDER BY c.MaCLO ASC, p.MaPLO ASC";

            using var connection = new SqlConnection(_connectionString);
            var mappings = await connection.QueryAsync<CloPloMappingDto>(sqlQuery, new { CourseId = courseId });

            if (mappings == null || !mappings.Any())
            {
                return NotFound(new { Message = $"Môn học ID {courseId} chưa được cấu hình ma trận đóng góp CLO -> PLO." });
            }

            return Ok(mappings);
        }
        #endregion
    }
}
