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

# Common Taiwan Stocks Dictionary (Hardcoded to avoid scrapping issues)
stock_dict = {
    # 科技權值
    '台積電': '2330', '聯發科': '2454', '鴻海': '2317', '廣達': '2382', '台達電': '2308',
    '聯電': '2303', '日月光': '3711', '大立光': '3008', '研華': '2395', '華碩': '2357',
    '緯創': '3231', '智邦': '2345', '國巨': '2327', '欣興': '3037', '南亞科': '2408',
    '友達': '2409', '群創': '3481', '力積電': '6770', '世界': '5347', '元太': '8069',
    '健策': '3653', '嘉澤': '3533', '祥碩': '5269', '信驊': '5274', '世芯': '3661',
    '創意': '3443', '力旺': '3529', '譜瑞': '4966', '矽力': '6415', '聯詠': '3034', 
    '瑞昱': '2379',
    
    # 金融
    '富邦金': '2881', '國泰金': '2882', '中信金': '2891', '兆豐金': '2886', '玉山金': '2884',
    '第一金': '2892', '合庫金': '5880', '華南金': '2880', '台新金': '2887', '元大金': '2885',
    '永豐金': '2890', '開發金': '2883', '新光金': '2888', '彰銀': '2801', '臺企銀': '2834',
    
    # 傳產/航運/塑化
    '長榮': '2603', '陽明': '2609', '萬海': '2615', '長榮航': '2618', '華航': '2610',
    '台塑': '1301', '南亞': '1303', '台化': '1326', '臺塑化': '6505', '中鋼': '2002',
    '統一': '1216', '台泥': '1101', '亞泥': '1102', '遠東新': '1402', '豐泰': '9910',
    '儒鴻': '1476', '巨大': '9921', '美利達': '9914',
    
    # ETF
    '0050': '0050', '0056': '0056', '00878': '00878', '00929': '00929', '00919': '00919',
    '00635U': '00635U', '元大台灣50': '0050', '元大高股息': '0056'
}

stock_id = None
if user_input:
    user_input = user_input.strip()
    
    # Check if input is in our hardcoded dictionary
    if user_input in stock_dict:
        stock_id = f"{stock_dict[user_input]}.TW"
        st.caption(f"已自動轉換為: {stock_id} ({user_input})")
        
    # Check if numeric input
    elif user_input.isdigit():
        stock_id = f"{user_input}.TW"
        st.caption(f"已自動加上後綴: {stock_id}")
        
    # Check if input looks like an ETF code or has .TW suffix already
    elif user_input.upper().endswith(".TW") or user_input.upper().endswith(".TWO"):
        stock_id = user_input
    elif user_input.isascii() and user_input.isalnum():
         # Assume it's a code like 00635U
        stock_id = f"{user_input}.TW"
        st.caption(f"已自動加上後綴: {stock_id}")
    else:
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