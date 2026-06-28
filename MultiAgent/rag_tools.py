from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_core.tools import tool
import time

# Kết nối sẵn vào kho ChromaDB
# embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",
    api_key=""
)
vector_db = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

@tool
def tra_cuu_quy_che(tu_khoa: str) -> str:
    """
    Dùng để tra cứu toàn bộ cơ sở tri thức tĩnh của trường học.
    Hãy gọi công cụ này khi câu hỏi liên quan đến:
    - Quy chế, quy định đào tạo, thủ tục học vụ, học phí.
    - Thông tin tổng quan, lịch sử, giới thiệu về trường, các ngành học, các khoa.
    """
    time.sleep(5)
    # print(f"\n[🔧 Tool RAG] -> Đang đọc quy chế tìm thông tin: '{tu_khoa}'...")
    docs = vector_db.similarity_search(tu_khoa, k=3)
    
    if not docs:
        return "Không tìm thấy thông tin nào trong quy chế."
        
    return "\n\n".join([doc.page_content for doc in docs])