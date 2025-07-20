import os
from flask import Flask, request, abort
from dotenv import load_dotenv

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# 導入 Gemini 相關模組
import google.generativeai as genai

# 從 .env 文件載入環境變數
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

# 配置 Gemini API 金鑰
genai.configure(api_key=GEMINI_API_KEY)

# 初始化 Gemini 模型
# 既然日誌顯示 'gemini-pro' 可用，我們就直接用它
model = genai.GenerativeModel('gemini-pro')

def get_ai_response(user_message):
    """根據用戶訊息生成 AI 回覆 (使用 Gemini API)"""
    try:
        # 直接使用 Gemini 模型生成內容
        response = model.generate_content(user_message)
        return response.text # Gemini 回覆的內容在 .text 屬性中
    except Exception as e:
        print(f"Gemini API error during content generation: {e}")
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
    
    # 呼叫 AI 模型獲取回覆
    ai_response = get_ai_response(user_message)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=ai_response)
    )

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
