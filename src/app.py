"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer / Integrator)
Ghép nối hoàn chỉnh: Tools + Prompts + Test Cases + Multi-Provider ReAct Engine.
Chủ đề: Trợ Lý Tìm & Đặt Lịch Xem Nhà Trọ / Căn Hộ Cho Thuê
"""

import json
import os
import re
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()


def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_action(llm_text: str):
    """
    Bóc tách Action và các tham số từ văn bản phản hồi của LLM.
    Ví dụ: Action: search_listings['Cầu Giấy', 5000000]
    """
    match = re.search(r"Action:\s*(\w+)\[(.*?)\]", llm_text, re.DOTALL)
    if not match:
        return None, []
    
    tool_name = match.group(1).strip()
    raw_args = match.group(2).strip()
    
    if not raw_args:
        args = []
    else:
        args = [arg.strip().strip("'\"") for arg in raw_args.split(",")]
        
    return tool_name, args


def run_baseline_chatbot(user_query: str, provider):
    """Chạy Chatbot gốc (Baseline) không sử dụng Tool"""
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")


def run_react_agent(user_query: str, provider):
    """
    Động cơ Vòng lặp ReAct Agent (Thought -> Action -> Observation) ĐỘNG có Guardrails
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    
    conversation_history = f"Câu hỏi của người dùng: {user_query}\n"
    step = 0
    
    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        
        response = provider.generate(conversation_history, system_prompt=REACT_SYSTEM_PROMPT)
        print(response)
        
        if "Final Answer:" in response:
            print("\n✅ AGENT ĐÃ HOÀN THÀNH NHIỆM VỤ!")
            break
            
        tool_name, args = parse_action(response)
        
        if tool_name and tool_name in AVAILABLE_TOOLS:
            print(f"\n🛠️ [EXECUTING TOOL]: {tool_name}{args}")
            tool_func = AVAILABLE_TOOLS[tool_name]
            
            try:
                observation = tool_func(*args)
            except Exception as e:
                observation = f"LỖI THỰC THI TOOL {tool_name}: {str(e)}"
                
            print(f"👁️ [OBSERVATION]: {observation}")
            conversation_history += f"\n{response}\nObservation: {observation}\n"
        else:
            print("⚠️ Không phát hiện Action hợp lệ hoặc tên Tool không tồn tại.")
            conversation_history += f"\n{response}\nObservation: Lỗi định dạng Action hoặc tên công cụ không đúng.\n"
            
    if step >= MAX_ITERATIONS and "Final Answer:" not in response:
        print(f"\n🛡️ [GUARDRAIL TRIGGERED]: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Tự động ngắt lặp an toàn!")


if __name__ == "__main__":
    print("==================================================================")
    print("🏫 VINUNI LAB 3 - TRỢ LÝ TÌM & ĐẶT LỊCH XEM NHÀ TRỌ (REACT AGENT)")
    print("==================================================================")
    
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})\n")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
    
    # Câu hỏi multi-step quy trình đầy đủ 4 bước
    sample_query = "Tìm giúp tôi phòng trọ ở 'Cầu Giấy' giá dưới 5 triệu, xem chi tiết PT-101, kiểm tra lịch trống và đặt lịch xem lúc 09:00 cho Nguyễn Văn A, SĐT 0912345678."
    
    print("--- DEMO 1: CHẠY CHATBOT BASELINE ---")
    run_baseline_chatbot(sample_query, provider)
    
    print("\n--- DEMO 2: CHẠY REACT AGENT (CHUỖI 4 BƯỚC) ---")
    run_react_agent(sample_query, provider)