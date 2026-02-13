"""
S&P 100 실적 발표 모니터링

기능:
- 이번 주 S&P 100 실적 발표 일정 조회
- EPS 예상치 및 실제 결과 비교
- 매출 예상치 제공 (가능한 경우)
"""
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

# S&P 100 주요 기업 (stock_monitor.py US_TOP_STOCKS와 동일)
SP100_STOCKS = {
    # Technology
    "AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Alphabet",
    "NVDA": "NVIDIA", "META": "Meta", "AVGO": "Broadcom",
    "CSCO": "Cisco", "ADBE": "Adobe", "CRM": "Salesforce",
    "ORCL": "Oracle", "ACN": "Accenture", "IBM": "IBM",
    "INTC": "Intel", "AMD": "AMD", "QCOM": "Qualcomm",
    "TXN": "Texas Instruments",
    # Consumer
    "AMZN": "Amazon", "TSLA": "Tesla", "HD": "Home Depot",
    "MCD": "McDonald's", "NKE": "Nike", "SBUX": "Starbucks",
    "LOW": "Lowe's", "TGT": "Target", "COST": "Costco",
    "WMT": "Walmart", "PG": "P&G", "KO": "Coca-Cola",
    "PEP": "PepsiCo", "MDLZ": "Mondelez", "CL": "Colgate",
    "KHC": "Kraft Heinz",
    # Communication
    "NFLX": "Netflix", "DIS": "Disney", "CMCSA": "Comcast",
    "T": "AT&T", "VZ": "Verizon", "TMUS": "T-Mobile",
    # Healthcare
    "UNH": "UnitedHealth", "JNJ": "J&J", "LLY": "Eli Lilly",
    "MRK": "Merck", "ABBV": "AbbVie", "PFE": "Pfizer",
    "TMO": "Thermo Fisher", "ABT": "Abbott", "DHR": "Danaher",
    "BMY": "Bristol-Myers", "AMGN": "Amgen", "GILD": "Gilead",
    "MDT": "Medtronic", "CVS": "CVS Health",
    # Financial
    "BRK-B": "Berkshire", "JPM": "JPMorgan", "V": "Visa",
    "MA": "Mastercard", "BAC": "BofA", "WFC": "Wells Fargo",
    "GS": "Goldman Sachs", "MS": "Morgan Stanley", "C": "Citigroup",
    "SCHW": "Schwab", "BLK": "BlackRock", "AXP": "AmEx",
    "COF": "Capital One", "MET": "MetLife", "AIG": "AIG",
    # Industrial
    "BA": "Boeing", "HON": "Honeywell", "UNP": "Union Pacific",
    "RTX": "Raytheon", "CAT": "Caterpillar", "GE": "GE Aerospace",
    "LMT": "Lockheed Martin", "UPS": "UPS", "FDX": "FedEx",
    "MMM": "3M",
    # Energy
    "XOM": "Exxon Mobil", "CVX": "Chevron", "COP": "ConocoPhillips",
    # Utilities
    "NEE": "NextEra Energy", "DUK": "Duke Energy",
    "SO": "Southern Co", "EXC": "Exelon",
    # Others
    "LIN": "Linde", "DOW": "Dow", "AMT": "American Tower",
    "BKNG": "Booking", "GM": "GM",
}

WEEKDAY_KR = {0: '월요일', 1: '화요일', 2: '수요일', 3: '목요일', 4: '금요일'}


@dataclass
class EarningsInfo:
    symbol: str
    name: str
    earnings_date: str  # YYYY-MM-DD
    earnings_time: str  # "BMO", "AMC", ""
    eps_estimate: Optional[float] = None
    eps_actual: Optional[float] = None
    surprise_pct: Optional[float] = None
    revenue_estimate: Optional[float] = None  # dollars
    revenue_actual: Optional[float] = None


