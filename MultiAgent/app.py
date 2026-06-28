import streamlit as st
import requests
from langchain_core.messages import HumanMessage, AIMessage
from multi_agent_gpt import app as agent_app

# ==========================================
# 1. CẤU HÌNH TRANG WEB & BIẾN TRẠNG THÁI
# ==========================================
st.set_page_config(
    page_title="Cố Vấn Học Vụ AI",
    page_icon="🎓",
    layout="centered"
)

# Biến trạng thái đăng nhập
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "student_data" not in st.session_state:
    st.session_state.student_data = None
    
# MỚI: Biến trạng thái lưu trữ Lịch sử Chatbot
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# Đảm bảo bạn đang dùng đúng port của API Backend
BASE_API_URL = "https://localhost:44326/api"

# ==========================================
# 2. GIAO DIỆN ĐĂNG NHẬP (LOGIN SCREEN)
# ==========================================
def show_login_screen():
    st.title("🎓 Cổng Tư Vấn Học Vụ Sinh Viên")
    st.markdown("Vui lòng đăng nhập bằng Mã số sinh viên để tiếp tục.")
    
    with st.form("login_form"):
        student_id = st.text_input("Mã số sinh viên:", placeholder="Ví dụ: SV12345")
        submit_button = st.form_submit_button("🚀 Đăng nhập", type="primary")
        
        if submit_button:
            if not student_id.strip():
                st.error("⚠️ Vui lòng nhập Mã số sinh viên!")
            else:
                with st.spinner("Đang xác thực thông tin..."):
                    try:
                        response = requests.get(
                            f"{BASE_API_URL}/Students/{student_id.strip()}", 
                            timeout=10,
                            verify=False
                        )
                        
                        if response.status_code == 200:
                            st.session_state.logged_in = True
                            st.session_state.student_data = response.json()
                            # Xóa lịch sử chat cũ nếu có người khác đăng nhập vào
                            st.session_state.chat_messages = [] 
                            st.rerun() 
                        elif response.status_code == 404:
                            st.error("❌ Không tìm thấy sinh viên! Vui lòng kiểm tra lại mã số.")
                        else:
                            st.error(f"⚠️ Lỗi từ Backend: {response.status_code}")
                            
                    except Exception as e:
                        st.error(f"🔌 Lỗi kết nối: {str(e)}")

# ==========================================
# 3. GIAO DIỆN CHÍNH (DASHBOARD CHATBOT)
# ==========================================
def show_dashboard_screen():
    data = st.session_state.student_data
    
    # Bóc tách dữ liệu an toàn
    last_name = data.get('LastName') or data.get('lastName', '')
    first_name = data.get('FirstName') or data.get('firstName', '')
    student_code = data.get('StudentCode') or data.get('studentCode', '')
    department_title = data.get('DepartmentTitle') or data.get('departmentTitle', '')
    
    # --- Sidebar chứa thông tin Sinh viên ---
    with st.sidebar:
        st.header("👤 Thông tin sinh viên")
        st.info(f"**Họ tên:** {last_name} {first_name}\n\n"
                f"**MSSV:** {student_code}\n\n"
                f"**Khoa:** {department_title}")
        
        st.markdown("---")
        if st.button("🚪 Đăng xuất", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.student_data = None
            st.session_state.chat_messages = [] # Xóa bộ nhớ chat
            st.rerun()

    # --- Khu vực Chat chính ---
    st.title("💬 Cố vấn Học vụ AI")
    st.markdown("---")
    
    # 3.1. VẼ LẠI LỊCH SỬ CHAT CŨ (Mỗi khi màn hình load lại)
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            # Nếu là tin nhắn của AI và có lưu quá trình suy nghĩ
            if msg["role"] == "assistant" and "thinking_logs" in msg:
                with st.expander("🧠 Quá trình suy nghĩ", expanded=False):
                    for log in msg["thinking_logs"]:
                        st.markdown(log)
            # In nội dung chat
            st.markdown(msg["content"])

    # 3.2. NHẬP LIỆU VÀ XỬ LÝ CÂU HỎI MỚI
    # st.chat_input tạo thanh nhập liệu dính ở đáy màn hình
    if prompt := st.chat_input("Nhập câu hỏi của bạn tại đây..."):
        
        # In ngay câu hỏi của người dùng lên màn hình
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Lưu câu hỏi vào lịch sử UI (Chưa có mã sinh viên để UI nhìn đẹp)
        st.session_state.chat_messages.append({"role": "user", "content": prompt})

        # Xử lý câu trả lời của AI
        with st.chat_message("assistant"):
            with st.spinner("🤖 Đang suy nghĩ..."):
                try:
                    # MỚI: Tái tạo lại toàn bộ bộ nhớ ngữ cảnh cho LangGraph
                    langgraph_memory = []
                    for ui_msg in st.session_state.chat_messages[:-1]: # Bỏ câu cuối cùng vừa append
                        if ui_msg["role"] == "user":
                            langgraph_memory.append(HumanMessage(content=ui_msg["content"]))
                        else:
                            langgraph_memory.append(AIMessage(content=ui_msg["content"]))
                            
                    # Gắn ngầm mã sinh viên vào CHỈ câu hỏi hiện tại để giữ khả năng gọi API
                    full_prompt = f"Tôi là sinh viên mã {student_code}. {prompt}"
                    langgraph_memory.append(HumanMessage(content=full_prompt))
                    
                    # Chạy Multi-Agent với toàn bộ trí nhớ
                    final_result = agent_app.invoke({"messages": langgraph_memory})
                    
                    # Bóc tách dữ liệu
                    thinking_logs = []
                    final_answer = "Xin lỗi, hệ thống không thể đưa ra câu trả lời."
                    
                    # Duyệt lấy các tin nhắn MỚI NHẤT do Agent sinh ra
                    for msg in final_result["messages"][len(langgraph_memory)-1:]:
                        if msg.type == "ai":
                            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                for tool in msg.tool_calls:
                                    thinking_logs.append(f"⚙️ **Agent gọi Tool:** `{tool['name']}` | Tham số: {tool['args']}")
                            
                            if msg.content:
                                if isinstance(msg.content, list):
                                    text_blocks = [block["text"] for block in msg.content if block.get("type") == "text"]
                                    final_answer = "\n".join(text_blocks)
                                else:
                                    final_answer = msg.content
                        elif msg.type == "tool":
                            # Bọc kết quả Tool trong khung code để giao diện không bị vỡ
                            thinking_logs.append(f"🔧 **Kết quả Tool:**\n```\n{msg.content}\n```")

                    # Vẽ White-box UI
                    if thinking_logs:
                        with st.expander("🧠 Quá trình suy nghĩ của Hệ thống", expanded=False):
                            for log in thinking_logs:
                                st.markdown(log)

                    # Vẽ câu trả lời cuối cùng
                    st.markdown(final_answer)
                    
                    # Lưu câu trả lời và quá trình suy nghĩ vào Session State
                    st.session_state.chat_messages.append({
                        "role": "assistant", 
                        "content": final_answer,
                        "thinking_logs": thinking_logs
                    })
                    
                except Exception as e:
                    st.error(f"❌ Có lỗi xảy ra trong luồng AI: {e}")

# ==========================================
# 4. BỘ ĐỊNH TUYẾN ROUTER (MAIN APP)
# ==========================================
if not st.session_state.logged_in:
    show_login_screen()
else:
    show_dashboard_screen()