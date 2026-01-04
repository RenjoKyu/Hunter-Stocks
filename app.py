import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime


st.set_page_config(page_title="Stock Hunter", page_icon="📈")


st.title("Stock Hunter Pro")
st.caption("ระบบค้นหาแนวรับเชิงกลยุทธ์ (Price Action & Fractal)")


with st.expander("⚠️ อ่านคำเตือนความเสี่ยง (Disclaimer)", expanded=True):
    st.error("""
    **คำเตือนสำคัญ:**
    1. ข้อมูลนี้เป็นเพียงการคำนวณทางสถิติจากราคาในอดีต **ไม่ใช่** คำแนะนำในการลงทุน (Financial Advice)
    2. การลงทุนมีความเสี่ยง ผู้ใช้งานควรใช้วิจารณญาณและรับผิดชอบผลการลงทุนด้วยตนเอง
    3. ข้อมูลอาจมีความล่าช้า (Delay) ขึ้นอยู่กับแหล่งข้อมูลต้นทาง (Yahoo Finance)
    """)
# --------------------------------

st.markdown("---")


symbol_input = st.text_input("ป้อนชื่อหุ้น (เช่น NVDA, TSLA, AAPL):", value="NVDA")


def analyze_stock(symbol):
    search_date = datetime.now().strftime("%d/%m/%Y")
    
    ticker = yf.Ticker(symbol.upper())
    
    try:
        info = ticker.info
        full_name = info.get('longName', 'ไม่พบชื่อบริษัท')
    except:
        full_name = "ไม่สามารถดึงข้อมูลชื่อบริษัทได้"

    # ดึงข้อมูล
    with st.spinner(f"กำลังเจาะลึกข้อมูล {full_name}..."):
        df = ticker.history(period="5y", interval="1wk")
    
    if df.empty:
        st.error(f"❌ ไม่พบข้อมูลหุ้น '{symbol.upper()}' กรุณาตรวจสอบตัวสะกดครับ")
        return

    current_price = df['Close'].iloc[-1]
    
    # คำนวณ High/Low 52 สัปดาห์
    one_year_df = df.tail(52)
    one_year_high = one_year_df['High'].max()
    one_year_low = one_year_df['Low'].min()

    st.success(f"📅 วันที่วิเคราะห์: {search_date}")

    # แสดงข้อมูลพื้นฐาน
    st.subheader(f"🏢 {full_name} ({symbol.upper()})")
    col1, col2, col3 = st.columns(3)
    col1.metric("ราคาปัจจุบัน", f"${current_price:.2f}")
    col2.metric("สูงสุด 52 สัปดาห์", f"${one_year_high:.2f}")
    col3.metric("ต่ำสุด 52 สัปดาห์", f"${one_year_low:.2f}")
    
    # Logic หาแนวรับ (Fractal)
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
            
    waiting = [l for l in consolidated if l[0] < current_price]
    waiting.sort(key=lambda x: x[0], reverse=True)
    top_3 = waiting[:3]
    
    if not top_3:
        st.warning("📊 ราคาปัจจุบันอยู่ต่ำที่สุดในรอบ 5 ปีแล้ว หรือไม่พบแนวรับที่ชัดเจน")
        return

    total_strength = sum(l[1] for l in top_3)
    
    st.markdown("### 🎯 แผนการเข้าซื้อ (Strategic Plan)")

    for i, (price, count) in enumerate(top_3):
        discount_pct = ((one_year_high - price) / one_year_high) * 100
        weight = round((count / total_strength) * 100)
        gap = ((current_price - price) / current_price) * 100
        
        # การแสดงผลแบบ Card
        with st.container():
            st.markdown(f"**📍 ไม้ที่ {i+1} : ${price:.2f}**")
            st.progress(weight)
            st.caption(f"ความหนักของไม้: {weight}% (อิงจากความแข็งแกร่งของฐาน)")
            
            c1, c2 = st.columns(2)
            c1.write(f"- ถูกกว่าจุดสูงสุดปีนี้: -{discount_pct:.1f}%")
            c2.write(f"- ห่างจากราคาปัจจุบัน: -{gap:.1f}%")
            st.markdown("---")
            
 
    st.info("💡 ข้อแนะนำ: ราคาสูงสุด/ต่ำสุดรอบปี ช่วยให้คุณห็นกรอบการวิ่งของหุ้นในรอบปีล่าสุดครับ")

# ปุ่มกด
if st.button("🚀 เริ่มวิเคราะห์", type="primary"):
    analyze_stock(symbol_input)
else:
    st.write("กดปุ่มเพื่อเริ่มคำนวณครับ")




