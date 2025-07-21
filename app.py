import os
from flask import Flask, request, abort
from dotenv import load_dotenv

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import google.generativeai as genai
import traceback 
import re # 導入正則表達式模組，用於文字匹配
import sqlite3 # 導入 SQLite 模組，用於資料庫操作

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

model = genai.GenerativeModel('gemini-1.5-flash') 

init_db()
# === 新增：初始化資料庫函數 ===
# 這個函數會在 Bot 啟動時執行，確保我們有一個儲存記帳數據的資料庫表
def init_db():
    try:
        # 連接到資料庫文件。如果文件不存在，SQLite 會自動創建它。
        conn = sqlite3.connect('expenses.db') 
        cursor = conn.cursor()
        # 創建 expenses 表。如果表已經存在，就不會重複創建。
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                item TEXT,
                date TEXT DEFAULT CURRENT_DATE
            )
        ''')
        conn.commit() # 提交更改
        conn.close() # 關閉連接
        print("SQLite 資料庫初始化成功。")
    except Exception as e:
        print(f"SQLite 資料庫初始化失敗: {e}")
        traceback.print_exc()

# === 主要的 AI 回覆邏輯函數 ===
def def get_ai_response(user_message):
    """根據用戶訊息生成 AI 回覆 (嘗試記帳，否則呼叫 Gemini)"""
    if not user_message or user_message.strip() == "":
        return "您好！請輸入一些內容，我才能為您服務喔。"

    # 1. 嘗試記帳邏輯 (這部分保持不變)
    match_expense = re.search(r'(?:花了|消費|支出|買了|購買)(\d+(?:\.\d+)?)元(.+)', user_message, re.I)
    
    if match_expense:
        try:
            amount = float(match_expense.group(1)) 
            item = match_expense.group(2).strip() 
            
            conn = sqlite3.connect('expenses.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO expenses (amount, item) VALUES (?, ?)", (amount, item))
            conn.commit()
            conn.close()
            # 確保這裡的記帳成功回覆是繁體字
            return f"好的，已為您記錄 {amount} 元購買 {item} 的支出。"
        except ValueError:
            return "對不起，我無法識別您輸入的金額，請確保是有效的數字。"
        except Exception as e:
            print(f"記帳數據庫操作失敗: {e}")
            traceback.print_exc()
            pass 
    
    # 2. 如果不是記帳訊息，或者記帳失敗，則呼叫 Gemini
    try:
        # *** 關鍵修改：在 user_message 前加上繁體中文的提示 ***
        prompt = f"請使用繁體中文回覆。問題：{user_message}"
        response = model.generate_content(prompt) # 將修改後的 prompt 傳入
        return response.text 
    except Exception as e:
        print(f"Gemini API error during content generation: {e}")
        traceback.print_exc() 
        return "對不起，目前AI服務無法回應您的請求，請稍後再試。"

# === Line Bot 的 Webhook 處理部分 (保持不變) ===
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
 
# === 應用程式啟動入口 (新增資料庫初始化) ===
if __name__ == "__main__":
    # 在應用程式啟動時呼叫資料庫初始化
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
