import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage 
from langgraph.graph.message import add_messages 

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence
import operator
from pydantic import BaseModel, Field

# Import các Tool y hệt như file cũ
from rag_tools import tra_cuu_quy_che
from form_tools import lay_link_bieu_mau
from api_tools import (
    tra_cuu_thong_tin_sinh_vien,
    tra_cuu_diem_sinh_vien,
    tra_cuu_mon_hoc_da_dang_ky,
    lay_danh_sach_hoc_ky,
    lay_danh_muc_mon_hoc
)

SUPERVISOR_PROMPT = """Bạn là TỔNG ĐIỀU PHỐI (Supervisor) của một hệ thống Đa Đặc Vụ. Nhiệm vụ duy nhất của bạn là phân loại câu hỏi và CHỈ ĐỊNH ĐẶC VỤ TIẾP THEO dựa trên quy tắc ƯU TIÊN nghiêm ngặt sau:

1. ƯU TIÊN 1 (Nhóm Tri thức tĩnh - AcademicAgent):
- Trigger khi câu hỏi có các từ khóa: 'trường', 'giới thiệu', 'lịch sử', 'quy chế', 'biểu mẫu', 'mẫu đơn', 'học phí', 'ngành', 'khoa'.
- Lưu ý: Kể cả khi câu hỏi có kèm mã sinh viên, VẪN PHẢI chuyển cho AcademicAgent.

2. ƯU TIÊN 2 (Nhóm Dữ liệu động cá nhân - StudentServiceAgent):
- Trigger khi câu hỏi xoay quanh việc tra cứu dữ liệu cá nhân của người dùng: 'điểm', 'môn học đã đăng ký', 'TKB', 'số học kỳ', 'đã học mấy học kỳ', 'thông tin của tôi'.

3. TRƯỜNG HỢP KẾT THÚC (FINISH):
- CHỈ chọn FINISH khi người dùng chào hỏi giao tiếp cơ bản, HOẶC khi câu hỏi đã được một Agent khác trả lời đầy đủ thông tin.
- TUYỆT ĐỐI KHÔNG chọn FINISH ngay lượt đầu tiên khi người dùng vừa đặt câu hỏi chuyên môn."""

# ==========================================
# CẤU HÌNH LLM (OLLAMA /v1 ENDPOINT)
# ==========================================
# Thay bằng API Key và tên Model chính xác mà bạn đang host trên Ollama
OLLAMA_API_KEY = "42efac7dac9a4e0a8fb204bc1e444220.TYKmGIaCks2Rt2bRZrWUOKhI" 
OLLAMA_MODEL_NAME = "kimi-k2.6" # Ví dụ: llama3.1, llama3, qwen2...

llm = ChatOpenAI(
    base_url="https://ollama.com/v1",
    api_key=OLLAMA_API_KEY,
    model=OLLAMA_MODEL_NAME,
    temperature=0 # Để 0 để Agent tư duy logic, không bịa chuyện
)

# ==========================================================
# PHẦN 1: ĐỊNH NGHĨA TRẠNG THÁI (STATE) & CÁC ĐẶC VỤ (AGENTS)
# ==========================================================
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    next_agent: str

# KHẮC PHỤC LỖI: Bọc Agent của Llama bằng create_react_agent giống hệt Gemini/GPT
from langgraph.prebuilt import create_react_agent

academic_tools = [tra_cuu_quy_che, lay_link_bieu_mau]
academic_agent = create_react_agent(
    llm, 
    tools=academic_tools, 
    prompt="Bạn là Chuyên viên Học vụ. Nhiệm vụ của bạn là tư vấn quy chế, các thông tin về trường học, ngành đào đạo, khoa đào tạo và cấp link biểu mẫu. Không được trả lời các câu hỏi về điểm số và thời khóa biểu, thông tin cá nhân của sinh viên."
)

student_tools = [
    tra_cuu_thong_tin_sinh_vien, tra_cuu_mon_hoc_da_dang_ky, 
    tra_cuu_diem_sinh_vien, lay_danh_sach_hoc_ky, lay_danh_muc_mon_hoc
]
student_service_agent = create_react_agent(
    llm, 
    tools=student_tools, 
    prompt="Bạn là Chuyên viên Quản lý Sinh viên. Nhiệm vụ của bạn là tra cứu điểm số, môn học, thời khóa biểu và dữ liệu cá nhân qua hệ thống API. Tuyệt đối chỉ trả lời dựa trên dữ liệu API trả về, không được tự ý bịa đặt thông tin. Không được trả lời các câu hỏi về quy chế, lịch sử trường hay biểu mẫu."
)

# ==========================================================
# PHẦN 2: ĐỊNH NGHĨA CÁC NÚT (NODES) TRONG ĐỒ THỊ
# ==========================================================
def supervisor_node(state: AgentState):
    """Lễ tân đọc hội thoại (Cơ chế Parse chuỗi an toàn cho Llama)"""
    # Ép Llama chỉ trả lời 1 từ
    system_prompt = SUPERVISOR_PROMPT + "\n\nQUAN TRỌNG: BẠN CHỈ ĐƯỢC PHÉP TRẢ LỜI ĐÚNG 1 TỪ DUY NHẤT LÀ TÊN CỦA AGENT (AcademicAgent, StudentServiceAgent, hoặc FINISH). KHÔNG GIẢI THÍCH."
    
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = llm.invoke(messages)
    
    raw_output = response.content.strip().replace('"', '').replace("'", "")
    
    next_agent = "AcademicAgent" # Fallback an toàn
    if "StudentServiceAgent" in raw_output:
        next_agent = "StudentServiceAgent"
    elif "FINISH" in raw_output:
        next_agent = "FINISH"
    elif "AcademicAgent" in raw_output:
        next_agent = "AcademicAgent"
        
    return {"next_agent": next_agent}

def academic_node(state: AgentState):
    result = academic_agent.invoke({"messages": state["messages"]})
    return {"messages": result["messages"][len(state["messages"]):]}

def student_service_node(state: AgentState):
    result = student_service_agent.invoke({"messages": state["messages"]})
    return {"messages": result["messages"][len(state["messages"]):]}

# ==========================================
# 5. XÂY DỰNG ĐỒ THỊ LANGGRAPH
# ==========================================
workflow = StateGraph(AgentState)

workflow.add_node("Supervisor", supervisor_node)
workflow.add_node("AcademicAgent", academic_node)
workflow.add_node("StudentServiceAgent", student_service_node)

workflow.set_entry_point("Supervisor")

# Cấu hình Routing
def route(state):
    # Lấy thông tin định tuyến từ Supervisor
    # Vì Supervisor không sinh ra message mới, ta lưu state ngầm (ở bản này LangGraph tự hiểu)
    pass 
    # Do đồ thị StateGraph cần rẽ nhánh, ta sẽ dùng cơ chế conditional_edges
    
workflow.add_conditional_edges(
    "Supervisor",
    lambda state: supervisor_node(state)["next_agent"], # Hàm lấy kết quả route
    {
        "AcademicAgent": "AcademicAgent",
        "StudentServiceAgent": "StudentServiceAgent",
        "FINISH": END
    }
)

# Sau khi Agent chạy xong, quay lại Supervisor để check xem cần chạy tiếp không
workflow.add_edge("AcademicAgent", "Supervisor")
workflow.add_edge("StudentServiceAgent", "Supervisor")

app = workflow.compile()