# UniAdvisorAI 🎓

> **Hệ thống Cố vấn Học vụ Thông minh** dành cho sinh viên đại học — kết hợp **Multi-Agent AI** và **RAG** để giải đáp mọi thắc mắc tức thì.

---

## Tổng quan

UniAdvisorAI tự động phân loại và xử lý hai nhóm câu hỏi:

| Loại câu hỏi | Ví dụ | Xử lý bằng |
|---|---|---|
| 📄 **Dữ liệu tĩnh** | Quy chế đào tạo, biểu mẫu, chuẩn kỹ năng | RAG từ tài liệu PDF/Markdown |
| ⚡ **Dữ liệu động** | Điểm số, thời khóa biểu, môn đăng ký | Gọi Backend API thời gian thực |

---

## Kiến trúc Hệ thống

```
Người dùng (Streamlit UI)
        │
        ▼
  Supervisor Agent ─── phân tích & định tuyến
        │
   ┌────┴────┐
   ▼         ▼
Academic   StudentService
 Agent       Agent
   │           │
 RAG từ    Gọi REST
 PDF/MD     API (.NET)
                │
            SQL Server
```

### Backend Web API — `APISinhVien`
- **Công nghệ:** ASP.NET Core 8.0, Entity Framework Core, SQL Server
- **Chức năng:** Cung cấp các endpoint RESTful để truy vấn thông tin sinh viên, điểm số, thời khóa biểu, học kỳ, danh mục môn học
- 📖 [Xem tài liệu API](APISinhVien/API_SinhVien/api_documentation.md)

### Multi-Agent Dashboard — `MultiAgent`
- **Công nghệ:** Python 3.10+, Streamlit, LangChain, LangGraph
- **Các Agent:**
  - **Supervisor Agent** — tiếp nhận câu hỏi, định tuyến đến agent phù hợp
  - **AcademicAgent** — tra cứu quy chế, biểu mẫu hành chính qua RAG
  - **StudentServiceAgent** — tra cứu dữ liệu cá nhân sinh viên qua API
- **Mô hình LLM hỗ trợ:** GPT-4o, Gemini, Llama (OpenAI-compatible)

---

## Cấu trúc Thư mục

```text
UniAdvisorAI/
├── DB_SinhVien.bak                      # Backup cơ sở dữ liệu SQL Server
├── mo_ta_database_quan_ly_dao_tao.md    # Tài liệu thiết kế database
│
├── APISinhVien/                         # Backend Web API (.NET Core)
│   └── API_SinhVien/
│       ├── Controllers/                 # Xử lý các endpoint API
│       ├── DTO/                         # Data Transfer Objects
│       ├── Program.cs                   # Cấu hình & khởi chạy API
│       ├── appsettings.json             # Connection string & cổng chạy
│       └── api_documentation.md        # Tài liệu endpoint API
│
└── MultiAgent/                          # Ứng dụng AI (Python & Streamlit)
    ├── app.py                           # Giao diện Streamlit
    ├── multi_agent_gpt.py               # LangGraph với GPT
    ├── multi_agent_gmi.py               # LangGraph với Gemini
    ├── multi_agent_llama.py             # LangGraph với Llama
    ├── api_tools.py                     # Công cụ gọi Backend API
    ├── form_tools.py                    # Công cụ lấy link biểu mẫu
    ├── rag_tools.py                     # Công cụ tìm kiếm quy chế
    ├── pdf_to_markdown.py               # Chuyển đổi PDF → Markdown
    ├── TransformData.py                 # Nhúng dữ liệu vào Vector DB
    ├── chroma_db/                       # Vector database (ChromaDB)
    ├── data_TienXuLy/                   # File PDF quy chế gốc
    └── data_markdown/                   # File quy chế dạng Markdown
```

---

## Cài đặt & Chạy

### Bước 1 — Khôi phục Database

1. Mở **SQL Server Management Studio (SSMS)**
2. Chuột phải vào **Databases** → **Restore Database...**
3. Chọn **Device** → trỏ đến file `DB_SinhVien.bak` trong thư mục gốc
4. Restore thành công với tên database là `DB_SinhVien`

---

### Bước 2 — Khởi chạy Backend API

> **Yêu cầu:** [.NET SDK 8.0](https://dotnet.microsoft.com/download/dotnet/8.0)

```bash
cd APISinhVien/API_SinhVien
dotnet restore
dotnet run
```

Cập nhật **Connection String** trong `appsettings.json` trước khi chạy:

```json
"ConnectionStrings": {
  "DefaultConnection": "Server=YOUR_SERVER_NAME;Database=DB_SinhVien;Trusted_Connection=True;TrustServerCertificate=True;"
}
```

> **Lưu ý:** API mặc định chạy tại `http://localhost:5087/api` hoặc `https://localhost:44326/api`.

---

### Bước 3 — Khởi chạy Multi-Agent Dashboard

> **Yêu cầu:** Python 3.10+

```bash
cd MultiAgent
pip install -r requirements.txt
```

Tạo file `.env` trong thư mục `MultiAgent` và điền API key:

```env
OPENAI_API_KEY=sk-proj-...
GOOGLE_API_KEY=AIzaSy...
```

Khởi chạy ứng dụng:

```bash
streamlit run app.py
```

Truy cập giao diện tại: **http://localhost:8501**

---

## Dùng thử

Đăng nhập bằng Mã số sinh viên hợp lệ trong DB, sau đó đặt câu hỏi:

- 🎓 **Hỏi quy chế:** *"Quy định về chuẩn đầu ra ngoại ngữ của trường thế nào?"*
- 📋 **Lấy biểu mẫu:** *"Cho mình xin link biểu mẫu xin bảng điểm học tập"*
- 📊 **Tra cứu cá nhân:** *"Học kỳ này mình đăng ký những môn học nào?"*
- 🔢 **Tính điểm:** *"Tính GPA trung bình học kỳ 1 năm 2023-2024 của mình"*

> Hệ thống tự động chuyển giao nhiệm vụ giữa các agent mà không mất ngữ cảnh hội thoại.

---

## Lưu ý khi Đóng góp

- Không commit file build C# (`bin/`, `obj/`, `.vs/`) và file Python compile (`__pycache__/`)
- Không commit file `.env` chứa API key
- Chạy `git status` trước khi commit để kiểm tra file không mong muốn
