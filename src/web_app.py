"""
🌐 WEB UI ĐỂ TEST CHATBOT BASELINE & REACT AGENT TRÊN LOCALHOST
Giao diện trình duyệt đơn giản dựng trên Flask, tái sử dụng logic thật từ
tools.py (Role 2), prompts.py (Role 3) và app.py (Role 4) — không thay đổi
hành vi của các file đó, chỉ gọi lại để hiển thị trực quan trên web.

Chạy: python src/web_app.py  ➔  mở http://127.0.0.1:5000
"""

import json
import os
import re
import sys

from flask import Flask, jsonify, render_template, request

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import parse_action
from prompts import CHATBOT_BASELINE_PROMPT, MAX_ITERATIONS, REACT_SYSTEM_PROMPT
from providers import get_llm_provider
from tools import AVAILABLE_TOOLS

app = Flask(__name__)

# Provider (providers.py) trả lỗi kết nối dưới dạng chuỗi có tiền tố này thay vì raise
# Exception, để không làm crash Agent — nhưng UI cần nhận diện để KHÔNG đem chuỗi lỗi
# đi parse như một Thought/Action bình thường.
_PROVIDER_ERROR_RE = re.compile(r"^\[(Gemini|OpenAI|Anthropic|OpenRouter) (Exception|Error)\]:\s*(.*)", re.DOTALL)


def _friendly_provider_error(text: str):
    """Rút gọn lỗi provider thô (thường là JSON dài) thành 1 câu tiếng Việt dễ hiểu.
    Trả về None nếu `text` không phải là lỗi provider (tức là câu trả lời bình thường)."""
    match = _PROVIDER_ERROR_RE.match((text or "").strip())
    if not match:
        return None
    provider_name, _, detail = match.groups()
    if "RESOURCE_EXHAUSTED" in detail or "insufficient_quota" in detail or " 429" in f" {detail}":
        return f"⚠️ Đã vượt quota miễn phí của {provider_name}. Vui lòng thử lại sau vài phút hoặc đổi LLM_PROVIDER khác trong file .env."
    if "chưa cấu hình" in detail.lower() or "api_key" in detail.lower():
        return f"⚠️ Chưa cấu hình đúng API key cho {provider_name}. Kiểm tra lại file .env."
    first_line = detail.strip().splitlines()[0][:200]
    return f"⚠️ Lỗi kết nối tới {provider_name}: {first_line}"


def _provider_label(provider) -> str:
    model_name = getattr(provider, "model_name", None)
    return f"{provider.__class__.__name__} ({model_name})" if model_name else provider.__class__.__name__


def load_test_cases():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_react_agent_web(user_query: str, provider) -> dict:
    """Bản sao logic của run_react_agent() trong app.py, nhưng trả về dữ liệu
    có cấu trúc (JSON) thay vì print ra console, để frontend render trực quan."""
    conversation_history = f"Câu hỏi của người dùng: {user_query}\n"
    steps = []
    step = 0
    final_answer = None

    while step < MAX_ITERATIONS:
        step += 1
        response = provider.generate(conversation_history, system_prompt=REACT_SYSTEM_PROMPT)

        # Lỗi kết nối LLM Provider (hết quota, sai key...) không phải là một bước suy
        # luận thật — dừng ngay thay vì tốn 1 vòng lặp cố parse Action từ chuỗi lỗi.
        provider_error = _friendly_provider_error(response)
        if provider_error:
            return {
                "steps": steps,
                "final_answer": None,
                "provider_error": provider_error,
                "guardrail_triggered": False,
                "max_iterations": MAX_ITERATIONS,
            }

        if "Final Answer:" in response:
            thought_part, _, final_part = response.partition("Final Answer:")
            steps.append({
                "step": step,
                "thought": thought_part.replace("Thought:", "").strip(),
                "action": None,
                "observation": None,
                "is_final": True,
            })
            final_answer = final_part.strip()
            break

        tool_name, args = parse_action(response)
        thought_part = response.split("Action:")[0].replace("Thought:", "").strip() if "Action:" in response else response.strip()

        if tool_name and tool_name in AVAILABLE_TOOLS:
            observation = AVAILABLE_TOOLS[tool_name](*args)
            error = False
        else:
            observation = "Lỗi định dạng Action hoặc tên công cụ không đúng. Hãy kiểm tra lại danh sách công cụ."
            error = True

        steps.append({
            "step": step,
            "thought": thought_part,
            "action": f"{tool_name}[{', '.join(args)}]" if tool_name else None,
            "observation": observation,
            "is_final": False,
            "error": error,
        })
        conversation_history += f"\n{response}\nObservation: {observation}\n"

    guardrail_triggered = final_answer is None
    return {
        "steps": steps,
        "final_answer": final_answer,
        "provider_error": None,
        "guardrail_triggered": guardrail_triggered,
        "max_iterations": MAX_ITERATIONS,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/test-cases")
def api_test_cases():
    return jsonify(load_test_cases())


@app.route("/api/baseline", methods=["POST"])
def api_baseline():
    question = (request.get_json(silent=True) or {}).get("question", "").strip()
    if not question:
        return jsonify({"error": "Câu hỏi trống"}), 400

    provider = get_llm_provider()
    response = provider.generate(question, system_prompt=CHATBOT_BASELINE_PROMPT)
    return jsonify({
        "response": response,
        "provider_error": _friendly_provider_error(response),
        "provider": _provider_label(provider),
    })


@app.route("/api/agent", methods=["POST"])
def api_agent():
    question = (request.get_json(silent=True) or {}).get("question", "").strip()
    if not question:
        return jsonify({"error": "Câu hỏi trống"}), 400

    provider = get_llm_provider()
    result = run_react_agent_web(question, provider)
    result["provider"] = _provider_label(provider)
    return jsonify(result)


if __name__ == "__main__":
    print("==================================================")
    print("🌐 WEB UI TEST — CHATBOT VS REACT AGENT")
    print("👉 Mở trình duyệt tại: http://127.0.0.1:5000")
    print("==================================================")
    app.run(debug=True, port=5000)
