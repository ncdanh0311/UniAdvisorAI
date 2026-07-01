import os
import time
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

# 1. Cấu hình API Key của Gemini
os.environ["GOOGLE_API_KEY"] = "".strip()

def tao_kho_du_lieu_vector():
    print("1. Đang quét và đọc TẤT CẢ các file Markdown (.md) trong thư mục './data_markdown'...")
    
    # Sử dụng DirectoryLoader để đọc file .md với chuẩn utf-8
    loader = DirectoryLoader(
        "./data_markdown", 
        glob="*.md", 
        loader_cls=TextLoader, 
        loader_kwargs={'encoding': 'utf-8'}
    )
    documents = loader.load()
    
    print(f"   -> Đã đọc tổng cộng {len(documents)} file tài liệu.")

    if len(documents) == 0:
        print("❌ LỖI: Không tìm thấy file .md nào! Hãy chạy file 1_pdf_to_markdown.py trước!")
        return

    print("2. Đang cắt nhỏ văn bản (Chunking)...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(documents)
    print(f"   -> Đã băm nhỏ thành {len(chunks)} đoạn (chunks).")

    print("3. Đang gửi dữ liệu lên Gemini để tạo Vector và lưu cục bộ vào ChromaDB...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    vector_db = Chroma(embedding_function=embeddings, persist_directory="./chroma_db")
    
    # CHIA LÔ (BATCHING) SIÊU CHẬM ĐỂ LÁCH LUẬT FREE TIER
    batch_size = 5 
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        print(f"   -> Đang đẩy lô dữ liệu từ {i} đến {i + len(batch)}...")
        
        vector_db.add_documents(batch)
        
        if i + batch_size < len(chunks):
            print("      (Đang ngủ 25 giây để hồi Quota API của Google...)")
            time.sleep(25)
            
    print("✅ HOÀN TẤT! Toàn bộ tri thức đã được số hóa và lưu vào ./chroma_db")

if __name__ == "__main__":
    tao_kho_du_lieu_vector()