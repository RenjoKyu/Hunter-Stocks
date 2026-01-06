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
    
    /* Input Field */
    .stTextInput input {
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------
# Sidebar
with st.sidebar:
    st.markdown("### ตั้งค่าระบบ")
    
    symbol_input = st.text_input("ระบุชื่อย่อหุ้น (Ticker)", value="NVDA").upper()
    
    # Default Timeframe = 5y
    period_input = st.selectbox("ระยะเวลาย้อนหลัง", ["1y", "2y", "5y", "10y"], index=2)
    
    st.markdown("---")
    st.markdown("""
    <div style='font-size: 12px; color: #666; font-family: "Prompt";'>
    ตลาด: หุ้นสหรัฐฯ (NASDAQ/NYSE)<br>
    สกุลเงิน: ดอลลาร์สหรัฐ (USD)<br>
    สถานะ: พร้อมใช้งาน
    </div>
    """, unsafe_allow_html=True)
    
    analyze_btn = st.button("เริ่มการวิเคราะห์", type="primary", use_container_width=True)

# -----------------------------------------------------------
# Logic Functions
def get_us_stock_data(symbol, period):
    ticker = yf.Ticker(symbol)
    try:
        # 1. Fetch History first (Most robust check if stock exists)
        df = ticker.history(period=period, interval="1wk")
        
        if df.empty:
            return None, None, "ไม่พบข้อมูล (History Empty)", None

        # 2. Get Info & Price using fast_info (More reliable for price)
        try:
            # fast_info is newer and faster
            currency = ticker.fast_info.currency
            current_price = ticker.fast_info.last_price
        except:
            # Fallback to .info if fast_info fails
            info = ticker.info
            currency = info.get('currency', 'Unknown')
            current_price = info.get('currentPrice', info.get('regularMarketPrice', df['Close'].iloc[-1]))

        # 3. Filter US Only
        if currency != 'USD':
            if currency == 'Unknown' and '.' not in symbol:
                currency = 'USD'
            else:
                return None, None, f"ไม่ใช่หุ้นสหรัฐฯ (ตรวจพบสกุลเงิน: {currency})", None

        # 4. Fetch Full Name (Robust Method)
        # -----------------------------------------------------------
        # ส่วนที่แก้ไข: เพิ่ม Logic การดึงชื่อเต็มให้รัดกุมขึ้น
        try:
            stock_info = ticker.info
            # พยายามดึง longName -> shortName -> symbol ตามลำดับ
            full_name = stock_info.get('longName', stock_info.get('shortName', symbol))
        except Exception:
            # กรณีเชื่อมต่อดึง Info ไม่ได้ ให้ใช้ Symbol แทน
            full_name = symbol
        # -----------------------------------------------------------

        return df, full_name, currency, current_price

    except Exception as e:
        return None, None, f"Error: {str(e)}", None

def calculate_fractal_levels(df):
    levels = []
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
# Main Execution

# Header Section
st.markdown(f"<h2 style='margin-bottom: 0;'>STOCK HUNTER <span style='color:#4CAF50; font-size:20px; font-weight:300;'>/ US</span></h2>", unsafe_allow_html=True)
st.markdown(f"<p style='color:#666; font-size:12px; font-family:monospace;'>แหล่งข้อมูล: YAHOO FINANCE | วันที่: {datetime.now().strftime('%d/%m/%Y')}</p>", unsafe_allow_html=True)
st.markdown("---")

if analyze_btn or symbol_input:
    with st.spinner("กำลังประมวลผลข้อมูล..."):
        # Unpack result
        result = get_us_stock_data(symbol_input, period_input)
        
        # Check Error
        if result[0] is None:
            error_msg = result[2]
            if "ไม่ใช่หุ้นสหรัฐฯ" in str(error_msg):
                st.error(f"ระบบแจ้งเตือน: {error_msg}")
            elif "ไม่พบข้อมูล" in str(error_msg):
                st.error(f"ไม่พบข้อมูล: '{symbol_input}' กรุณาตรวจสอบตัวสะกด")
            else:
                st.error(f"เกิดข้อผิดพลาด: {error_msg}")
        else:
            # Case Success
            df, full_name, currency, current_price = result

            # คำนวณ High/Low 52 สัปดาห์
            one_year_high = df['High'].tail(52).max()
            one_year_low = df['Low'].tail(52).min()
            
            # --- Display Company Name Header ---
            st.markdown(f"""
            <div>
                <div class='company-name'>{full_name}</div>
                <div class='ticker-sub'>{symbol_input} • NASDAQ/NYSE</div>
            </div>
            """, unsafe_allow_html=True)

            # --- Metrics ---
            c1, c2, c3 = st.columns(3)
            c1.metric("ราคาปัจจุบัน (USD)", f"${current_price:,.2f}") 
            c2.metric("สูงสุด 52 สัปดาห์", f"${one_year_high:,.2f}")
            c3.metric("ต่ำสุด 52 สัปดาห์", f"${one_year_low:,.2f}")
            
            st.markdown("---")

            # --- Analysis Section ---
            raw_levels = calculate_fractal_levels(df)
            waiting_levels = [l for l in raw_levels if l[0] < current_price]
            waiting_levels.sort(key=lambda x: x[0], reverse=True)
            top_3 = waiting_levels[:3]

            st.markdown("### แผนกลยุทธ์การลงทุน")
            
            if not top_3:
                st.markdown("""
                <div class="custom-alert">
                    <b>สถานะ: ทำจุดสูงสุดใหม่ (All Time High)</b><br>
                    ราคากำลังทำจุดสูงสุดใหม่ ไม่พบแนวรับที่มีนัยสำคัญในระยะใกล้<br>
                    คำแนะนำ: รอให้ราคาพักตัวสร้างฐาน (Base Formation) ก่อนพิจารณาลงทุน
                </div>
                """, unsafe_allow_html=True)
            else:
                total_strength = sum(l[1] for l in top_3)
                
                # Cards
                for i, (price, count) in enumerate(top_3):
                    weight = round((count / total_strength) * 100)
                    
                    # คำนวณ % ห่างจากราคาปัจจุบัน
                    dist_from_curr = ((price - current_price) / current_price) * 100
                    
                    # คำนวณ % ห่างจากจุดสูงสุด (52 Week High)
                    dist_from_high = ((price - one_year_high) / one_year_high) * 100
                    
                    st.markdown(f"""
                    <div class="strategy-card">
                        <div class="strategy-head">
                            <span class="zone-label">ไม้ที่ {i+1}</span>
                            <span class="weight-label">น้ำหนัก {weight}%</span>
                        </div>
                        <div class="price-large">${price:,.2f}</div>
                        <div style="margin-top: 15px; border-top: 1px solid #333; padding-top: 15px;">
                            <div style="display:flex; justify-content:space-between; color:#bbb; font-size:13px; font-family:'Prompt';">
                                <span>ห่างจากราคาปัจจุบัน: {dist_from_curr:.2f}%</span>
                                <span>ห่างจากจุดสูงสุด: {dist_from_high:.2f}%</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# Legal Disclaimer Section (Footer) 
st.markdown("""
<style>
    .legal-footer {
        margin-top: 80px;
        padding: 30px;
        border-top: 1px solid #262626;
        color: #555;
        font-size: 11.5px;
        line-height: 1.8;
        text-align: justify;
        font-family: 'Prompt', sans-serif;
    }
    .legal-footer b {
        color: #777;
        letter-spacing: 0.5px;
    }
</style>

<div class="legal-footer">
    <b>ข้อจำกัดความรับผิดและคำเตือน (DISCLAIMER):</b><br>
    ข้อมูล บทวิเคราะห์ และแผนกลยุทธ์ที่แสดงผลในระบบนี้ เป็นเพียงผลลัพธ์จากการคำนวณทางสถิติและคณิตศาสตร์จากข้อมูลราคาในอดีต (Technical Analysis) เท่านั้น 
    มุ่งเน้นเพื่อเป็นเครื่องมือประกอบการศึกษาทฤษฎีกราฟ <u>มิใช่คำแนะนำทางการเงิน (Financial Advice)</u> 
    มิใช่การชักชวนหรือชี้นำให้ซื้อขายหลักทรัพย์ และไม่ได้รับประกันผลตอบแทนในอนาคต 
    <br><br>
    การลงทุนในตลาดหลักทรัพย์ต่างประเทศมีความเสี่ยงสูงจากความผันผวนของราคาและอัตราแลกเปลี่ยน 
    ผู้ใช้งานควรศึกษาข้อมูลเชิงลึกเพิ่มเติมจากหลายแหล่งและใช้วิจารณญาณในการตัดสินใจลงทุนด้วยตนเองอย่างรอบคอบ 
    โดยผู้พัฒนาระบบจะไม่รับผิดชอบต่อความเสียหาย หรือการขาดทุนใดๆ ที่เกิดขึ้นจากการนำข้อมูลนี้ไปใช้งานในทุกกรณี
</div>

""", unsafe_allow_html=True)
