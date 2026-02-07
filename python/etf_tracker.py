"""
3배 레버리지 ETF 추적 모듈 (Bull Only - 인버스 제외)

DD (Drawdown): 52주 최고 종가 대비 현재 하락률
- DD가 -10%이면 고점 대비 10% 하락한 상태
- DD가 0%에 가까울수록 고점 근처
"""
import logging
from typing import List, Dict
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


# 기본 ETF 목록 (미국 3배 Bull Only - 인버스/해외 제외)
DEFAULT_ETF_LIST = [
    # 주요 지수
    "TQQQ",   # ProShares UltraPro QQQ (나스닥 3배)
    "UPRO",   # ProShares UltraPro S&P500 (S&P 3배)
    "SPXL",   # Direxion S&P 500 Bull 3X (S&P 3배)
    "UDOW",   # ProShares UltraPro Dow30 (다우 3배)
    "TNA",    # Direxion Small Cap Bull 3X (소형주 3배)
    "MIDU",   # Direxion Mid Cap Bull 3X (중형주 3배)
    "HIBL",   # Direxion S&P 500 High Beta Bull 3X (고베타 3배)
    # 섹터
    "SOXL",   # Direxion Semiconductor Bull 3X (반도체 3배)
    "TECL",   # Direxion Technology Bull 3X (기술 3배)
    "FNGU",   # MicroSectors FANG+ 3X (빅테크 3배)
    "BULZ",   # MicroSectors Solactive FANG & Innovation 3X (빅테크 3배)
    "WEBL",   # Direxion Internet Bull 3X (인터넷 3배)
    "UBOT",   # Direxion Robotics AI & Automation Bull 3X (로봇/AI 3배)
    "FAS",    # Direxion Financial Bull 3X (금융 3배)
    "DPST",   # Direxion Regional Banks Bull 3X (지방은행 3배)
    "LABU",   # Direxion Biotech Bull 3X (바이오 3배)
    "CURE",   # Direxion Healthcare Bull 3X (헬스케어 3배)
    "PILL",   # Direxion Pharmaceutical Bull 3X (제약 3배)
    "NAIL",   # Direxion Homebuilders Bull 3X (주택건설 3배)
    "DFEN",   # Direxion Aerospace Bull 3X (방산/항공 3배)
    "DUSL",   # Direxion Industrials Bull 3X (산업 3배)
    "TPOR",   # Direxion Transportation Bull 3X (운송 3배)
    "RETL",   # Direxion Retail Bull 3X (리테일 3배)
    "WANT",   # Direxion Consumer Discretionary Bull 3X (소비재 3배)
    "DRN",    # Direxion Real Estate Bull 3X (부동산 3배)
    "UTSL",   # Direxion Utilities Bull 3X (유틸리티 3배)
    # 에너지/원자재
    "ERX",    # Direxion Energy Bull 3X (에너지 3배)
    "GUSH",   # Direxion Oil & Gas E&P Bull 3X (석유/가스 3배)
    "NUGT",   # Direxion Gold Miners Bull 3X (금광주 3배)
    # 채권
    "TMF",    # Direxion Treasury Bull 3X (장기국채 3배)
]


