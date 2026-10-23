import os
import google.generativeai as genai

# 設定 Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def summarize_tender_with_ai(tender_title, unit_name, tender_detail_text=""):
    """使用 AI 針對標案名稱與內容生成高價值業務摘要"""
    prompt = f"""
你是一位政府標案與資訊服務業的專業投標顧問。請針對以下公部門標案進行快速摘要：
- 標案名稱：{tender_title}
- 招標機關：{unit_name}
- 標案簡述：{tender_detail_text}

請用簡潔繁體中文列出 2 個核心重點：
1. 【核心需求與潛在技術】：這案子主要要做什麼？（例如：網站改版、雲端遷移、AI微調、資安SOC）
2. 【建議評估方向】：這類標案適合什麼類型的團隊參與，或投標應注意的關鍵？

請控制在 80 字以內，用語簡明專業，適合主管快速閱讀。
"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "• AI 摘要整理中（暫用預設簡述）"
