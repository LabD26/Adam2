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
with st.form(key='query_form'):
    user_input = st.text_input("請輸入股票代號或中文名稱 (支援台股如 2330、第一金；美股/ETF 如 AAPL、QQQ、特斯拉)", "2330")
    lookback_days = st.slider("亞當翻轉天數 (Lookback Days)", 10, 60, 20)
    time_frame = st.selectbox("選擇週期 (Time Frame)", ["日線 (Daily)", "週線 (Weekly)", "月線 (Monthly)"])
    backtest_date_input = st.date_input("回測基準日 (Backtest Date) - optional", datetime.date.today())
    submit_button = st.form_submit_button(label='查詢')

# Common Stock Dictionary (Expanded with US Stocks)
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
    
    # ETF (Taiwan)
    '0050': '0050', '0056': '0056', '00878': '00878', '00929': '00929', '00919': '00919',
    '00635U': '00635U', '元大台灣50': '0050', '元大高股息': '0056',
    
    # US Stocks / ETFs
    '蘋果': 'AAPL', '特斯拉': 'TSLA', '輝達': 'NVDA', '微軟': 'MSFT', 
    '納斯達克': 'QQQ', '標普500': 'SPY',
    '波克夏': 'BRK-B', 'BRK': 'BRK-B', 'BRK.B': 'BRK-B', 'BRK/B': 'BRK-B',
    'Google': 'GOOGL', 'Alphabet': 'GOOGL'
}

stock_id = None
if user_input:
    user_input = user_input.strip()
    
    # 1. 查字典 (Dictionary Lookup)
    # 如果在字典裡，先轉換成代號 (例如 '台積電' -> '2330', '蘋果' -> 'AAPL')
    if user_input in stock_dict:
        code = stock_dict[user_input]
    else:
        code = user_input # 不在字典裡，直接使用輸入值
        
    # 2. 智慧判斷 (Smart Logic)
    # 判斷第一個字元
    if len(code) > 0:
        first_char = code[0]
        
        # Case A: 數字開頭 -> 視為台股 (Taiwan Stock)
        if first_char.isdigit():
            # 檢查是否已經有後綴
            code_upper = code.upper()
            if code_upper.endswith(".TW") or code_upper.endswith(".TWO"):
                stock_id = code_upper # 已經有後綴，直接使用
            else:
                stock_id = f"{code}.TW" # 自動加上 .TW
                
            if user_input != stock_id:
                st.caption(f"已自動轉換為: {stock_id}")
                
        # Case B: 英文字母開頭 -> 視為美股 (US Stock)
        elif first_char.isalpha():
            stock_id = code.upper().replace('.', '-').replace('/', '-') # 自動將 . 或 / 替換為 - (Yahoo Finance 格式)
            if user_input != stock_id:
                st.caption(f"已自動轉換為: {stock_id}")
                
        # Case C: 其他狀況 (防呆)
        else:
            st.error(f"無法辨識「{user_input}」，請輸入正確的股號或名稱。")
    

