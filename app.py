# ... (app.py 的其他導入和配置，以及 init_db 函數保持不變) ...

# 主要的 AI 回覆邏輯函數
def get_ai_response(user_message):
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

# ... (Line Bot 的 Webhook 處理部分和應用程式啟動入口保持不變) ...
