# UniAdvisorAI - Cố vấn Học vụ Sinh viên Thông minh 🎓

**UniAdvisorAI** là một hệ thống hỗ trợ cố vấn học vụ thông minh dành cho sinh viên đại học. Hệ thống kết hợp giữa **Cơ sở dữ liệu Đào tạo** (được cung cấp qua Backend Web API viết bằng ASP.NET Core) và **Kiến trúc Đa Đặc vụ (Multi-Agent System)** tích hợp RAG (được viết bằng Python, LangChain, LangGraph và Streamlit) để giải đáp mọi thắc mắc của sinh viên một cách nhanh chóng, chính xác.

Hệ thống có khả năng phân biệt và xử lý hai nhóm câu hỏi chính:
1. **Dữ liệu tĩnh:** Quy chế đào tạo, chuẩn kỹ năng CNTT/Ngoại ngữ, các mẫu đơn, biểu mẫu, quy trình hành chính (Sử dụng kỹ thuật RAG từ tài liệu chính thức).
2. **Dữ liệu động:** Tra cứu điểm số cá nhân, thời khóa biểu, thông tin đăng ký môn học, danh sách học kỳ, chương trình đào tạo của từng sinh viên (Truy vấn qua Backend API thời gian thực).

---

## 🏗️ Kiến trúc Hệ thống

Hệ thống gồm 2 thành phần hoạt động song song:

```mermaid
graph TD
    User([Sinh viên / Người dùng]) -->|Đăng nhập & Trò chuyện| UI[Streamlit Frontend Dashboard]
    
    subgraph Multi-Agent System (LangGraph)
        UI --> Supervisor{Supervisor Agent <br> Bộ điều phối}
        Supervisor -->|Phân loại & Định tuyến| AcademicAgent[Academic Agent <br> Chuyên viên Học vụ]
        Supervisor -->|Phân loại & Định tuyến| StudentAgent[Student Service Agent <br> Chuyên viên Quản lý Sinh viên]
        
        AcademicAgent -->|RAG Search| VectorDB[(Chroma Vector DB)]
        AcademicAgent -->|Cấp link| FormTool[Form Tools <br> Danh mục Biểu mẫu]
        
        StudentAgent -->|Query API| API_Client[API Tools <br> Gọi HTTP Requests]
    end
    
    subgraph Backend Services (.NET)
        API_Client -->|HTTPS REST| WebAPI[ASP.NET Core Web API]
        WebAPI -->|SQL Query| SQLServer[(SQL Server Database)]
    end
    
    VectorDB -.->|Đọc dữ liệu học vụ tĩnh| MD_Files[Tài liệu Markdown]
```

