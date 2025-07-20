import os
from flask import Flask, request, abort
from dotenv import load_dotenv

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import google.generativeai as genai
import traceback # 導入 traceback 模組

load_dotenv()

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') 

if not LINE_CHANNEL_ACCESS_TOKEN:
    raise ValueError("LINE_CHANNEL_ACCESS_TOKEN is not set.")
if not LINE_CHANNEL_SECRET:
    raise ValueError("LINE_CHANNEL_SECRET is not set.")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set.")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-pro')

def get_ai_response(user_message):
    """根據用戶訊息生成 AI 回覆 (使用 Gemini API)"""
    if not user_message or user_message.strip() == "":
        return "您好！請輸入一些內容，我才能為您服務喔。"

    try:
        # 使用 Gemini 模型生成內容
        # 這裡可以加入一些安全設置，例如降低敏感度 (如果需要)
        # 詳情請參考 Gemini API 文件
        # response = model.generate_content(user_message, safety_settings={'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE'})
        response = model.generate_content(user_message)
        return response.text 
    except Exception as e:
        # 打印完整的錯誤堆疊追蹤，以便我們更精確地診斷問題
        print(f"Gemini API error during content generation: {e}")
        traceback.print_exc() # 打印堆疊追蹤
        return "對不起，目前AI服務無法回應您的請求，請稍後再試。"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    
    ai_response = get_ai_response(user_message)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=ai_response)
    )

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
