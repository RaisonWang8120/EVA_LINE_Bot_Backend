import os
from flask import Flask, request, abort
from dotenv import load_dotenv

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import google.generativeai as genai

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

def get_ai_response(user_message):
    """根據用戶訊息生成 AI 回覆 (使用 Gemini API)"""
    try:
        # 嘗試列出可用的模型，以確認 API 連接和金鑰有效性
        print("嘗試列出 Gemini 可用模型...")
        available_models = [m.name for m in genai.list_models()]
        print(f"可用的 Gemini 模型: {available_models}")

        # 如果 'gemini-pro' 在列表中，則嘗試使用它
        if 'gemini-pro' in available_models:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(user_message)
            return response.text
        else:
            return "對不起，Gemini Pro 模型目前不可用，請稍後再試或聯繫管理員。"
    except Exception as e:
        print(f"Gemini API error during model listing or content generation: {e}")
        return "對不起，AI服務連接失敗，請稍後再試。"

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