### 1. Backend Web API (`APISinhVien`)
- **Công nghệ:** ASP.NET Core 8.0, Entity Framework Core.
- **Cơ sở dữ liệu:** SQL Server.
- **Nhiệm vụ:** Cung cấp các endpoint RESTful an toàn để truy vấn thông tin sinh viên, điểm số, thời khóa biểu, học kỳ và danh mục môn học. Xem tài liệu API tại: [api_documentation.md](file:///d:/Projects/UniAdvisorAI/APISinhVien/API_SinhVien/api_documentation.md).

### 2. Multi-Agent Dashboard (`MultiAgent`)
- **Công nghệ:** Python 3.10+, Streamlit, LangChain, LangGraph.
- **Đồ thị Đặc vụ (LangGraph):**
  - **Supervisor Agent (Bộ điều phối):** Tiếp nhận câu hỏi từ sinh viên, phân tích ý định và định tuyến đến đặc vụ phù hợp nhất hoặc quyết định kết thúc cuộc hội thoại (`FINISH`).
  - **AcademicAgent (Đặc vụ Học vụ):** Chịu trách nhiệm về thông tin chung và quy chế. Sử dụng RAG để đọc dữ liệu từ các file PDF/Markdown quy chế học vụ và trả về link biểu mẫu hành chính.
  - **StudentServiceAgent (Đặc vụ Quản lý Sinh viên):** Chịu trách nhiệm tra cứu dữ liệu cá nhân của sinh viên đang đăng nhập thông qua việc gọi các Web API Backend.
- **Mô hình hỗ trợ:** GPT-4o (hoặc GPT-3.5/GPT-4), Gemini (qua `ChatGoogleGenerativeAI`), và Llama (qua endpoint tương thích OpenAI/Ollama).

---

## 📂 Cấu trúc Thư mục Dự án

```text
UniAdvisorAI/
├── .gitignore                    # Quản lý file tạm thời và môi trường
├── DB_SinhVien.bak               # File backup Cơ sở dữ liệu SQL Server
├── mo_ta_database_quan_ly_dao_tao.md # Tài liệu thiết kế cơ sở dữ liệu chi tiết
│
├── APISinhVien/                  # Dự án Backend Web API (.NET Core)
│   ├── APISinhVien.sln           # Solution file của Visual Studio
│   └── API_SinhVien/             # Mã nguồn chính của API
│       ├── Controllers/          # Xử lý các endpoint API (StudentsController, v.v.)
│       ├── DTO/                  # Data Transfer Objects định nghĩa cấu trúc trả về
│       ├── Program.cs            # Cấu hình dịch vụ và khởi chạy API
│       ├── appsettings.json      # Cấu hình chuỗi kết nối Database và cổng chạy
│       └── api_documentation.md  # Tài liệu mô tả chi tiết các endpoint API
│
└── MultiAgent/                   # Dự án Đa Đặc vụ AI (Python & Streamlit)
    ├── app.py                    # Giao diện chính Streamlit Dashboard
    ├── multi_agent_gpt.py        # Cấu hình luồng LangGraph sử dụng mô hình GPT
    ├── multi_agent_gmi.py        # Cấu hình luồng LangGraph sử dụng mô hình Gemini
    ├── multi_agent_llama.py      # Cấu hình luồng LangGraph sử dụng mô hình Llama
    ├── api_tools.py              # Các công cụ gọi API Backend lấy dữ liệu động
    ├── form_tools.py             # Công cụ lấy link biểu mẫu hành chính
    ├── rag_tools.py              # Công cụ tìm kiếm văn bản quy chế đào tạo
    ├── pdf_to_markdown.py        # Script tiền xử lý chuyển đổi PDF quy chế sang Markdown
    ├── TransformData.py          # Script chunking và nhúng dữ liệu vào Vector DB
    ├── chroma_db/                # Cơ sở dữ liệu vector lưu trữ tài liệu đã được nhúng
    ├── data_TienXuLy/            # Thư mục chứa các tệp PDF quy chế gốc
    └── data_markdown/            # Thư mục chứa các tệp quy chế định dạng Markdown
```

---

## 🚀 Hướng dẫn Cài đặt & Chạy Hệ thống

### Bước 1: Khôi phục Cơ sở dữ liệu (Database Setup)
1. Mở **SQL Server Management Studio (SSMS)**.
2. Nhấp chuột phải vào mục **Databases** -> chọn **Restore Database...**
3. Chọn **Device** -> chọn đường dẫn tới file [`DB_SinhVien.bak`](file:///d:/Projects/UniAdvisorAI/DB_SinhVien.bak) nằm trong thư mục gốc dự án.
4. Thực hiện Restore database thành công dưới tên `DB_SinhVien`.

### Bước 2: Khởi chạy Backend Web API
1. Đảm bảo bạn đã cài đặt [.NET SDK 8.0](https://dotnet.microsoft.com/download/dotnet/8.0).
2. Di chuyển vào thư mục dự án API:
   ```bash
   cd APISinhVien/API_SinhVien
   ```
3. Cập nhật chuỗi kết nối cơ sở dữ liệu (Connection String) trong tệp [`appsettings.json`](file:///d:/Projects/UniAdvisorAI/APISinhVien/API_SinhVien/appsettings.json) để trỏ đúng về SQL Server cục bộ của bạn:
   ```json
   "ConnectionStrings": {
     "DefaultConnection": "Server=YOUR_SERVER_NAME;Database=DB_SinhVien;Trusted_Connection=True;TrustServerCertificate=True;"
   }
   ```
4. Chạy lệnh phục hồi thư viện và khởi chạy API:
   ```bash
   dotnet restore
   dotnet run
   ```
   *Lưu ý:* Ghi lại cổng (Port) mà API đang lắng nghe (mặc định trong code Frontend đang cấu hình cổng `https://localhost:44326/api` hoặc `http://localhost:5087/api`).

### Bước 3: Thiết lập Multi-Agent Dashboard (Frontend)
1. Đảm bảo bạn đã cài đặt **Python 3.10+**.
2. Di chuyển vào thư mục `MultiAgent`:
   ```bash
   cd MultiAgent
   ```
3. Cài đặt các thư viện Python cần thiết:
   ```bash
   pip install -r requirements.txt
   ```
   *(Các thư viện chính bao gồm: `streamlit`, `langchain`, `langgraph`, `chromadb`, `langchain-openai`, `langchain-google-genai`, `requests`)*
4. Cấu hình biến môi trường chứa API Key của các dịch vụ LLM:
   Tạo tệp `.env` trong thư mục `MultiAgent` và điền khóa của bạn:
   ```env
   OPENAI_API_KEY=sk-proj-...
   GOOGLE_API_KEY=AIzaSy...
   ```
5. Khởi chạy ứng dụng Streamlit:
   ```bash
   streamlit run app.py
   ```
6. Truy cập vào giao diện web theo đường dẫn cục bộ hiển thị trên terminal (thường là `http://localhost:8501`).

---

## 💡 Hướng dẫn Trò chuyện thử nghiệm

1. Đăng nhập vào Dashboard bằng một Mã số sinh viên hợp lệ tồn tại trong DB (ví dụ: `SV12345`).
2. Trải nghiệm hệ thống bằng cách đặt các câu hỏi:
   - **Hỏi quy chế (Academic Agent):** *"Cho mình xin link biểu mẫu xin bảng điểm học tập"* hoặc *"Quy định về chuẩn đầu ra ngoại ngữ của trường thế nào?"*.
   - **Hỏi thông tin cá nhân (Student Service Agent):** *"Học kỳ này mình đăng ký những môn học nào?"* hoặc *"Tính điểm GPA trung bình học kỳ 1 năm học 2023-2024 của mình"*.
   - **Trò chuyện linh hoạt:** Hệ thống sẽ tự động phối hợp chuyển giao nhiệm vụ giữa các đặc vụ mà không làm đứt đoạn hay mất ngữ cảnh cuộc nói chuyện.

---

## 🧹 Quy chuẩn Phát triển & Đóng góp
- Để đảm bảo dự án sạch sẽ, không commit các file tạm hay các thư viện đã build lên Git:
  - Thư mục C# build (`bin/`, `obj/`, `.vs/`) đã được định cấu hình loại bỏ trong `.gitignore`.
  - Thư mục Python compile (`__pycache__/`, `.env`) cũng được bỏ qua hoàn toàn.
  - Vui lòng chạy lệnh `git status` trước khi thực hiện commit để kiểm tra các file rác không mong muốn.
