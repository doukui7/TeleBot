"""
배당주 모니터링 및 브리핑 모듈
"""
import logging
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)

@dataclass
class DividendInfo:
    symbol: str
    name: str
    price: float
    dividend_yield: float  # % 단위
    ex_dividend_date: Optional[str] = None  # YYYY-MM-DD
    pay_date: Optional[str] = None  # YYYY-MM-DD
    
class DividendMonitor:
    """배당주 및 배당 ETF 모니터링 클래스"""
    
    # 모니터링할 배당 ETF 및 종목 목록
    DIVIDEND_ETFS = {
        "SCHD": "Schwab US Dividend Equity",
        "VYM": "Vanguard High Dividend Yield",
        "HDV": "iShares Core High Dividend",
        "JEPI": "JPMorgan Equity Premium Income",
        "JEPQ": "JPMorgan Nasdaq Equity Premium",
        "DIVO": "Amplify CWP Enhanced Dividend",
        "O": "Realty Income (Monthly)"
    }

    def __init__(self):
        pass
        
    def fetch_dividend_data(self) -> List[DividendInfo]:
        """
        배당주 데이터 수집
        """
        results = []
        symbols = list(self.DIVIDEND_ETFS.keys())
        
        try:
            # yfinance로 데이터 일괄 조회 (효율성)
            # Tickers 객체 생성
            tickers = yf.Tickers(" ".join(symbols))
            
            for symbol, name in self.DIVIDEND_ETFS.items():
                try:
                    ticker = tickers.tickers[symbol]
                    info = ticker.info
                    
                    # 현재가
                    price = info.get('regularMarketPrice') or info.get('currentPrice') or info.get('previousClose') or 0
                    
                    # 배당 수익률 (trailingAnnualDividendYield 또는 dividendYield)
                    # yfinance는 소수점 단위로 반환 (0.0345 -> 3.45%)
                    yield_val = info.get('dividendYield')
                    if yield_val is None:
                        yield_val = info.get('trailingAnnualDividendYield', 0)
                    
                    dividend_yield = yield_val * 100 if yield_val else 0
                    
                    # 배당락일 (timestamp to string)
                    ex_div_date_ts = info.get('exDividendDate')
                    ex_div_date = None
                    if ex_div_date_ts:
                        ex_div_date = datetime.fromtimestamp(ex_div_date_ts).strftime('%Y-%m-%d')
                        
                    # 지급일
                    pay_date_ts = info.get('dividendDate') # 어떤 티커는 dividendDate 사용
                    pay_date = None
                    if pay_date_ts:
                        pay_date = datetime.fromtimestamp(pay_date_ts).strftime('%Y-%m-%d')
                        
                    results.append(DividendInfo(
                        symbol=symbol,
                        name=name,
                        price=price,
                        dividend_yield=dividend_yield,
                        ex_dividend_date=ex_div_date,
                        pay_date=pay_date
                    ))
                    
                except Exception as e:
                    logger.error(f"{symbol} 데이터 수집 실패: {e}")
                    # 실패해도 다른 종목 계속 진행
                    continue
                    
            # 수익률 순으로 정렬
            results.sort(key=lambda x: x.dividend_yield, reverse=True)
            return results
            
        except Exception as e:
            logger.error(f"배당 데이터 전체 조회 실패: {e}")
            return []

    def format_dividend_briefing(self, data: List[DividendInfo]) -> str:
        """
        배당 브리핑 메시지 포맷팅 (HTML)
        """
        if not data:
            return ""
            
        now = datetime.now()
        date_str = now.strftime("%Y년 %m월 %d일")
        
        message = f"💰 <b>배당주 ETF 현황</b>\n"
        message += f"<pre>{date_str} 기준</pre>\n\n"
        
        # 헤더
        message += f"<b>{'종목':<5} {'가격':<8} {'수익률':<6} {'배당락일':<10}</b>\n"
        message += "-" * 35 + "\n"
        
        for item in data:
            # 수익률 표기 (연 % 단위)
            yield_str = f"{item.dividend_yield:.1f}%"
            
            # 배당락일 (없으면 -)
            ex_date = item.ex_dividend_date[5:] if item.ex_dividend_date else "-" 
            
            # 배당락일이 다가오는지 체크 (7일 이내면 강조)
            is_upcoming = False
            if item.ex_dividend_date:
                try:
                    ex_dt = datetime.strptime(item.ex_dividend_date, "%Y-%m-%d")
                    # 오늘 ~ 7일 후 사이
                    if now <= ex_dt <= now + timedelta(days=7):
                        is_upcoming = True
                except:
                    pass
            
            # 심볼 강조 (배당락 임박 시)
            symbol_str = f"{item.symbol}"
            if is_upcoming:
                 symbol_str = f"🚨{symbol_str}"
            
            # 표 형태로 줄 맞춤 (HTML에서는 pre 태그 사용 권장되나 여기선 텍스트 정렬 시도)
            # 모바일 가독성을 위해 간소화
            row = f"<b>{symbol_str:<5}</b> ${item.price:<7.2f} {yield_str:<6} {ex_date}\n"
            message += row
            
        message += "\n"
        message += "📢 <i>수익률은 연간 예상 배당률(TTM) 기준입니다.</i>\n"
        message += "⚡ <i>배당락일(Ex-Date) 전일까지 매수해야 배당을 받을 수 있습니다.</i>"
        
        return message
