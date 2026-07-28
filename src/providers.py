"""
🔌 MULTI-PROVIDER LLM ADAPTER (OpenAI, Gemini, Anthropic, OpenRouter & Offline Mock)
Chủ đề: Trợ Lý Tìm & Đặt Lịch Xem Nhà Trọ / Căn Hộ Cho Thuê
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()


class BaseLLMProvider:
    """Interface cơ sở cho tất cả các LLM Provider"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env!"
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (GPT-4o, GPT-3.5-turbo)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env!"
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude Provider"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "claude-3-haiku-20240307"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_anthropic_api_key_here":
            return "[Anthropic Error]: Chưa cấu hình ANTHROPIC_API_KEY trong file .env!"
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            kwargs = {
                "model": self.model_name,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system_prompt:
                kwargs["system"] = system_prompt
                
            response = client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            return f"[Anthropic Exception]: {str(e)}"


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter Provider"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "google/gemini-2.5-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            return "[OpenRouter Error]: Chưa cấu hình OPENROUTER_API_KEY trong file .env!"
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model_name,
                "messages": messages
            }
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
            else:
                return f"[OpenRouter API Error {res.status_code}]: {res.text}"
        except Exception as e:
            return f"[OpenRouter Exception]: {str(e)}"


class MockProvider(BaseLLMProvider):
    """Offline Mock Provider (Giả lập trôi chảy chuỗi 4 bước ReAct cho Đề tài 10)"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        text = prompt.lower()
        
        # Cho Baseline Chatbot
        if "tư vấn thuê nhà trọ thông thường" in system_prompt.lower():
            return "Tôi là Chatbot tư vấn thông thường. Tôi không có quyền truy cập cơ sở dữ liệu phòng trọ thực tế nên không thể tra cứu hay đặt lịch cho bạn."

        # STEP 4: Sau khi đã đặt lịch hẹn ở Step 3 -> Trả về Final Answer
        if "Observation: ✅ ĐẶT LỊCH THÀNH CÔNG" in prompt:
            return (
                "Thought: Lịch hẹn xem phòng đã được xác nhận thành công vào hệ thống. Tôi đã hoàn thành chuỗi 4 nhiệm vụ.\n"
                "Final Answer: Đã xem chi tiết, kiểm tra lịch trống và đặt lịch hẹn xem nhà thành công cho anh Nguyễn Văn A (SĐT: 0912345678) tại phòng PT-101 (Cầu Giấy) vào lúc 09:00!"
            )

        # STEP 3: Sau khi đã có danh sách khung giờ còn trống ở Step 2 -> Gọi book_viewing
        if "Observation: Khung giờ còn trống" in prompt:
            return "Thought: Khung giờ 09:00 còn trống. Bây giờ tôi sẽ gọi công cụ book_viewing để đặt lịch xem nhà.\nAction: book_viewing['PT-101', '09:00', 'Nguyễn Văn A', '0912345678']"

        # STEP 2: Sau khi đã có chi tiết phòng ở Step 1 -> Gọi check_viewing_slots
        if "Observation: Chi tiết PT-101" in prompt:
            return "Thought: Đã xem xong chi tiết phòng PT-101. Tiếp theo tôi sẽ kiểm tra các khung giờ xem nhà còn trống.\nAction: check_viewing_slots['PT-101']"

        # STEP 1: Sau khi đã tìm thấy danh sách phòng trọ ở Step 0 -> Gọi get_listing_detail
        if "Observation: Tìm thấy các tin đăng phù hợp" in prompt:
            return "Thought: Đã tìm thấy danh sách phòng trọ. Tiếp theo tôi sẽ lấy thông tin chi tiết của phòng PT-101.\nAction: get_listing_detail['PT-101']"

        # STEP 0: Ban đầu -> Gọi search_listings
        return "Thought: Bước 1, tôi cần tìm danh sách phòng trọ tại Cầu Giấy với ngân sách dưới 5 triệu.\nAction: search_listings['Cầu Giấy', 5000000]"


def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    """Factory function tự động chọn Provider từ biến môi trường LLM_PROVIDER"""
    name = (provider_name or os.getenv("LLM_PROVIDER") or "mock").lower().strip()
    
    if name == "gemini":
        return GeminiProvider()
    elif name == "openai":
        return OpenAIProvider()
    elif name == "anthropic":
        return AnthropicProvider()
    elif name == "openrouter":
        return OpenRouterProvider()
    else:
        return MockProvider()