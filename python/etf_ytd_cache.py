"""
배당 ETF YTD 데이터만 별도로 가져오는 함수
"""
import yfinance as yf
import logging
from typing import Dict

logger = logging.getLogger(__name__)

def get_etf_ytd_data() -> Dict[str, float]:
    """
    배당 ETF의 YTD 성과를 별도로 계산 (캐싱 가능)
    """
    etf_symbols = ["SCHD", "VYM", "DGRO", "NOBL", "VIG", "HDV"]
    ytd_data = {}
    
    for symbol in etf_symbols:
        try:
            ticker = yf.Ticker(symbol)
            # 1월 2일부터 현재까지
            hist = ticker.history(start="2026-01-02", period="1mo")
            if len(hist) >= 2:
                year_start = hist.iloc[0]['Close']
                current = hist.iloc[-1]['Close']
                ytd_pct = ((current - year_start) / year_start) * 100
                ytd_data[symbol] = ytd_pct
                print(f"{symbol}: YTD {ytd_pct:+.2f}%")
        except Exception as e:
            logger.error(f"YTD fetch failed for {symbol}: {e}")
    
    return ytd_data

if __name__ == "__main__":
    print("\nYTD 데이터 수집 중...\n")
    data = get_etf_ytd_data()
    print(f"\n수집 완료: {len(data)}개 ETF")