# 當使用者按下按鈕或輸入完畢後執行
if stock_id:
    # 2. 下載資料 (抓到今天為止的完整資料，用來對照)
    end_date = datetime.datetime.now()
    
    # 根據週期設定抓取資料的時間長度和頻率
    if "日線" in time_frame:
        start_date = end_date - datetime.timedelta(days=365*2) # 抓多一點確保回測夠用
        interval = "1d"
    elif "週線" in time_frame:
        start_date = end_date - datetime.timedelta(weeks=150*2)
        interval = "1wk"
    elif "月線" in time_frame:
        start_date = end_date - datetime.timedelta(days=365*20)
        interval = "1mo"

    try:
        df = yf.download(stock_id, start=start_date, end=end_date, interval=interval)
        
        if df.empty:
            st.error("找不到股票資料，請檢查代號是否正確 (例如台積電是 2330.TW)。")
        else:
            # 處理 MultiIndex (如有)
            close_price_full = df['Close']
            if isinstance(close_price_full, pd.DataFrame):
                close_price_full = close_price_full.iloc[:, 0]
            
            # --- 以下是根據回測日期切割資料的邏輯 ---
            
            # 將使用者選擇的 date 轉成 datetime (比較好跟 index 比對)
            # 因為 yfinance 下載的 index 通常是 timestamp
            backtest_datetime = pd.Timestamp(datetime.datetime.combine(backtest_date_input, datetime.time.max))
            
            # 1. 真實走勢 (全部資料) -> 用來畫黑線
            # close_price_full 已經是這個了
            
            # 2. 運算用資料 (只取到回測基準日) -> 用來算亞當
            calc_data = close_price_full[close_price_full.index <= backtest_datetime]
            
            if calc_data.empty or len(calc_data) < lookback_days:
                st.error("您選擇的回測基準日太早，在此日期之前沒有足夠的歷史資料進行計算。")
            else:
                # 3. 亞當理論運算 (全部使用 calc_data)
                current_price = calc_data.iloc[-1]
                last_date = calc_data.index[-1] # 這應該就是回測基準日附近的最後交易日
                
                # 計算均線 (MA) - 用全部資料計算比較有連貫性，但畫圖時可以全畫
                ma30 = close_price_full.rolling(window=30).mean()
                ma50 = close_price_full.rolling(window=50).mean()
                ma100 = close_price_full.rolling(window=100).mean()
                
                # 抓取要翻轉的這段資料 (從 calc_data 裡抓)
                recent_data = calc_data.iloc[-lookback_days:]
                
                # 計算翻轉
                projection = []
                future_dates = []
                
                # 產生未來日期
                for i in range(1, lookback_days + 1):
                    # 亞當核心公式：未來 = 現在 + (現在 - 過去)
                    past_price = recent_data.iloc[-i] # 倒著取
                    proj_price = current_price + (current_price - past_price)
                    
                    projection.append(proj_price)
                    # 這裡的 last_date 是回測基準日，所以預測線會從回測日往未來跑
                    future_dates.append(last_date + datetime.timedelta(days=i))
                
                # 4. 畫圖 (Matplotlib)
                fig, ax = plt.subplots(figsize=(10, 5))
                
                # 畫歷史股價 (黑色) - 畫出完整走勢 (包含回測日之後的真實狀況)
                # 設定畫圖範圍：顯示回測日前後一段時間
                # 我們希望看到回測點之前 lookback_days * 1.5 天，以及之後的所有天
                # 先找出回測點在 full data 中的位置
                
                # 這裡簡單抓一個範圍，例如回測日前 60 天開始畫
                # 找出 calc_data 在 full data 的長度
                split_idx = len(calc_data)
                start_plot_idx = max(0, split_idx - 60)
                
                plot_data = close_price_full.iloc[start_plot_idx:]
                
                ax.plot(plot_data.index, plot_data, label='真實走勢 (Real)', color='black', linewidth=1.5)
                
                # 畫均線
                ax.plot(plot_data.index, ma30.iloc[start_plot_idx:], label='30MA', color='orange', alpha=0.8, linewidth=1)
                ax.plot(plot_data.index, ma50.iloc[start_plot_idx:], label='50MA', color='green', alpha=0.8, linewidth=1)
                ax.plot(plot_data.index, ma100.iloc[start_plot_idx:], label='100MA', color='purple', alpha=0.8, linewidth=1)
                
                # 畫亞當預測線 (紅色虛線)
                ax.plot(future_dates, projection, label='亞當預測 (Prediction)', color='red', linestyle='--', linewidth=1.5)
                
                # 標示回測基準日 (藍色點斷線)
                ax.axvline(x=last_date, color='blue', linestyle='-.', alpha=0.8, label='回測起點 (Start)')
                
                ax.legend()
                ax.set_title(f"{stock_id} 亞當理論翻轉 (基準日: {last_date.date()})")
                ax.grid(True, alpha=0.3)
                
                # 5. 把圖秀在 Streamlit 網頁上
                st.pyplot(fig)
                
                st.info(f"回測基準價 ({last_date.date()}): {current_price:.2f}")
                st.success(f"目前最新價 ({close_price_full.index[-1].date()}): {close_price_full.iloc[-1]:.2f}")

    except Exception as e:
        st.error(f"發生錯誤: {e}")