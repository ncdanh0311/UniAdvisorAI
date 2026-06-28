import os
from typing import Annotated, Literal, TypedDict
from pydantic import BaseModel, Field

from langchain_core.messages import HumanMessage, BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent

# 1. Import toàn bộ 7 Tools từ 3 file của bạn
from api_tools import (
    tra_cuu_thong_tin_sinh_vien,
    tra_cuu_mon_hoc_da_dang_ky,
    tra_cuu_diem_sinh_vien,
    lay_danh_sach_hoc_ky,
    lay_danh_muc_mon_hoc,
)
from form_tools import lay_link_bieu_mau
from rag_tools import tra_cuu_quy_che

SUPERVISOR_PROMPT = """Bạn là TỔNG ĐIỀU PHỐI (Supervisor) của một hệ thống Đa Đặc Vụ. Nhiệm vụ duy nhất của bạn là phân loại câu hỏi và CHỈ ĐỊNH ĐẶC VỤ TIẾP THEO dựa trên quy tắc ƯU TIÊN nghiêm ngặt sau:

1. ƯU TIÊN 1 (Nhóm Tri thức tĩnh - AcademicAgent):
- Trigger khi câu hỏi có các từ khóa: 'trường', 'giới thiệu', 'lịch sử', 'quy chế', 'biểu mẫu', 'mẫu đơn', 'học phí', 'ngành', 'khoa'.
- Lưu ý: Kể cả khi câu hỏi có kèm mã sinh viên, VẪN PHẢI chuyển cho AcademicAgent.

2. ƯU TIÊN 2 (Nhóm Dữ liệu động cá nhân - StudentServiceAgent):
- Trigger khi câu hỏi xoay quanh việc tra cứu dữ liệu cá nhân của người dùng: 'điểm', 'môn học đã đăng ký', 'TKB', 'số học kỳ', 'đã học mấy học kỳ', 'thông tin của tôi'.

3. TRƯỜNG HỢP KẾT THÚC (FINISH):
- CHỈ chọn FINISH khi người dùng chào hỏi giao tiếp cơ bản, HOẶC khi câu hỏi đã được một Agent khác trả lời đầy đủ thông tin.
- TUYỆT ĐỐI KHÔNG chọn FINISH ngay lượt đầu tiên khi người dùng vừa đặt câu hỏi chuyên môn."""

# Cấu hình API Key (Lưu ý: Nên dùng file .env trong thực tế)
# os.environ["GOOGLE_API_KEY"] = .strip()

# Khởi tạo Mô hình LLM (Bộ não chính)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,        # Tính sáng tạo (0.0 đến 2.0)
    top_p=0.9,
    google_api_key=""
)

# ==========================================================
# PHẦN 1: ĐỊNH NGHĨA TRẠNG THÁI (STATE) & CÁC ĐẶC VỤ (AGENTS)
# ==========================================================

# Trạng thái hệ thống lưu trữ toàn bộ lịch sử chat
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    next_agent: str # Biến lưu tên Agent tiếp theo sẽ xử lý

# Định nghĩa cấu trúc quyết định cho Lễ tân (Supervisor)
class RouteResponse(BaseModel):
    next_agent: Literal["AcademicAgent", "StudentServiceAgent", "FINISH"] = Field(
        description="Chọn Agent tiếp theo để xử lý, hoặc FINISH nếu đã hoàn thành trả lời."
    )

# Khởi tạo 2 Agent chuyên viên bằng create_react_agent (tích hợp sẵn vòng lặp Thought-Action)
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
    """Lễ tân điều phối (Ép kiểu JSON cho Gemini/GPT)"""
    supervisor_chain = llm.with_structured_output(RouteResponse)
    messages = [{"role": "system", "content": SUPERVISOR_PROMPT}] + state["messages"]
    response = supervisor_chain.invoke(messages)
    return {"next_agent": response.next_agent}

def academic_node(state: AgentState):
    """Hàm chạy Academic Agent (Đã đồng bộ chống mất Context)"""
    result = academic_agent.invoke({"messages": state["messages"]})
    return {"messages": result["messages"][len(state["messages"]):]}

def student_service_node(state: AgentState):
    """Hàm chạy Student Service Agent (Đã đồng bộ chống mất Context)"""
    result = student_service_agent.invoke({"messages": state["messages"]})
    return {"messages": result["messages"][len(state["messages"]):]}

# ==========================================================
# PHẦN 3: XÂY DỰNG ĐỒ THỊ (BUILD GRAPH)
# ==========================================================

workflow = StateGraph(AgentState)

# Thêm các nút
workflow.add_node("Supervisor", supervisor_node)
workflow.add_node("AcademicAgent", academic_node)
workflow.add_node("StudentServiceAgent", student_service_node)

# Thiết lập đường đi (Edges)
workflow.add_edge(START, "Supervisor")

# Định tuyến (Conditional Edges) từ Supervisor
workflow.add_conditional_edges(
    "Supervisor",
    lambda state: state["next_agent"], # Lấy biến next_agent ra làm điều kiện rẽ nhánh
    {
        "AcademicAgent": "AcademicAgent",
        "StudentServiceAgent": "StudentServiceAgent",
        "FINISH": END # Nếu FINISH thì kết thúc đồ thị
    }
)

# Sau khi các chuyên viên làm xong, trả kết quả về lại cho Supervisor kiểm tra
workflow.add_edge("AcademicAgent", "Supervisor")
workflow.add_edge("StudentServiceAgent", "Supervisor")

# Biên dịch đồ thị
app = workflow.compile()

# ==========================================================
# PHẦN 4: HÀM TEST CHẠY THỰC TẾ
# ==========================================================
if __name__ == "__main__":
    # print("========================================")
    # print("🤖 HỆ THỐNG AGENTIC RAG ĐÃ SẴN SÀNG")
    # print("========================================\n")
    
    # Sinh viên đặt câu hỏi kết hợp cả quy chế lẫn thông tin cá nhân
    cau_hoi = "Câu hỏi input đầu vào?"
    
    # print(f"👤 Sinh viên: {cau_hoi}\n")
    
    # Chạy đồ thị
    inputs = {"messages": [HumanMessage(content=cau_hoi)]}
    
    # Lặp qua các bước chạy của Graph để in log
    for output in app.stream(inputs, {"recursion_limit": 15}):
        for key, value in output.items():
            pass # Quá trình xử lý đang chạy ngầm
            
    # Lấy câu trả lời cuối cùng
    final_state = app.get_state({"messages": [HumanMessage(content=cau_hoi)]}) # (Sẽ sửa thành lấy trực tiếp từ state sau nếu cần)
    
    # Lấy tin nhắn cuối cùng trong mảng messages
    # print("\n✅ TRẢ LỜI CUỐI CÙNG TỪ HỆ THỐNG:")
    # Chạy lại app.invoke để lấy kết quả cuối sạch sẽ nhất cho bài test này
    final_result = app.invoke(inputs)
    # print(final_result["messages"][-1].content)