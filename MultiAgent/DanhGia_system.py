import json
import time
from langchain_core.messages import HumanMessage, SystemMessage
import os
import datetime

# Import Đồ thị và cả LLM (để làm Giám khảo) từ file multi_agent của bạn
from multi_agent_gpt import app as agent_app, llm as judge_llm

def judge_answer(question: str, intent: str, evidence: str, final_answer: str) -> str:
    """Hàm Giám khảo AI đối chiếu câu trả lời với Bằng chứng thực tế"""
    
    judge_prompt = f"""Bạn là một GIÁM KHẢO AI KHÁCH QUAN. Nhiệm vụ của bạn là kiểm tra xem hệ thống Chatbot có bịa đặt thông tin (Hallucination) hay không.

    THÔNG TIN KIỂM THỬ:
    - Câu hỏi: {question}
    - Mục tiêu (Intent): {intent}
    - BẰNG CHỨNG TỪ HỆ THỐNG (API/Database): {evidence}
    - Câu trả lời của Chatbot: {final_answer}
    
    TIÊU CHÍ CHẤM ĐIỂM NGHIÊM NGẶT:
    1. Trung thành với Dữ liệu (Faithfulness): MỌI thông tin, con số, sự kiện trong "Câu trả lời của Chatbot" BẮT BUỘC phải xuất hiện hoặc được suy ra trực tiếp từ "BẰNG CHỨNG TỪ HỆ THỐNG". 
    2. Nếu Chatbot đưa ra bất kỳ chi tiết nào KHÔNG CÓ trong Bằng chứng, đó là BỊA ĐẶT -> Đánh giá [FAIL].
    3. Nếu Bằng chứng bị trống hoặc báo lỗi, nhưng Chatbot vẫn cố tình trả lời ra kết quả -> BỊA ĐẶT -> Đánh giá [FAIL].
    4. Nếu Bằng chứng trống và Chatbot từ chối trả lời (xin lỗi người dùng) -> Chấp nhận -> Đánh giá [PASS].

    ĐỊNH DẠNG TRẢ LỜI BẮT BUỘC:
    [PASS/FAIL] - <Giải thích ngắn gọn việc đối chiếu với bằng chứng>"""
    
    response = judge_llm.invoke(
        [SystemMessage(content=judge_prompt)],
        temperature=1.0
    )
    return response.content.strip()