class ETFTracker:
    """3배 레버리지 ETF 추적 클래스"""
    
    def __init__(self, etf_list: List[str] = None):
        """
        초기화
        
        Args:
            etf_list: 추적할 ETF 목록 (기본값: DEFAULT_ETF_LIST)
        """
        self.etf_list = etf_list or DEFAULT_ETF_LIST
    
    def get_etf_data(self, symbol: str) -> Dict:
        """
        ETF 데이터 수집 (Yahoo Finance Chart API v8)

        Args:
            symbol: ETF 티커 기호

        Returns:
            ETF 정보 딕셔너리
        """
        try:
            # Yahoo Finance Chart API v8 (1년 데이터)
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
                logger.warning(f"{symbol}: API 응답 오류 ({response.status_code})")
                return None

            data = response.json()
            result = data.get("chart", {}).get("result", [{}])[0]

            if not result:
                logger.warning(f"{symbol}: 데이터를 가져올 수 없습니다")
                return None

            meta = result.get("meta", {})
            timestamps = result.get("timestamp", [])
            indicators = result.get("indicators", {}).get("quote", [{}])[0]

            closes = indicators.get("close", [])

            # 현재가
            current_price = meta.get("regularMarketPrice", 0)

            # 전일종가 계산 (closes 배열에서 마지막 두 값 사용)
            valid_closes = [c for c in closes if c is not None]
            if len(valid_closes) >= 2:
                previous_close = valid_closes[-2]  # 어제 종가
            else:
                previous_close = current_price

            # 52주 최고 종가, 저가 및 날짜 계산
            high_52w_close = 0
            low_52w_close = float('inf')
            high_52w_date = "N/A"

            for i, c in enumerate(closes):
                if c is not None:
                    if c > high_52w_close:
                        high_52w_close = c
                        if i < len(timestamps):
                            high_52w_date = datetime.fromtimestamp(timestamps[i]).strftime("%Y-%m-%d")
                    if c < low_52w_close:
                        low_52w_close = c

            if high_52w_close == 0:
                high_52w_close = current_price
            if low_52w_close == float('inf'):
                low_52w_close = current_price

            # DD (52주 최고 종가 대비 현재 하락률)
            dd = ((current_price - high_52w_close) / high_52w_close) * 100 if high_52w_close > 0 else 0

            # 52주 저가 대비 상승률
            low_52w_change = ((current_price - low_52w_close) / low_52w_close) * 100 if low_52w_close > 0 else 0

            # 연초 대비 수익률 (YTD)
            ytd_return = 0
            if len(valid_closes) > 200:
                # 대략 연초 가격 (약 252 거래일)
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
                "current_price": round(float(current_price), 2),
                "high_52w": round(float(high_52w_close), 2),
                "low_52w": round(float(low_52w_close), 2),
                "high_52w_date": high_52w_date,
                "dd": round(float(dd), 2),
                "low_52w_change": round(float(low_52w_change), 2),
                "ytd_return": round(float(ytd_return), 2),
                "monthly_return": round(float(monthly_return), 2),
                "daily_change": round(float(daily_change), 2),
                "previous_close": round(float(previous_close), 2),
            }

        except Exception as e:
            logger.error(f"{symbol} 데이터 수집 오류: {e}")
            return None
    
    def get_all_etf_data(self) -> List[Dict]:
        """
        모든 ETF 데이터 수집
        
        Returns:
            ETF 정보 리스트
        """
        all_data = []
        
        for symbol in self.etf_list:
            logger.info(f"{symbol} 데이터 수집 중...")
            data = self.get_etf_data(symbol)
            
            if data:
                all_data.append(data)
        
        return all_data
    
    def format_etf_report(self, etf_data: List[Dict]) -> str:
        """
        ETF 데이터를 포맷된 메시지로 변환 (간결한 형태)

        Args:
            etf_data: ETF 정보 리스트

        Returns:
            포맷된 메시지
        """
        if not etf_data:
            return "ETF 데이터가 없습니다"

        now = datetime.now()
        date_str = now.strftime('%m/%d')

        message = "<b>3xETF 시세알림</b>\n"
        message += f"<b>{date_str}일 마감 종가</b> 📊\n"
        message += "<pre>\n"

        # 상승 종목
        gainers = [e for e in etf_data if e['daily_change'] >= 0]
        losers = [e for e in etf_data if e['daily_change'] < 0]

        # 상승률 순 정렬
        gainers.sort(key=lambda x: x['daily_change'], reverse=True)
        losers.sort(key=lambda x: x['daily_change'])

        # 상승 종목 출력
        for etf in gainers:
            symbol = etf['symbol']
            price = etf['current_price']
            change = etf['daily_change']
            line = f"{symbol:5} ${price:>7.2f} (+{change:>5.2f}%)"
            message += line + "\n"

        if gainers and losers:
            message += "─" * 24 + "\n"

        # 하락 종목 출력
        for etf in losers:
            symbol = etf['symbol']
            price = etf['current_price']
            change = etf['daily_change']
            line = f"{symbol:5} ${price:>7.2f} ({change:>+6.2f}%)"
            message += line + "\n"

        message += "</pre>"

        return message
    
    def add_etf(self, symbol: str) -> bool:
        """
        ETF 추가
        
        Args:
            symbol: ETF 티커 기호
        
        Returns:
            성공 여부
        """
        if symbol not in self.etf_list:
            self.etf_list.append(symbol)
            logger.info(f"{symbol} 추가됨")
            return True
        return False
    
    def remove_etf(self, symbol: str) -> bool:
        """
        ETF 제거
        
        Args:
            symbol: ETF 티커 기호
        
        Returns:
            성공 여부
        """
        if symbol in self.etf_list:
            self.etf_list.remove(symbol)
            logger.info(f"{symbol} 제거됨")
            return True
        return False
