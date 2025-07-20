import os
from flask import Flask, request, abort
from dotenv import load_dotenv

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# 從 .env 文件載入環境變數
load_dotenv()

app = Flask(__name__)

# 從環境變數中取得 LINE Bot 的相關金鑰
# 請確保這些變數在部署時設定正確
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# 檢查環境變數是否設定
if not LINE_CHANNEL_ACCESS_TOKEN:
    raise ValueError("LINE_CHANNEL_ACCESS_TOKEN is not set.")
if not LINE_CHANNEL_SECRET:
    raise ValueError("LINE_CHANNEL_SECRET is not set.")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set.")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ==============================================================================
# 這裡放置您的 AI 模型互動邏輯 (目前為簡單範例，之後會替換)
# 為了簡化，這裡暫時不直接呼叫 OpenAI API，而是模擬回覆
# 您之後會在這裡加入真正的 OpenAI API 呼叫
# ==============================================================================
def get_ai_response(user_message):
    """根據用戶訊息生成 AI 回覆"""
    # 這裡將來會替換成與 OpenAI API 互動的代碼
    # 例如：
    # from openai import OpenAI
    # client = OpenAI(api_key=OPENAI_API_KEY)
    # completion = client.chat.completions.create(
    #     model="gpt-4", # 選擇適合的模型
    #     messages=[
    #         {"role": "system", "content": "你是一個樂於助人的AI助理。"},
    #         {"role": "user", "content": user_message}
    #     ]
    # )
    # return completion.choices[0].message.content

    # 為了確保部署成功，這裡先用簡單的規則回覆
    if "你好" in user_message:
        return "您好！我是EVA AI助理，很高興為您服務！"
    elif "天氣" in user_message:
        return "天氣資訊目前無法提供，請您稍後再試。我還在學習中！"
    elif "謝謝" in user_message:
        return "不客氣！"
    else:
        return "我還在學習如何回應您的問題，請說得更清楚一點好嗎？"

# ==============================================================================

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
    # 在本地開發時使用 5000 端口
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)