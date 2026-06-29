import os
import glob
from llama_parse import LlamaParse

# 1. Điền API Key của LlamaCloud vào đây (Bắt đầu bằng chữ llx-...)
os.environ["LLAMA_CLOUD_API_KEY"] = "llx-0reZT4Dk6A2sQwn2uzZAyhy5vF7KjrGubYOpH4pFdy18iaMv"

def convert_all_pdfs_to_markdown():
    # Thư mục chứa PDF gốc và thư mục lưu Markdown
    thu_muc_pdf = "./data_TienXuLy"
    thu_muc_md = "./data_markdown"
    
    # Tạo thư mục lưu MD nếu chưa có
    if not os.path.exists(thu_muc_md):
        os.makedirs(thu_muc_md)
        
    # Lấy danh sách tất cả file PDF
    pdf_files = glob.glob(os.path.join(thu_muc_pdf, "*.pdf"))
    print(f"🔍 Tìm thấy {len(pdf_files)} file PDF cần xử lý...\n")

    # 2. Khởi tạo Cỗ máy LlamaParse
    parser = LlamaParse(
        result_type="markdown", # Bắt buộc xuất ra Markdown
        verbose=True,
        language="vi" # Ưu tiên nhận diện tiếng Việt
    )

    # 3. Lặp qua từng file và xử lý
    for pdf_file in pdf_files:
        print(f"⏳ Đang dùng AI phân tích file: {os.path.basename(pdf_file)} ...")
        
        # Đổi đuôi .pdf thành .md
        ten_file_md = os.path.basename(pdf_file).replace(".pdf", ".md")
        duong_dan_md = os.path.join(thu_muc_md, ten_file_md)
        
        try:
            # Gửi lên LlamaCloud để bóc tách
            tai_lieu = parser.load_data(pdf_file)
            
            # Nối tất cả các trang lại thành 1 chuỗi văn bản dài
            noi_dung_md = "\n\n".join([trang.text for trang in tai_lieu])
            
            # Lưu ra file .md
            with open(duong_dan_md, "w", encoding="utf-8") as f:
                f.write(noi_dung_md)
                
            print(f"   ✅ Đã lưu thành công: {duong_dan_md}\n")
            
        except Exception as e:
            print(f"   ❌ LỖI khi xử lý {pdf_file}: {e}\n")
            
    print("🎉 HOÀN TẤT QUÁ TRÌNH TIỀN XỬ LÝ DỮ LIỆU!")

if __name__ == "__main__":
    convert_all_pdfs_to_markdown()