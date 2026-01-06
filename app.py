import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. Page Configuration
st.set_page_config(
    page_title="Stock Hunter: US",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS (Strictly No Emoji / Terminal Style)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');

    /* Global Settings */
    .stApp {
        font-family: 'Prompt', sans-serif;
        background-color: #0e1117;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5 {
        font-weight: 600;
        letter-spacing: -0.5px;
        color: #f0f2f6;
    }
    
    /* Metrics */
    div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 26px;
        font-weight: 700;
        color: #fff;
    }
    div[data-testid="stMetricLabel"] {
        font-family: 'Prompt', sans-serif;
        font-size: 14px;
        color: #888;
    }

    /* Strategy Card */
    .strategy-card {
        background: linear-gradient(145deg, #1a1c24, #13151b);
        border: 1px solid #333;
        padding: 24px;
        border-radius: 6px;
        margin-bottom: 16px;
    }
    .strategy-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        border-bottom: 1px solid #2d2d2d;
        padding-bottom: 10px;
    }
    .zone-label {
        color: #aaa;
        font-size: 14px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .weight-label {
        color: #4CAF50;
        font-size: 14px;
        font-family: 'Prompt', sans-serif;
    }
    .price-large {
        font-family: 'JetBrains Mono', monospace;
        font-size: 36px;
        color: #e0e0e0;
        font-weight: 600;
        margin: 10px 0;
    }
    .company-name {
        font-size: 28px;
        color: #ffffff;
        margin-top: 10px;
        margin-bottom: 5px;
        font-weight: 600;
    }
    .ticker-sub {
        font-family: 'JetBrains Mono', monospace;
        font-size: 16px;
        color: #4CAF50;
        margin-bottom: 20px;
    }
    
    /* Custom Alert Box */
    .custom-alert {
        padding: 15px;
        border-left: 3px solid #FFC107;
        background-color: rgba(255, 193, 7, 0.1);
        color: #e0e0e0;
        font-size: 14px;
        margin-bottom: 20px;
    }

    /* Legal Disclaimer Footer */
    .legal-footer {
        margin-top: 40px;
        padding: 20px;
        border-top: 1px solid #333;
        color: #555;
        font-size: 11px;
        font-family: 'Prompt', sans-serif;
        text-align: justify;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------
# Logic Functions
def get_us_stock_data(symbol, period):
    ticker = yf.Ticker(symbol)
    try:
        # 1. ดึง History เพื่อเช็คว่าหุ้นมีตัวตนหรือไม่
        df = ticker.history(period=period, interval="1wk")
        
        if df.empty:
            return None, None, "ไม่พบข้อมูลหุ้นตัวนี้", None

        # 2. ดึงราคาและสกุลเงิน (ใช้ fast_info ก่อนเพื่อความเร็ว)
        try:
            currency = ticker.fast_info.currency
            current_price = ticker.fast_info.last_price
        except:
            # Fallback หาก fast_info มีปัญหา
            info = ticker.info
            currency = info.get('currency', 'Unknown')
            current_price = info.get('currentPrice') or info.get('regularMarketPrice') or df['Close'].iloc[-1]

        # 3. กรองเฉพาะหุ้นสหรัฐฯ (USD)
        if currency != 'USD':
            if currency == 'Unknown' and '.' not in symbol:
                currency = 'USD'
            else:
                return None, None, f"ระบบรองรับเฉพาะหุ้นสหรัฐฯ (พบ: {currency})", None

        # 4. ส่วนสำคัญ: ดึงชื่อเต็ม (ใช้ Logic 'or' เพื่อป้องกันค่า None)
        try:
            full_name = ticker.info.get('longName') or ticker.info.get('shortName') or symbol
        except:
            full_name = symbol

        return df, full_name, currency, current_price

    except Exception as e:
        return None, None, f"ข้อผิดพลาด: {str(e)}", None

def calculate_fractal_levels(df):
    levels = []
    # Logic หาแนวรับแบบ Fractal
    for i in range(2, len(df)-2):
        low_val = df['Low'].iloc[i]
        if low_val < df['Low'].iloc[i-1] and low_val < df['Low'].iloc[i-2] and \
           low_val < df['Low'].iloc[i+1] and low_val < df['Low'].iloc[i+2]:
            levels.append(low_val)
            
    consolidated = []
    if levels:
        levels.sort()
        while levels:
            base = levels.pop(0)
            group = [base]
            keep = []
            for x in levels:
                if x <= base * 1.05:
                    group.append(x)
                else:
                    keep.append(x)
            levels = keep
            consolidated.append((sum(group)/len(group), len(group)))
    return consolidated

# -----------------------------------------------------------
# Sidebar UI
with st.sidebar:
    st.markdown("### ตั้งค่าระบบ")
    symbol_input = st.text_input("ระบุชื่อย่อหุ้น (Ticker)", value="NVDA").upper()
    period_input = st.selectbox("ระยะเวลาย้อนหลัง", ["1y", "2y", "5y", "10y"], index=2)
    st.markdown("---")
    st.markdown("""
    <div style='font-size: 12px; color: #666; font-family: "Prompt";'>
    ตลาด: US Stock Market<br>
    แหล่งข้อมูล: Yahoo Finance
    </div>
    """, unsafe_allow_html=True)
    analyze_btn = st.button("เริ่มการวิเคราะห์", type="primary", use_container_width=True)

# -----------------------------------------------------------
# Main Execution UI
st.markdown(f"<h2 style='margin-bottom: 0;'>STOCK HUNTER <span style='color:#4CAF50; font-size:20px; font-weight:300;'>/ US</span></h2>", unsafe_allow_html=True)
st.markdown(f"<p style='color:#666; font-size:12px; font-family:monospace;'>UPDATE: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>", unsafe_allow_html=True)
st.markdown("---")

if analyze_btn or symbol_input:
    with st.spinner("กำลังดึงข้อมูลจากตลาด..."):
        df, full_name, currency, current_price = get_us_stock_data(symbol_input, period_input)
        
        if df is None:
            # full_name ในที่นี้จะกลายเป็น error_msg จากการ unpack
            st.error(f"{currency}") 
        else:
            # แสดงชื่อบริษัทเต็มๆ
            st.markdown(f"""
            <div>
                <div class='company-name'>{full_name}</div>
                <div class='ticker-sub'>{symbol_input} • USD</div>
            </div>
            """, unsafe_allow_html=True)

            # แสดง Metrics
            one_year_high = df['High'].tail(52).max()
            one_year_low = df['Low'].tail(52).min()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("ราคาปัจจุบัน", f"${current_price:,.2f}") 
            c2.metric("สูงสุด 52 สัปดาห์", f"${one_year_high:,.2f}")
            c3.metric("ต่ำสุด 52 สัปดาห์", f"${one_year_low:,.2f}")
            
            st.markdown("---")

            # แผนกลยุทธ์
            st.markdown("### แผนกลยุทธ์การลงทุน")
            raw_levels = calculate_fractal_levels(df)
            waiting_levels = sorted([l for l in raw_levels if l[0] < current_price], key=lambda x: x[0], reverse=True)
            top_3 = waiting_levels[:3]

            if not top_3:
                st.markdown('<div class="custom-alert"><b>สถานะ: Bullish</b><br>หุ้นกำลังทำ All Time High หรือไม่พบแนวรับใกล้เคียง</div>', unsafe_allow_html=True)
            else:
                total_strength = sum(l[1] for l in top_3)
                for i, (price, count) in enumerate(top_3):
                    weight = round((count / total_strength) * 100)
                    dist_curr = ((price - current_price) / current_price) * 100
                    dist_high = ((price - one_year_high) / one_year_high) * 100
                    
                    st.markdown(f"""
                    <div class="strategy-card">
                        <div class="strategy-head">
                            <span class="zone-label">ไม้ที่ {i+1}</span>
                            <span class="weight-label">สัดส่วน {weight}%</span>
                        </div>
                        <div class="price-large">${price:,.2f}</div>
                        <div style="margin-top: 15px; border-top: 1px solid #333; padding-top: 15px;">
                            <div style="display:flex; justify-content:space-between; color:#bbb; font-size:13px; font-family:'Prompt';">
                                <span>ห่างจากราคาปัจจุบัน: {dist_curr:.2f}%</span>
                                <span>ห่างจากจุดสูงสุด: {dist_high:.2f}%</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="legal-footer">
    <b>DISCLAIMER:</b> ข้อมูลนี้เป็นเพียงการวิเคราะห์ทางสถิติ มิใช่คำแนะนำทางการเงิน ผู้ลงทุนควรตัดสินใจด้วยตนเอง
</div>
""", unsafe_allow_html=True)
