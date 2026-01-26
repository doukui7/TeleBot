"""
주가 변동 모니터링 모듈
- 지수 (코스피, 나스닥, S&P 500) 및 비트코인: 2% 이상 변동 시 알림
- S&P 100 개별주 및 3x 레버리지 ETF: 10% 이상 변동 시 알림
- 당일 같은 종목에 대해 중복 알림 방지
"""
import logging
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class PriceChange:
    """주가 변동 정보"""
    symbol: str
    name: str
    current_price: float
    previous_close: float
    change_percent: float
    category: str  # 'index', 'stock', 'etf', 'crypto'


class StockMonitor:
    """주가 변동 모니터링 클래스"""

    # 지수 (1% 이상 변동 시 알림)
    INDICES = {
        "^KS11": "코스피 (KOSPI)",
        "^IXIC": "나스닥 (NASDAQ)",
        "^GSPC": "S&P 500",
        "NQ=F": "나스닥 선물",
    }

    # 비트코인만 감시 (2% 이상 변동 시 알림)
    CRYPTO = {
        "BTC-USD": "비트코인 (Bitcoin)",
    }

    # 환율
    CURRENCIES = {
        "KRW=X": "원/달러 환율",
    }

    # S&P 100 종목 (5% 이상 변동 시 알림)
    US_TOP_STOCKS = {
        # Technology
        "AAPL": "Apple",
        "MSFT": "Microsoft",
        "GOOGL": "Alphabet (Google)",
        "NVDA": "NVIDIA",
        "META": "Meta (Facebook)",
        "AVGO": "Broadcom",
        "CSCO": "Cisco",
        "ADBE": "Adobe",
        "CRM": "Salesforce",
        "ORCL": "Oracle",
        "ACN": "Accenture",
        "IBM": "IBM",
        "INTC": "Intel",
        "AMD": "AMD",
        "QCOM": "Qualcomm",
        "TXN": "Texas Instruments",
        # Consumer
        "AMZN": "Amazon",
        "TSLA": "Tesla",
        "HD": "Home Depot",
        "MCD": "McDonald's",
        "NKE": "Nike",
        "SBUX": "Starbucks",
        "LOW": "Lowe's",
        "TGT": "Target",
        "COST": "Costco",
        "WMT": "Walmart",
        "PG": "Procter & Gamble",
        "KO": "Coca-Cola",
        "PEP": "PepsiCo",
        "MDLZ": "Mondelez",
        "CL": "Colgate-Palmolive",
        "KHC": "Kraft Heinz",
        # Communication
        "NFLX": "Netflix",
        "DIS": "Disney",
        "CMCSA": "Comcast",
        "CHTR": "Charter",
        "T": "AT&T",
        "VZ": "Verizon",
        "TMUS": "T-Mobile",
        # Healthcare
        "UNH": "UnitedHealth",
        "JNJ": "Johnson & Johnson",
        "LLY": "Eli Lilly",
        "MRK": "Merck",
        "ABBV": "AbbVie",
        "PFE": "Pfizer",
        "TMO": "Thermo Fisher",
        "ABT": "Abbott",
        "DHR": "Danaher",
        "BMY": "Bristol-Myers Squibb",
        "AMGN": "Amgen",
        "GILD": "Gilead Sciences",
        "MDT": "Medtronic",
        "CVS": "CVS Health",
        # Financial
        "BRK-B": "Berkshire Hathaway",
        "JPM": "JPMorgan Chase",
        "V": "Visa",
        "MA": "Mastercard",
        "BAC": "Bank of America",
        "WFC": "Wells Fargo",
        "GS": "Goldman Sachs",
        "MS": "Morgan Stanley",
        "C": "Citigroup",
        "SCHW": "Charles Schwab",
        "BLK": "BlackRock",
        "AXP": "American Express",
        "BK": "Bank of New York",
        "USB": "U.S. Bancorp",
        "COF": "Capital One",
        "MET": "MetLife",
        "AIG": "AIG",
        "SPG": "Simon Property",
        # Industrial
        "BA": "Boeing",
        "HON": "Honeywell",
        "UNP": "Union Pacific",
        "RTX": "Raytheon",
        "CAT": "Caterpillar",
        "GE": "GE Aerospace",
        "LMT": "Lockheed Martin",
        "GD": "General Dynamics",
        "UPS": "UPS",
        "FDX": "FedEx",
        "EMR": "Emerson Electric",
        "MMM": "3M",
        # Energy
        "XOM": "Exxon Mobil",
        "CVX": "Chevron",
        "COP": "ConocoPhillips",
        # Utilities
        "NEE": "NextEra Energy",
        "DUK": "Duke Energy",
        "SO": "Southern Company",
        "EXC": "Exelon",
        # Materials
        "LIN": "Linde",
        "DOW": "Dow",
        # Real Estate
        "AMT": "American Tower",
        # Travel
        "BKNG": "Booking Holdings",
        # Auto
        "GM": "General Motors",
        "F": "Ford",
        # Other
        "PM": "Philip Morris",
        "MO": "Altria",
        "WBA": "Walgreens",
    }

    # 3x 레버리지 ETF (5% 이상 변동 시 알림) - 인버스 제외
    LEVERAGED_ETFS = {
        "TQQQ": "ProShares UltraPro QQQ (나스닥 3배)",
        "UPRO": "ProShares UltraPro S&P500 (S&P 3배)",
        "SOXL": "Direxion Semiconductor Bull 3X (반도체 3배)",
        "LABU": "Direxion Biotech Bull 3X (바이오 3배)",
        "TNA": "Direxion Small Cap Bull 3X (소형주 3배)",
        "FAS": "Direxion Financial Bull 3X (금융 3배)",
        "TECL": "Direxion Technology Bull 3X (기술 3배)",
        "FNGU": "MicroSectors FANG+ 3X (빅테크 3배)",
    }

    # 변동률 임계값
    INDEX_THRESHOLD = 2.0    # 지수 및 암호화폐: 2%
    STOCK_THRESHOLD = 10.0   # 개별주 및 레버리지 ETF: 10%

    def __init__(self):
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def get_kospi_realtime(self) -> Optional[Tuple[float, float]]:
        """네이버 금융 API로 코스피 실시간 데이터 가져오기"""
        try:
            url = 'https://m.stock.naver.com/api/index/KOSPI/basic'
            response = requests.get(url, headers=self._headers, timeout=10)

            if response.status_code != 200:
                logger.warning(f"코스피: 네이버 API 오류 ({response.status_code})")
                return None

            data = response.json()
            current_price = float(data.get('closePrice', '0').replace(',', ''))
            change = float(data.get('compareToPreviousClosePrice', '0').replace(',', ''))
            previous_close = current_price - change

            if current_price and previous_close:
                logger.debug(f"코스피(네이버): 현재가 {current_price}, 전일종가 {previous_close}")
                return (current_price, previous_close)

            return None
        except Exception as e:
            logger.error(f"코스피 네이버 API 오류: {e}")
            return None

    def get_bitcoin_realtime(self) -> Optional[Tuple[float, float]]:
        """Binance API로 비트코인 실시간 데이터 가져오기"""
        try:
            url = 'https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT'
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                logger.warning(f"비트코인: Binance API 오류 ({response.status_code})")
                return None

            data = response.json()
            current_price = float(data.get('lastPrice', 0))
            previous_close = float(data.get('prevClosePrice', 0))

            if current_price and previous_close:
                logger.debug(f"비트코인(Binance): 현재가 {current_price}, 전일종가 {previous_close}")
                return (current_price, previous_close)

            return None
        except Exception as e:
            logger.error(f"비트코인 Binance API 오류: {e}")
            return None

    def get_price_data(self, symbol: str) -> Optional[Tuple[float, float]]:
        """
        주가 데이터 가져오기
        - 코스피: 네이버 금융 API (실시간)
        - 비트코인: Binance API (실시간)
        - 기타: Yahoo Finance API

        Returns:
            (현재가, 전일종가) 또는 None
        """
        # 코스피는 네이버 실시간 데이터 사용
        if symbol == "^KS11":
            return self.get_kospi_realtime()

        # 비트코인은 Binance 실시간 데이터 사용
        if symbol == "BTC-USD":
            return self.get_bitcoin_realtime()

        try:
            # Yahoo Finance Chart API v8
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                "interval": "1d",
                "range": "5d"  # 5일 데이터로 확장 (휴일 대비)
            }

            response = requests.get(url, params=params, headers=self._headers, timeout=10)

            if response.status_code != 200:
                logger.warning(f"{symbol}: API 응답 오류 ({response.status_code})")
                return None

            data = response.json()
            result = data.get("chart", {}).get("result", [])

            if not result:
                logger.warning(f"{symbol}: 데이터 없음")
                return None

            meta = result[0].get("meta", {})
            quotes = result[0].get("indicators", {}).get("quote", [{}])[0]
            closes = quotes.get("close", [])

            # 유효한 종가만 필터링
            valid_closes = [c for c in closes if c is not None]

            # 현재가는 regularMarketPrice 사용 (실시간)
            current_price = meta.get("regularMarketPrice")

            # 전일종가는 종가 배열에서 마지막 두 번째 값 사용
            if len(valid_closes) >= 2:
                previous_close = valid_closes[-2]
            else:
                previous_close = meta.get("chartPreviousClose") or meta.get("previousClose")

            if current_price and previous_close:
                logger.debug(f"{symbol}: 성공 - 현재가: {current_price}, 전일종가: {previous_close}")
                return (float(current_price), float(previous_close))

            logger.warning(f"{symbol}: 가격 데이터 불완전 (current={current_price}, prev={previous_close})")
            return None

        except requests.RequestException as e:
            logger.error(f"{symbol} 요청 오류: {e}")
            return None
        except Exception as e:
            logger.error(f"{symbol} 데이터 조회 오류: {e}")
            return None

    def calculate_change_percent(self, current: float, previous: float) -> float:
        """변동률 계산"""
        if previous == 0:
            return 0.0
        return ((current - previous) / previous) * 100

    def check_symbols(self, symbols_dict: Dict[str, str], category: str, threshold: float) -> List[PriceChange]:
        """
        종목 체크 (임계값 초과 시 알림 대상 반환)
        중복 알림 방지는 scheduler.py에서 처리
        """
        alerts = []

        for symbol, name in symbols_dict.items():
            price_data = self.get_price_data(symbol)
            if price_data:
                current, previous = price_data
                change = self.calculate_change_percent(current, previous)

                if abs(change) >= threshold:
                    alerts.append(PriceChange(
                        symbol=symbol,
                        name=name,
                        current_price=current,
                        previous_close=previous,
                        change_percent=change,
                        category=category
                    ))

        return alerts

    def is_us_market_hours(self) -> bool:
        """
        미국장 정규 거래 시간인지 확인 (한국시간 기준)
        - 정규장: 23:30 ~ 06:00 (썸머타임 시 22:30 ~ 05:00)
        - 주가 변동 알림은 정규장 시간에만 발송
        """
        now = datetime.now()
        hour = now.hour
        minute = now.minute

        # 한국시간 23:30 ~ 06:00 (정규장)
        if hour >= 23 and minute >= 30:
            return True
        if hour < 6:
            return True

        return False

    def is_kr_market_hours(self) -> bool:
        """한국장 거래 시간인지 확인 (09:00 ~ 15:30)"""
        now = datetime.now()
        hour = now.hour
        minute = now.minute

        if hour < 9 or (hour == 15 and minute > 30) or hour > 15:
            return False
        return True

    def is_weekend(self) -> bool:
        """주말인지 확인"""
        return datetime.now().weekday() >= 5  # 토(5), 일(6)

    def check_weekend(self) -> List[PriceChange]:
        """
        주말 전용 체크 (나스닥 선물 + 비트코인만)
        - 나스닥 선물: 주말에도 일부 시간 거래
        - 비트코인: 24/7 거래
        """
        all_alerts = []
        logger.info("주말 모드: 나스닥 선물 + 비트코인만 체크")

        # 나스닥 선물
        nq_futures = {"NQ=F": self.INDICES["NQ=F"]}
        all_alerts.extend(self.check_symbols(nq_futures, 'index', self.INDEX_THRESHOLD))

        # 비트코인
        all_alerts.extend(self.check_symbols(self.CRYPTO, 'crypto', self.INDEX_THRESHOLD))

        all_alerts.sort(key=lambda x: abs(x.change_percent), reverse=True)
        logger.info(f"주말 체크: {len(all_alerts)}개 알림 항목 발견")
        return all_alerts

    def check_all(self) -> List[PriceChange]:
        """모든 항목 체크 (장 운영 시간에 따라 필터링)"""
        all_alerts = []

        kr_market_open = self.is_kr_market_hours()
        us_market_open = self.is_us_market_hours()

        logger.info(f"시장 상태 - 한국장: {'열림' if kr_market_open else '닫힘'}, 미국장: {'열림' if us_market_open else '닫힘'}")

        # 코스피는 한국장 시간에만 체크
        if kr_market_open:
            kospi_alerts = self.check_symbols({"^KS11": self.INDICES["^KS11"]}, 'index', self.INDEX_THRESHOLD)
            all_alerts.extend(kospi_alerts)

        # 미국 지수는 미국장 시간에만 체크
        if us_market_open:
            us_indices = {k: v for k, v in self.INDICES.items() if k != "^KS11"}
            all_alerts.extend(self.check_symbols(us_indices, 'index', self.INDEX_THRESHOLD))

            # 개별주 (10% 기준) - 미국장 시간에만
            logger.info("개별주 변동 체크 중...")
            all_alerts.extend(self.check_symbols(self.US_TOP_STOCKS, 'stock', self.STOCK_THRESHOLD))

            # 레버리지 ETF (10% 기준) - 미국장 시간에만
            logger.info("레버리지 ETF 변동 체크 중...")
            all_alerts.extend(self.check_symbols(self.LEVERAGED_ETFS, 'etf', self.STOCK_THRESHOLD))

        # 암호화폐는 24시간 체크
        logger.info("암호화폐 변동 체크 중...")
        all_alerts.extend(self.check_symbols(self.CRYPTO, 'crypto', self.INDEX_THRESHOLD))

        # 변동률 절대값 기준으로 정렬
        all_alerts.sort(key=lambda x: abs(x.change_percent), reverse=True)

        logger.info(f"총 {len(all_alerts)}개 알림 항목 발견")
        return all_alerts

    def get_market_summary(self) -> List[PriceChange]:
        """전체 시장 요약 (임계값 무관하게 모든 지수/암호화폐 조회)"""
        summary = []

        # 지수
        for symbol, name in self.INDICES.items():
            price_data = self.get_price_data(symbol)
            if price_data:
                current, previous = price_data
                change = self.calculate_change_percent(current, previous)
                summary.append(PriceChange(
                    symbol=symbol,
                    name=name,
                    current_price=current,
                    previous_close=previous,
                    change_percent=change,
                    category='index'
                ))

        # 암호화폐
        for symbol, name in self.CRYPTO.items():
            price_data = self.get_price_data(symbol)
            if price_data:
                current, previous = price_data
                change = self.calculate_change_percent(current, previous)
                summary.append(PriceChange(
                    symbol=symbol,
                    name=name,
                    current_price=current,
                    previous_close=previous,
                    change_percent=change,
                    category='crypto'
                ))

        return summary

    def format_alert_message(self, alerts: List[PriceChange]) -> str:
        """알림 메시지 포맷"""
        if not alerts:
            return ""

        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        message = f"🚨 <b>주가 변동 알림</b> 🚨\n"
        message += f"📅 {now}\n\n"

        # 카테고리별 분류
        indices = [a for a in alerts if a.category in ('index', 'crypto')]
        stocks = [a for a in alerts if a.category == 'stock']
        etfs = [a for a in alerts if a.category == 'etf']

        if indices:
            message += "📊 <b>지수/암호화폐 (2% 이상 변동)</b>\n"
            for alert in indices:
                emoji = "📈" if alert.change_percent > 0 else "📉"
                sign = "+" if alert.change_percent > 0 else ""
                message += f"{emoji} {alert.name}\n"
                message += f"   ${alert.current_price:,.2f} ({sign}{alert.change_percent:.2f}%)\n"
            message += "\n"

        if stocks:
            message += "💼 <b>개별주 (10% 이상 변동)</b>\n"
            for alert in stocks:
                emoji = "📈" if alert.change_percent > 0 else "📉"
                sign = "+" if alert.change_percent > 0 else ""
                message += f"{emoji} {alert.name} ({alert.symbol})\n"
                message += f"   ${alert.current_price:,.2f} ({sign}{alert.change_percent:.2f}%)\n"
            message += "\n"

        if etfs:
            message += "⚡ <b>3x 레버리지 ETF (10% 이상 변동)</b>\n"
            for alert in etfs:
                emoji = "📈" if alert.change_percent > 0 else "📉"
                sign = "+" if alert.change_percent > 0 else ""
                message += f"{emoji} {alert.symbol}: {alert.name}\n"
                message += f"   ${alert.current_price:,.2f} ({sign}{alert.change_percent:.2f}%)\n"
            message += "\n"

        message += "💡 투자에 유의하시기 바랍니다."

        return message

    def format_market_summary_message(self, summary: List[PriceChange], market_type: str = "all") -> str:
        """
        시장 요약 메시지 포맷 (TQQQ, SOXL 포함)

        Args:
            summary: 시장 데이터 리스트
            market_type: 'us' (미국장 마감), 'kr' (한국장 마감), 'all' (전체)
        """
        if not summary:
            return ""

        # 미국장 마감: 코스피는 거래 전 (⏸️)
        # 한국장 마감: 나스닥, S&P는 거래 전 (⏸️)
        us_symbols = ["^IXIC", "^GSPC", "NQ=F"]  # 미국 지수
        kr_symbols = ["^KS11"]  # 한국 지수

        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        message = f"📊 <b>시장 현황</b>\n"
        message += f"📅 {now}\n\n"

        indices = [s for s in summary if s.category == 'index']
        crypto = [s for s in summary if s.category == 'crypto']

        if indices:
            message += "<b>📈 주요 지수</b>\n"
            for item in indices:
                # 거래 없는 시장 표시
                if market_type == "us" and item.symbol in kr_symbols:
                    # 미국장 마감 시 한국은 아직 거래 전
                    message += f"⏸️ {item.name}: ${item.current_price:,.2f} (거래 전)\n"
                elif market_type == "kr" and item.symbol in us_symbols:
                    # 한국장 마감 시 미국은 아직 거래 전
                    message += f"⏸️ {item.name}: ${item.current_price:,.2f} (거래 전)\n"
                else:
                    emoji = "🔺" if item.change_percent > 0 else "🔻"
                    sign = "+" if item.change_percent > 0 else ""
                    message += f"{emoji} {item.name}: ${item.current_price:,.2f} ({sign}{item.change_percent:.2f}%)\n"
            message += "\n"

        if crypto:
            message += "<b>🪙 암호화폐</b>\n"
            for item in crypto:
                emoji = "🔺" if item.change_percent > 0 else "🔻"
                sign = "+" if item.change_percent > 0 else ""
                message += f"{emoji} {item.name}: ${item.current_price:,.2f} ({sign}{item.change_percent:.2f}%)\n"
            message += "\n"

        # TQQQ, SOXL 추가 (미국장 마감 시만 표시)
        if market_type != "kr":
            message += "<b>📊 3배 레버리지</b>\n"
            for symbol in ["TQQQ", "SOXL"]:
                price_data = self.get_price_data(symbol)
                if price_data:
                    current, previous = price_data
                    change = self.calculate_change_percent(current, previous)
                    emoji = "🔺" if change > 0 else "🔻"
                    sign = "+" if change > 0 else ""
                    name = "TQQQ (나스닥 3배)" if symbol == "TQQQ" else "SOXL (반도체 3배)"
                    message += f"{emoji} {name}: ${current:,.2f} ({sign}{change:.2f}%)\n"
            message += "\n"

        # 원달러 환율
        message += "<b>💱 환율</b>\n"
        for symbol, name in self.CURRENCIES.items():
            price_data = self.get_price_data(symbol)
            if price_data:
                current, previous = price_data
                change = self.calculate_change_percent(current, previous)
                # 환율 상승 = 원화 약세 (🔺빨강), 환율 하락 = 원화 강세 (🔻파랑)
                emoji = "🔺" if change > 0 else "🔻"
                sign = "+" if change > 0 else ""
                message += f"{emoji} {name}: ₩{current:,.2f} ({sign}{change:.2f}%)\n"

        return message
