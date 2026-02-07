"""
주요 시장지수 추적 모듈
나스닥, S&P500, 비트코인, 코스피, 코스닥, SOXX 등
"""
import logging
from typing import Dict, Optional
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

# 주요 지수 리스트
MAJOR_INDICES = {
    "^IXIC": "나스닥",      # Nasdaq Composite
    "^GSPC": "S&P500",      # S&P 500
    "BTC-USD": "비트코인",  # Bitcoin
    "^KS11": "코스피",      # KOSPI
    "^KQ11": "코스닥",      # KOSDAQ
    "^SOX": "SOXX",         # Semiconductor Index
}


class MarketIndexTracker:
    """시장 지수 추적 클래스"""
    
    def __init__(self):
        """초기화"""
        self.indices = MAJOR_INDICES
    
    def get_index_data(self, symbol: str, name: str) -> Optional[Dict]:
        """
        지수 데이터 수집 (Yahoo Finance Chart API)
        
        Args:
            symbol: 지수 티커 기호
            name: 지수 이름
        
        Returns:
            지수 정보 딕셔너리
        """
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                "interval": "1d",
                "range": "1y"
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"{name}({symbol}): API 응답 오류 ({response.status_code})")
                return None
            
            data = response.json()
            result = data.get("chart", {}).get("result", [{}])[0]
            
            if not result:
                logger.warning(f"{name}({symbol}): 데이터를 가져올 수 없습니다")
                return None
            
            meta = result.get("meta", {})
            timestamps = result.get("timestamp", [])
            indicators = result.get("indicators", {}).get("quote", [{}])[0]
            
            closes = indicators.get("close", [])
            
            # 현재가
            current_price = meta.get("regularMarketPrice", 0)
            
            # 전일종가 계산
            valid_closes = [c for c in closes if c is not None]
            if len(valid_closes) >= 2:
                previous_close = valid_closes[-2]
            else:
                previous_close = current_price
            
            # 52주 최고가 및 저가
            high_52w = 0
            low_52w = float('inf')
            high_52w_date = "N/A"
            
            for i, c in enumerate(closes):
                if c is not None:
                    if c > high_52w:
                        high_52w = c
                        if i < len(timestamps):
                            high_52w_date = datetime.fromtimestamp(timestamps[i]).strftime("%Y-%m-%d")
                    if c < low_52w:
                        low_52w = c
            
            if high_52w == 0:
                high_52w = current_price
            if low_52w == float('inf'):
                low_52w = current_price
            
            # DD (52주 최고가 대비 현재 하락률)
            dd = ((current_price - high_52w) / high_52w) * 100 if high_52w > 0 else 0
            
            # 52주 저가 대비 상승률
            low_52w_change = ((current_price - low_52w) / low_52w) * 100 if low_52w > 0 else 0
            
            # YTD 수익률
            ytd_return = 0
            if len(valid_closes) > 200:
                year_start_idx = max(0, len(valid_closes) - 252)
                year_start_price = valid_closes[year_start_idx]
                if year_start_price > 0:
                    ytd_return = ((current_price - year_start_price) / year_start_price) * 100
            
            # 월간 수익률 (최근 21 거래일)
            monthly_return = 0
            if len(valid_closes) > 21:
                month_ago_price = valid_closes[-22]
                if month_ago_price > 0:
                    monthly_return = ((current_price - month_ago_price) / month_ago_price) * 100
            
            # 전일 변동률
            daily_change = ((current_price - previous_close) / previous_close) * 100 if previous_close > 0 else 0
            
            return {
                "symbol": symbol,
                "name": name,
                "current_price": round(float(current_price), 2),
                "high_52w": round(float(high_52w), 2),
                "low_52w": round(float(low_52w), 2),
                "high_52w_date": high_52w_date,
                "dd": round(float(dd), 2),
                "low_52w_change": round(float(low_52w_change), 2),
                "ytd_return": round(float(ytd_return), 2),
                "monthly_return": round(float(monthly_return), 2),
                "daily_change": round(float(daily_change), 2),
                "previous_close": round(float(previous_close), 2),
            }
        
        except Exception as e:
            logger.error(f"{name}({symbol}) 데이터 수집 오류: {e}")
            return None
    
    def get_all_indices_data(self) -> Dict[str, Dict]:
        """
        모든 지수 데이터 수집
        
        Returns:
            지수 정보 딕셔너리 (symbol -> data)
        """
        all_data = {}
        
        for symbol, name in self.indices.items():
            logger.info(f"{name}({symbol}) 데이터 수집 중...")
            data = self.get_index_data(symbol, name)
            
            if data:
                all_data[symbol] = data
        
        return all_data