class EarningsMonitor:
    """S&P 100 실적 발표 모니터링"""

    def __init__(self):
        self._cache: List[EarningsInfo] = []
        self._cache_date: Optional[str] = None

    def _get_week_range(self):
        """이번 주 월~금 날짜 범위 반환 (미국 기준)"""
        today = datetime.now().date()
        # 토요일(5)이면 다음주, 일요일(6)이면 다음주
        if today.weekday() >= 5:
            days_ahead = 7 - today.weekday()
            monday = today + timedelta(days=days_ahead)
        else:
            monday = today - timedelta(days=today.weekday())
        friday = monday + timedelta(days=4)
        return monday, friday

    def fetch_weekly_earnings(self) -> List[EarningsInfo]:
        """이번 주 S&P 100 실적 발표 일정 조회"""
        today_str = datetime.now().strftime('%Y-%m-%d')

        # 캐시 확인
        if self._cache_date == today_str and self._cache:
            logger.info("실적 캐시 사용")
            return self._cache

        logger.info(f"S&P 100 실적 일정 조회 시작 ({len(SP100_STOCKS)}개 종목)")
        results = []
        monday, friday = self._get_week_range()

        for symbol, name in SP100_STOCKS.items():
            try:
                ticker = yf.Ticker(symbol)

                # 실적 날짜 + EPS 예상/실제
                earnings_df = ticker.get_earnings_dates(limit=4)
                if earnings_df is None or earnings_df.empty:
                    time.sleep(0.15)
                    continue

                for idx, row in earnings_df.iterrows():
                    try:
                        e_date = idx.date() if hasattr(idx, 'date') else idx
                    except Exception:
                        continue

                    if monday <= e_date <= friday:
                        eps_est = row.get('EPS Estimate')
                        eps_act = row.get('Reported EPS')
                        surprise = row.get('Surprise(%)')

                        eps_est = float(eps_est) if pd.notna(eps_est) else None
                        eps_act = float(eps_act) if pd.notna(eps_act) else None
                        surprise = float(surprise) if pd.notna(surprise) else None

                        # 매출 예상치 (calendar에서)
                        rev_est = None
                        try:
                            cal = ticker.calendar
                            if cal is not None:
                                if isinstance(cal, dict):
                                    rev_avg = cal.get('Revenue Average')
                                    if rev_avg and rev_avg > 0:
                                        rev_est = float(rev_avg)
                                elif isinstance(cal, pd.DataFrame) and 'Revenue Average' in cal.columns:
                                    vals = cal['Revenue Average'].dropna()
                                    if len(vals) > 0 and vals.iloc[0] > 0:
                                        rev_est = float(vals.iloc[0])
                        except Exception:
                            pass

                        # 실적 발표 시간
                        e_time = self._get_earnings_time(ticker)

                        results.append(EarningsInfo(
                            symbol=symbol,
                            name=name,
                            earnings_date=e_date.strftime('%Y-%m-%d'),
                            earnings_time=e_time,
                            eps_estimate=eps_est,
                            eps_actual=eps_act,
                            surprise_pct=surprise,
                            revenue_estimate=rev_est,
                        ))
                        break  # 심볼당 1개만

            except Exception as e:
                logger.error(f"{symbol} 실적 데이터 수집 실패: {e}")

            time.sleep(0.2)

        results.sort(key=lambda x: x.earnings_date)
        logger.info(f"이번 주 실적 발표 {len(results)}개 종목 발견")

        # 캐시 저장
        self._cache = results
        self._cache_date = today_str

        return results

    def fetch_earnings_results(self) -> List[EarningsInfo]:
        """최근 발표된 실적 결과 (eps_actual이 있는 항목)"""
        all_earnings = self.fetch_weekly_earnings()
        return [e for e in all_earnings if e.eps_actual is not None]

    def _get_earnings_time(self, ticker) -> str:
        """실적 발표 시간 (BMO/AMC) 판별"""
        try:
            cal = ticker.calendar
            if cal is None:
                return ""
            # calendar가 dict인 경우
            if isinstance(cal, dict):
                earnings_dates = cal.get('Earnings Date', [])
                if earnings_dates and len(earnings_dates) > 0:
                    ed = earnings_dates[0]
                    if hasattr(ed, 'hour'):
                        if ed.hour < 12:
                            return "BMO"
                        elif ed.hour >= 16:
                            return "AMC"
            # calendar가 DataFrame인 경우
            elif isinstance(cal, pd.DataFrame):
                if 'Earnings Date' in cal.columns:
                    vals = cal['Earnings Date'].dropna()
                    if len(vals) > 0:
                        ed = vals.iloc[0]
                        if hasattr(ed, 'hour'):
                            if ed.hour < 12:
                                return "BMO"
                            elif ed.hour >= 16:
                                return "AMC"
        except Exception:
            pass
        return ""

    def _format_revenue(self, revenue: float) -> str:
        """매출액을 읽기 좋은 형식으로 변환"""
        if revenue >= 1e9:
            return f"${revenue / 1e9:.1f}B"
        elif revenue >= 1e6:
            return f"${revenue / 1e6:.0f}M"
        else:
            return f"${revenue:,.0f}"

    def format_weekly_earnings(self, data: List[EarningsInfo]) -> str:
        """주간 실적 발표 일정 HTML 메시지 포맷"""
        if not data:
            return ""

        monday, friday = self._get_week_range()
        header = (
            f"📊 <b>S&P 100 실적 발표 일정</b>\n"
            f"{monday.strftime('%Y.%m.%d')} ~ {friday.strftime('%m.%d')}\n"
        )

        # 요일별 그룹핑
        by_day: Dict[str, List[EarningsInfo]] = {}
        for e in data:
            by_day.setdefault(e.earnings_date, []).append(e)

        body = ""
        has_content = False
        for day_offset in range(5):  # 월~금
            d = monday + timedelta(days=day_offset)
            d_str = d.strftime('%Y-%m-%d')
            weekday = WEEKDAY_KR.get(d.weekday(), '')
            d_display = d.strftime('%m/%d')

            entries = by_day.get(d_str, [])
            if entries:
                has_content = True
                body += f"\n📅 <b>{weekday} ({d_display})</b>\n"
                for e in entries:
                    time_tag = f" {e.earnings_time}" if e.earnings_time else ""
                    eps_tag = ""
                    if e.eps_actual is not None:
                        # 이미 발표됨
                        if e.eps_estimate is not None and e.surprise_pct is not None:
                            if e.surprise_pct > 0:
                                eps_tag = f"  ✅ ${e.eps_actual:.2f} (예상 ${e.eps_estimate:.2f}) Beat"
                            elif e.surprise_pct < 0:
                                eps_tag = f"  ❌ ${e.eps_actual:.2f} (예상 ${e.eps_estimate:.2f}) Miss"
                            else:
                                eps_tag = f"  🟰 ${e.eps_actual:.2f} (예상 ${e.eps_estimate:.2f})"
                        else:
                            eps_tag = f"  EPS: ${e.eps_actual:.2f}"
                    elif e.eps_estimate is not None:
                        eps_tag = f"  EPS 예상: ${e.eps_estimate:.2f}"

                    rev_tag = ""
                    if e.revenue_estimate:
                        rev_tag = f"  매출 예상: {self._format_revenue(e.revenue_estimate)}"

                    body += f"  <b>{e.symbol}</b> {e.name}{time_tag}\n"
                    if eps_tag:
                        body += f"  {eps_tag}\n"
                    if rev_tag:
                        body += f"  {rev_tag}\n"

        if not has_content:
            return ""

        footer = "\n💡 BMO=장전 | AMC=장후"

        return header + body + footer

    def format_earnings_results(self, data: List[EarningsInfo]) -> str:
        """실적 발표 결과 HTML 메시지 포맷"""
        if not data:
            return ""

        today = datetime.now().strftime('%m/%d')
        header = f"📈 <b>S&P 100 실적 발표 결과</b> ({today})\n"

        body = ""
        for e in data:
            if e.eps_actual is None:
                continue

            if e.surprise_pct is not None and e.eps_estimate is not None:
                if e.surprise_pct > 0:
                    icon = "✅"
                    result = f"Beat +{e.surprise_pct:.1f}%"
                elif e.surprise_pct < 0:
                    icon = "❌"
                    result = f"Miss {e.surprise_pct:.1f}%"
                else:
                    icon = "🟰"
                    result = "In-line"
                body += f"\n{icon} <b>{e.symbol}</b> {e.name}\n"
                body += f"   EPS: ${e.eps_actual:.2f} (예상 ${e.eps_estimate:.2f}) {result}\n"
            else:
                body += f"\n📋 <b>{e.symbol}</b> {e.name}\n"
                body += f"   EPS: ${e.eps_actual:.2f}\n"

            if e.revenue_actual:
                rev_str = self._format_revenue(e.revenue_actual)
                if e.revenue_estimate:
                    rev_est_str = self._format_revenue(e.revenue_estimate)
                    body += f"   매출: {rev_str} (예상 {rev_est_str})\n"
                else:
                    body += f"   매출: {rev_str}\n"

        return header + body
