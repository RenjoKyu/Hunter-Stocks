from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import yfinance as yf
import pandas as pd

# สร้าง instance ของ FastAPI
app = FastAPI(
    title="Stock Hunter US API",
    description="API สำหรับวิเคราะห์แนวรับหุ้น US ด้วย Fractal Theory",
    version="1.0.0"
)

# --- Data Models (Pydantic) สำหรับกำหนดโครงสร้าง Response ---

class SupportLevel(BaseModel):
    rank: int
    price: float
    strength_score: int
    weight_percent: int
    distance_from_current_percent: float
    distance_from_high_percent: float

class StockAnalysisResponse(BaseModel):
    symbol: str
    company_name: str
    currency: str
    current_price: float
    year_high: float
    year_low: float
    status: str
    strategy: List[SupportLevel]

# --- Core Logic Functions (ดึงมาจากโค้ดเดิมและปรับให้เหมาะกับ API) ---

def calculate_fractal_levels(df: pd.DataFrame) -> List[tuple]:
    """คำนวณหาแนวรับตามทฤษฎี Fractal และ Grouping ราคาที่ใกล้เคียงกัน"""
    levels = []
    # Loop หา Fractal Low (Low ต่ำกว่า 2 แท่งก่อนหน้าและ 2 แท่งถัดไป)
    for i in range(2, len(df)-2):
        low_val = df['Low'].iloc[i]
        if low_val < df['Low'].iloc[i-1] and low_val < df['Low'].iloc[i-2] and \
           low_val < df['Low'].iloc[i+1] and low_val < df['Low'].iloc[i+2]:
            levels.append(low_val)
            
    # Grouping ราคาที่ใกล้กัน (Within 5%)
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
            # เก็บค่าเฉลี่ยของกลุ่ม และ จำนวนจุดสัมผัส (ความแข็งแกร่ง)
            consolidated.append((sum(group)/len(group), len(group)))
    return consolidated

# --- API Endpoints ---

@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "active", "message": "Stock Hunter API is running"}

@app.get("/analyze/{symbol}", response_model=StockAnalysisResponse, tags=["Analysis"])
def analyze_stock(
    symbol: str, 
    period: str = Query("5y", enum=["1y", "2y", "5y", "10y"])
):
    symbol = symbol.upper()
    ticker = yf.Ticker(symbol)
    
    try:
        # 1. Fetch History
        df = ticker.history(period=period, interval="1wk")
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"ไม่พบข้อมูลสำหรับหุ้น {symbol}")

        # 2. Get Info & Price
        try:
            currency = ticker.fast_info.currency
            current_price = ticker.fast_info.last_price
        except:
            info = ticker.info
            currency = info.get('currency', 'Unknown')
            current_price = info.get('currentPrice', info.get('regularMarketPrice', df['Close'].iloc[-1]))

        # 3. Filter US Only
        if currency != 'USD':
             # อนุญาตถ้าหาไม่เจอแต่ ticker ไม่มี . (เช่น NVDA)
            if not (currency == 'Unknown' and '.' not in symbol):
                raise HTTPException(status_code=400, detail=f"รองรับเฉพาะหุ้น US (สกุลเงินที่พบ: {currency})")

        # 4. Get Name
        try:
            stock_info = ticker.info
            full_name = stock_info.get('longName') or stock_info.get('shortName') or symbol
        except:
            full_name = symbol

        # 5. Calculate Metrics
        one_year_high = df['High'].tail(52).max()
        one_year_low = df['Low'].tail(52).min()

        # 6. Calculate Strategy (Core Logic)
        raw_levels = calculate_fractal_levels(df)
        
        # กรองเฉพาะราคาที่ต่ำกว่าราคาปัจจุบัน
        waiting_levels = [l for l in raw_levels if l[0] < current_price]
        waiting_levels.sort(key=lambda x: x[0], reverse=True) # เรียงมากไปน้อย
        
        top_3 = waiting_levels[:3]
        total_strength = sum(l[1] for l in top_3)
        
        strategy_response = []
        
        if not top_3:
            status_msg = "All Time High"
        else:
            status_msg = "Active"
            for i, (price, count) in enumerate(top_3):
                weight = round((count / total_strength) * 100) if total_strength > 0 else 0
                dist_curr = ((price - current_price) / current_price) * 100
                dist_high = ((price - one_year_high) / one_year_high) * 100
                
                strategy_response.append(SupportLevel(
                    rank=i+1,
                    price=round(price, 2),
                    strength_score=count,
                    weight_percent=weight,
                    distance_from_current_percent=round(dist_curr, 2),
                    distance_from_high_percent=round(dist_high, 2)
                ))

        return StockAnalysisResponse(
            symbol=symbol,
            company_name=full_name,
            currency=str(currency),
            current_price=round(current_price, 2),
            year_high=round(one_year_high, 2),
            year_low=round(one_year_low, 2),
            status=status_msg,
            strategy=strategy_response
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
