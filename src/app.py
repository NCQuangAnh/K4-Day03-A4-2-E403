"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer / Integrator)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
Chủ đề: Trợ Lý Tìm & Đặt Lịch Xem Nhà Trọ / Căn Hộ Cho Thuê
"""

import json
import os
import re
import sys
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import đầy đủ từ các file của Role 2, Role 3 & Multi-Provider Adapter
from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()


def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_action(llm_text: str):
    """
    Hàm bóc tách Action và danh sách tham số từ phản hồi của LLM.
    Ví dụ: Action: search_listings['Cầu Giấy', 4500000]
    """
    match = re.search(r"Action:\s*(\w+)\[(.*?)\]", llm_text, re.DOTALL)
    if not match:
        return None, []
    
    tool_name = match.group(1).strip()
    raw_args = match.group(2).strip()
    
    if not raw_args:
        args = []
    else:
        # Bóc tách tham số phân tách bằng dấu phẩy và làm sạch dấu ngoặc kép/đơn
        args = [arg.strip().strip("'\"") for arg in raw_args.split(",")]
        
    return tool_name, args


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")
    
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")


def run_react_agent(user_query: str, provider):
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) ĐỘNG có Guardrails.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    
    conversation_history = f"Câu hỏi của người dùng: {user_query}\n"
    step = 0
    
    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        
        # Gọi LLM sinh suy luận (Thought & Action)
        response = provider.generate(conversation_history, system_prompt=REACT_SYSTEM_PROMPT)
        print(response)
        
        # 1. Kiểm tra nếu Agent đã chốt Final Answer
        if "Final Answer:" in response:
            print("\n✅ AGENT ĐÃ HOÀN THÀNH NHIỆM VỤ!")
            break
            
        # 2. Bóc tách tên Tool và các tham số
        tool_name, args = parse_action(response)
        
        if tool_name and tool_name in AVAILABLE_TOOLS:
            print(f"\n🛠️ [EXECUTING TOOL]: {tool_name}{args}")
            tool_func = AVAILABLE_TOOLS[tool_name]
            
            # Gọi tool và thu về Observation
            observation = tool_func(*args)
            print(f"👁️ [OBSERVATION]: {observation}")
            
            # Nối kết quả Observation vào lịch sử hội thoại cho bước tiếp theo
            conversation_history += f"\n{response}\nObservation: {observation}\n"
        else:
            print("⚠️ Không phát hiện Action hợp lệ hoặc tên Tool không được đăng ký.")
            conversation_history += f"\n{response}\nObservation: Lỗi định dạng Action hoặc tên công cụ không đúng. Hãy kiểm tra lại danh sách công cụ.\n"
            
    if step >= MAX_ITERATIONS and "Final Answer:" not in response:
        print(f"\n🛡️ [GUARDRAIL TRIGGERED]: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Tự động ngắt lặp an toàn!")


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("🏫 Đề tài: Tìm & Đặt Lịch Xem Nhà Trọ / Căn Hộ")
    print("==================================================")
    
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
    
    # Chạy thử câu Test Case #3 (Tìm nhà trọ ở Cầu Giấy dưới 4.5 triệu)
    sample_query = tests[2]["question"]
    
    print("--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE ---")
    run_baseline_chatbot(sample_query, provider)
    
    print("\n--- DEMO 2: CHẠY TRÊN REACT AGENT ---")
    run_react_agent(sample_query, provider)