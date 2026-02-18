import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import platform

# 解決 Matplotlib 中文顯示問題
if platform.system() == "Windows":
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
else:
    # Linux / Streamlit Cloud 
    plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei']

plt.rcParams['axes.unicode_minus'] = False # 解決負號無法顯示的問題

# 這是網頁的標題
st.title("🔮 亞當理論 - 第二映像圖產生器")
st.write("輸入股票代號，自動畫出亞當理論的翻轉預測線。")

# 1. 在網頁上建立一個輸入框
user_input = st.text_input("請輸入台股代號 (或輸入中文名稱，如：台積電、長榮)", "2330.TW")
lookback_days = st.slider("亞當翻轉天數 (Lookback Days)", 10, 60, 20)
time_frame = st.selectbox("選擇週期 (Time Frame)", ["日線 (Daily)", "週線 (Weekly)", "月線 (Monthly)"])

import twstock

stock_id = None
if user_input:
    user_input = user_input.strip()
    
    # 先判斷是否為數字或一般代號 (例如 00635U)
    if user_input.upper().endswith(".TW") or user_input.upper().endswith(".TWO"):
        stock_id = user_input
    elif user_input.isascii() and user_input.isalnum():
        stock_id = f"{user_input}.TW"
        st.caption(f"已自動加上後綴: {stock_id}")
    else:
        # 嘗試用 twstock 搜尋中文名稱
        # twstock.codes 是一個 dictionary，key 是代號，value 是 StockCodeInfo (包含 name)
        found = False
        for code, info in twstock.codes.items():
            if info.name == user_input:
                stock_id = f"{code}.TW"
                st.caption(f"已自動轉換為: {stock_id} ({user_input})")
                found = True
                break
        
        if not found:
            st.error(f"找不到「{user_input}」，請確認名稱正確或直接輸入數字代號。")

# 當使用者按下按鈕或輸入完畢後執行
if stock_id:
    # 2. 下載資料
    end_date = datetime.datetime.now()
    
    # 根據週期設定抓取資料的時間長度和頻率
    if "日線" in time_frame:
        start_date = end_date - datetime.timedelta(days=300) # 抓約一年
        interval = "1d"
    elif "週線" in time_frame:
        start_date = end_date - datetime.timedelta(weeks=150) # 抓約三年
        interval = "1wk"
    elif "月線" in time_frame:
        start_date = end_date - datetime.timedelta(days=365*10) # 抓約十年
        interval = "1mo"

    try:
        df = yf.download(stock_id, start=start_date, end=end_date, interval=interval)
        
        if df.empty:
            st.error("找不到股票資料，請檢查代號是否正確 (例如台積電是 2330.TW)。")
        else:
            # 3. 亞當理論運算
            close_price = df['Close']
            # 如果是多層索引 (MultiIndex)，簡化它
            if isinstance(close_price, pd.DataFrame):
                close_price = close_price.iloc[:, 0]
                
            current_price = close_price.iloc[-1]
            last_date = close_price.index[-1]
            
            # 計算均線 (MA)
            ma30 = close_price.rolling(window=30).mean()
            ma50 = close_price.rolling(window=50).mean()
            ma100 = close_price.rolling(window=100).mean()
            
            # 抓取要翻轉的這段資料
            recent_data = close_price.iloc[-lookback_days:]
            
            # 計算翻轉 (這裡用簡單的 list 運算)
            projection = []
            future_dates = []
            
            # 產生未來日期
            for i in range(1, lookback_days + 1):
                # 亞當核心公式：未來 = 現在 + (現在 - 過去)
                past_price = recent_data.iloc[-i] # 倒著取
                proj_price = current_price + (current_price - past_price)
                
                projection.append(proj_price)
                future_dates.append(last_date + datetime.timedelta(days=i))
            
            # 4. 畫圖 (Matplotlib)
            fig, ax = plt.subplots(figsize=(10, 5))
            
            # 畫歷史股價 (黑色)
            plot_range = 90 # 設定畫圖範圍稍微長一點，讓均線更清楚
            ax.plot(close_price.index[-plot_range:], close_price.iloc[-plot_range:], label='歷史走勢', color='black', linewidth=1.5)
            
            # 畫均線
            ax.plot(close_price.index[-plot_range:], ma30.iloc[-plot_range:], label='30MA', color='orange', alpha=0.8, linewidth=1)
            ax.plot(close_price.index[-plot_range:], ma50.iloc[-plot_range:], label='50MA', color='green', alpha=0.8, linewidth=1)
            ax.plot(close_price.index[-plot_range:], ma100.iloc[-plot_range:], label='100MA', color='purple', alpha=0.8, linewidth=1)
            
            # 畫亞當預測線 (紅色虛線)
            ax.plot(future_dates, projection, label='亞當預測 (第二映像)', color='red', linestyle='--', linewidth=1.5)
            
            # 標示今天的十字線
            ax.axvline(x=last_date, color='gray', linestyle=':', alpha=0.5)
            
            ax.legend()
            ax.set_title(f"{stock_id} 亞當理論翻轉圖")
            ax.grid(True, alpha=0.3)
            
            # 5. 把圖秀在 Streamlit 網頁上
            st.pyplot(fig)
            
            st.success(f"目前價格: {current_price:.2f}")

    except Exception as e:
        st.error(f"發生錯誤: {e}")