def run_evaluation(dataset_path: str):
    print(f"🚀 BẮT ĐẦU CHẠY KIỂM THỬ TỰ ĐỘNG & ĐÁNH GIÁ KÉP (CÓ BẰNG CHỨNG)...")
    
    with open(dataset_path, 'r', encoding='utf-8') as file:
        test_cases = json.load(file)
        
    results = []
    correct_routing = 0
    correct_content = 0
    total = len(test_cases)
    
    for idx, test in enumerate(test_cases):
        print(f"🔄 Đang xử lý [{idx+1}/{total}]: {test['id']}...", end=" ", flush=True)
        start_time = time.time()
        
        # --- KHỞI TẠO BIẾN HỨNG DỮ LIỆU ---
        actual_agent = "UNKNOWN"
        final_answer = "Lỗi hệ thống hoặc Không có câu trả lời."
        evidence_logs = [] # Mảng chứa bằng chứng từ Tool
        
        try:
            inputs = {"messages": [HumanMessage(content=test['question'])]}
            
            # --- CHẠY ĐỒ THỊ LẤY DỮ LIỆU ---
            for output in agent_app.stream(inputs, {"recursion_limit": 25}):
                node_name = list(output.keys())[0]
                
                # 1. Bắt quyết định của Lễ tân
                if node_name == "Supervisor":
                    actual_agent = output[node_name].get("next_agent", actual_agent)
                
                # 2. Bắt log xử lý của Đặc vụ
                elif node_name in ["AcademicAgent", "StudentServiceAgent"]:
                    messages = output[node_name].get("messages", [])
                    
                    for msg in messages:
                        # GOM BẰNG CHỨNG (Từ Tool)
                        if msg.type == "tool":
                            # Cắt ngắn nếu nội dung tool quá dài để tránh lỗi max_tokens của Giám khảo
                            content_preview = msg.content[:2000] + "..." if len(msg.content) > 2000 else msg.content
                            evidence_logs.append(f"[{msg.name}]: {content_preview}")
                        
                        # BẮT CÂU TRẢ LỜI (Từ AI)
                        elif msg.type == "ai" and msg.content:
                            if isinstance(msg.content, list):
                                text_blocks = [block["text"] for block in msg.content if block.get("type") == "text"]
                                final_answer = "\n".join(text_blocks)
                            else:
                                final_answer = msg.content
            
            # --- CHUẨN BỊ BẰNG CHỨNG CHO GIÁM KHẢO ---
            full_evidence = "\n".join(evidence_logs) if evidence_logs else "[Không có Tool nào được gọi]"
            
            # 1. Chấm điểm Định tuyến (Routing)
            routing_pass = (actual_agent == test['expected_agent'])
            if routing_pass: correct_routing += 1
            
            # 2. Chấm điểm Nội dung (LLM-as-a-Judge kèm Bằng chứng)
            judge_result = judge_answer(test['question'], test['intent'], full_evidence, final_answer)
            if "[PASS]" in judge_result.upper(): correct_content += 1
            
            elapsed = round(time.time() - start_time, 2)
            print(f"✅ Xong ({elapsed}s)")
            
            results.append({
                "ID": test['id'],
                "Group": test['category'],
                "Routing": "✅ PASS" if routing_pass else f"❌ FAIL ({actual_agent})",
                "Content": judge_result,
                "Time(s)": elapsed
            })
            
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            results.append({
                "ID": test['id'],
                "Group": test['category'],
                "Routing": "⚠️ ERROR",
                "Content": f"Lỗi thực thi: {str(e)}",
                "Time(s)": round(time.time() - start_time, 2)
            })

    # ==========================================
    # KẾT XUẤT MARKDOWN BẢNG BIỂU VÀ LƯU FILE TXT
    # ==========================================
    md_table = f"## 📊 BÁO CÁO KẾT QUẢ KIỂM THỬ HỆ THỐNG MULTI-AGENT\n\n"
    md_table += f"**Độ chính xác Định tuyến:** {correct_routing}/{total} ({(correct_routing/total)*100:.1f}%)\n"
    md_table += f"**Độ chính xác Nội dung (dùng một mô hình LLM để đánh giá):** {correct_content}/{total} ({(correct_content/total)*100:.1f}%)\n\n"
    
    md_table += "| ID | Nhóm Test | Định tuyến | Đánh giá Nội dung (LLM Judge) | Tốc độ |\n"
    md_table += "|---|---|---|---|---|\n"
    
    for r in results:
        content_preview = r['Content'].replace('\n', ' ')
        md_table += f"| {r['ID']} | {r['Group']} | {r['Routing']} | {content_preview} | {r['Time(s)']}s |\n"
        
    # In ra Terminal
    print("\n" + "="*80)
    print(md_table)
    print("="*80)
    
    # ---------------------------------------------------------
    # TỰ ĐỘNG TẠO THƯ MỤC VÀ LƯU FILE KÈM TIMESTAMP
    # ---------------------------------------------------------
    thu_muc_luu = "DanhGia"
    os.makedirs(thu_muc_luu, exist_ok=True) # Tự động tạo thư mục nếu chưa tồn tại
    
    # Lấy thời gian hiện tại theo format yyyymmddhhmmss
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Nối tên file và đường dẫn
    ten_file = f"BaoCao_KiemThu_{timestamp}.txt"
    duong_dan_hoan_chinh = os.path.join(thu_muc_luu, ten_file)
    
    # Lưu file
    with open(duong_dan_hoan_chinh, "w", encoding="utf-8") as f:
        f.write(md_table)
        
    print(f"\n📁 Đã xuất báo cáo thành công tại: {duong_dan_hoan_chinh}")

if __name__ == "__main__":
    run_evaluation("test_dataset.json")