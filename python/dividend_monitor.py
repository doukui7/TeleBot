import yfinance as yf
import logging
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
from news_fetcher import NewsFetcher

logger = logging.getLogger(__name__)


class DividendMonitor:
    """
    배당 데이터 수집 및 브리핑 생성 클래스
    """
    
    # YTD 캐시 (하루 1회만 업데이트)
    _ytd_cache = {}
    _ytd_cache_date = None
    
    def _get_ytd_data(self) -> Dict[str, float]:
        """ETF YTD 성과 캐싱"""
        from datetime import date
        today = date.today()
        
        # 캐시가 오늘 것이면 재사용
        if self._ytd_cache_date == today and self._ytd_cache:
            return self._ytd_cache
        
        # 새로 계산
        etf_symbols = ["SCHD", "VYM", "DGRO", "NOBL", "VIG", "HDV"]
        ytd_data = {}
        
        for symbol in etf_symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start="2026-01-02", period="1mo")
                if len(hist) >= 2:
                    year_start = hist.iloc[0]['Close']
                    current = hist.iloc[-1]['Close']
                    ytd_pct = ((current - year_start) / year_start) * 100
                    ytd_data[symbol] = ytd_pct
            except Exception as e:
                logger.warning(f"YTD fetch failed for {symbol}: {e}")
        
        # 캐시 저장
        self._ytd_cache = ytd_data
        self._ytd_cache_date = today
        
        return ytd_data
    
    def fetch_dividend_data(self) -> Dict:
        """배당 ETF 및 종목 데이터 수집"""
        try:
            # 기본 시장 데이터
            alert_monitor = DividendAlertMonitor()
            data = alert_monitor.get_market_data()
            
            # YTD 데이터 추가
            ytd_data = self._get_ytd_data()
            for symbol, ytd in ytd_data.items():
                if symbol in data:
                    data[symbol]['ytd_change'] = ytd
            
            return data
        except Exception as e:
            logger.error(f"배당 데이터 수집 오류: {e}")
            return {}
    
    def format_dividend_briefing(self, data: Dict) -> str:
        """배당 브리핑 메시지 포맷"""
        if not data:
            return "배당 데이터를 가져올 수 없습니다."
        
        from pytz import timezone
        
        # 한국 시간과 미국 시간
        kst = timezone('Asia/Seoul')
        et = timezone('America/New_York')
        now_kst = datetime.now(kst)
        now_et = datetime.now(et)
        
        # 미국 장 시간 확인 (09:30 - 16:00 ET, 평일)
        is_weekday = now_et.weekday() < 5
        is_trading_hours = (9 < now_et.hour < 16 or (now_et.hour == 9 and now_et.minute >= 30))
        is_market_open = is_weekday and is_trading_hours
        
        # 요일 이름
        weekday_kr = ['월', '화', '수', '목', '금', '토', '일'][now_kst.weekday()]
        weekday_et = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][now_et.weekday()]
        
        if is_market_open:
            market_status = f"🟢 미국 장중 ({now_et.strftime('%m/%d %H:%M ET')})"
        else:
            market_status = f"⚪ 장전/장후 (전일 종가)"
        
        msg = f"💰 <b>배당 포트폴리오 브리핑</b>\n"
        msg += f"📅 {now_kst.strftime('%m/%d')}({weekday_kr}) {now_kst.strftime('%H:%M')} KST\n"
        msg += f"📊 {market_status}\n\n"
        
        # 1. 시장 지수
        msg += "📊 <b>시장 지수</b>\n"
        indices = [k for k in data.keys() if data[k]['type'] == 'INDEX']
        for sym in indices:
            d = data[sym]
            icon = "🔺" if d['change'] > 0 else "🔻" if d['change'] < 0 else "➖"
            msg += f"{icon} {d['name']}: {d['change']:+.2f}%\n"
        msg += "\n"
        
        # 2. 배당 ETF
        msg += "🛡️ <b>배당 ETF</b>\n"
        etfs = sorted([k for k in data.keys() if data[k]['type'] == 'ETF'], 
                     key=lambda x: data[x]['change'], reverse=True)
        for sym in etfs:
            d = data[sym]
            color = "🟢" if d['change'] >= 0 else "🔴"
            highlight = " 🔥" if abs(d['change']) >= 3.0 else ""
            
            # 기본 정보
            line = f"{color} {sym}: ${d['price']:.2f} ({d['change']:+.2f}%)"
            
            # YTD 추가
            if d.get('ytd_change') is not None:
                ytd_icon = "📈" if d['ytd_change'] > 0 else "📉"
                line += f" {ytd_icon}YTD {d['ytd_change']:+.1f}%"
            
            line += highlight
            msg += line + "\n"
        msg += "\n"
        
        # 3. 배당 개별주
        msg += "👑 <b>배당 개별주</b>\n"
        stocks = sorted([k for k in data.keys() if data[k]['type'] == 'STOCK'], 
                       key=lambda x: data[x]['change'], reverse=True)
        for sym in stocks:
            d = data[sym]
            color = "🟢" if d['change'] >= 0 else "🔴"
            highlight = " 🔥" if abs(d['change']) >= 5.0 else ""
            msg += f"{color} {sym} ({d['name'][:15]}): ${d['price']:.2f} ({d['change']:+.2f}%){highlight}\n"
        
        msg += "\n📌 기준: ETF 3%, 개별주 5% 이상 변동 시 🔥 표시"
        
        return msg


class DividendAlertMonitor:
    """
    배당 포트폴리오 모니터링 및 알림 클래스 ('Golden Toilet' 포트폴리오 기반)
    기능:
    1. 주가 변동 모니터링 (개별주 5%, ETF 3%, 지수 2%)
    2. 뉴스 모니터링 (실적/배당 키워드)
    3. 장마감 브리핑
    """

    # 1. ETFs (Golden Toilet List)
    DIVIDEND_ETFS = {
        "SCHD": "Schwab US Dividend Equity",
        "VYM": "Vanguard High Dividend Yield",
        "DGRO": "iShares Core Dividend Growth",
        "NOBL": "ProShares S&P 500 Dividend Aristocrats",
        "VIG": "Vanguard Dividend Appreciation",
        "HDV": "iShares Core High Dividend"
    }

    # 2. Individual Stocks (Dividend Kings/Aristocrats Top Picks + O)
    DIVIDEND_STOCKS = {
        "KO": "Coca-Cola",
        "JNJ": "Johnson & Johnson",
        "PG": "Procter & Gamble",
        "MMM": "3M Company",
        "ABBV": "AbbVie Inc",
        "PEP": "PepsiCo",
        "O": "Realty Income",
        "LOW": "Lowe's Companies",
        "TGT": "Target Corp",
        "ABT": "Abbott Laboratories"
    }

    # 3. Market Indices (Context)
    INDICES = {
        "^GSPC": "S&P 500",
        "^IXIC": "NASDAQ Composite"
    }

    # Alert Thresholds (Daily Change %)
    THRESHOLDS = {
        "STOCK": 5.0,  # User Request: 5% for individual stocks
        "ETF": 3.0,    # 3% for ETFs
        "INDEX": 2.0   # 2% for Indices
    }

    def __init__(self, news_fetcher: Optional[NewsFetcher] = None):
        self.news_fetcher = news_fetcher or NewsFetcher()
        # Cache for last check prices to avoid spamming same alert
        self.last_alert_prices = {} 

    def get_symbol_type(self, symbol: str) -> str:
        if symbol in self.DIVIDEND_STOCKS:
            return "STOCK"
        elif symbol in self.DIVIDEND_ETFS:
            return "ETF"
        else:
            return "INDEX"

    def get_market_data(self) -> Dict:
        """Fetch current market data for all symbols"""
        all_symbols = list(self.DIVIDEND_ETFS.keys()) + \
                     list(self.DIVIDEND_STOCKS.keys()) + \
                     list(self.INDICES.keys())
        
        data = {}
        try:
            # Batch fetch is more efficient
            tickers = yf.Tickers(" ".join(all_symbols))
            
            for symbol in all_symbols:
                try:
                    ticker = tickers.tickers[symbol]
                    # Fast info is faster than history
                    info = ticker.fast_info
                    prev_close = info.previous_close
                    current_price = info.last_price
                    
                    if current_price and prev_close:
                        change_pct = ((current_price - prev_close) / prev_close) * 100
                        
                        name = self.DIVIDEND_STOCKS.get(symbol) or \
                               self.DIVIDEND_ETFS.get(symbol) or \
                               self.INDICES.get(symbol)
                        
                        # YTD 성과 및 배당 정보 (ETF만 - 선택적)
                        ytd_change = None
                        dividend_yield = None
                        
                        data[symbol] = {
                            "name": name,
                            "price": current_price,
                            "change": change_pct,
                            "type": self.get_symbol_type(symbol),
                            "ytd_change": ytd_change,
                            "dividend_yield": dividend_yield
                        }
                except Exception as e:
                    logger.warning(f"Failed to fetch data for {symbol}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Market data fetch error: {e}")
            
        return data

    def check_price_alerts(self) -> List[str]:
        """
        Check for price movements exceeding thresholds.
        Returns list of formatted alert messages.
        """
        alerts = []
        market_data = self.get_market_data()
        
        for symbol, info in market_data.items():
            sym_type = info['type']
            threshold = self.THRESHOLDS.get(sym_type, 5.0)
            change_pct = info['change']
            
            # Check if threshold exceeded
            if abs(change_pct) >= threshold:
                # Check if we already alerted for this price range today?
                # For simplicity, we just alert if it crosses. 
                # (In production, might want to debounce)
                
                direction = "🚀 급등" if change_pct > 0 else "📉 급락"
                emoji = "🔴" if change_pct < 0 else "🟢"
                
                msg = (
                    f"{emoji} <b>{info['name']} ({symbol}) {direction}</b>\n\n"
                    f"현재가: ${info['price']:.2f}\n"
                    f"등락률: {change_pct:+.2f}%\n"
                    f"알림 기준: {threshold}% 이상 변동"
                )
                alerts.append(msg)
                
        return alerts

    def check_news_alerts(self) -> List[str]:
        """
        Check specific company news for Earnings or Dividend keywords.
        Returns list of formatted news messages.
        """
        if not self.news_fetcher:
            return []
            
        alerts = []
        # Keywords to search for
        keywords = ["Earnings", "Dividend", "실적", "배당", "Quarterly Results"]
        
        # Only check individual stocks to avoid too many requests
        for symbol, name in self.DIVIDEND_STOCKS.items():
            query = f'"{name}" AND ("Earnings" OR "Dividend" OR "실적" OR "배당")'
            
            try:
                # Fetch recent news (limit 2 per company)
                articles = self.news_fetcher.fetch_custom_news(query, limit=1)
                
                for article in articles:
                    # Simple duplication check logic would go here in a full DB system
                    # For now, we rely on the news_fetcher's deduplication if improved
                    # or just send what we find. 
                    # Real-world usage: Needs a 'seen_urls' cache.
                    
                    title = article.get('title', '')
                    link = article.get('link', '')
                    
                    # Basic check if relevant (double check)
                    if any(k.lower() in title.lower() for k in keywords):
                         msg = (
                            f"📰 <b>{name} ({symbol}) 주요 뉴스</b>\n\n"
                            f"{title}\n"
                            f"🔗 <a href='{link}'>기사 보기</a>"
                        )
                         alerts.append(msg)
                         
            except Exception as e:
                logger.error(f"News check failed for {symbol}: {e}")
                continue
                
        return alerts

    def format_closing_briefing(self) -> str:
        """Format daily closing briefing message"""
        data = self.get_market_data()
        if not data:
            return "데이터를 가져올 수 없습니다."
        
        from pytz import timezone
        kst = timezone('Asia/Seoul')
        now_kst = datetime.now(kst)
        
        msg = f"🔔 <b>배당 포트폴리오 마감 브리핑</b>\n"
        msg += f"📅 {now_kst.strftime('%Y-%m-%d %H:%M KST')}\n"
        msg += f"📊 데이터: 미국 장 마감 기준\n\n"
        
        # 1. Indices
        msg += "📊 <b>시장 지수</b>\n"
        for sym, name in self.INDICES.items():
            if sym in data:
                d = data[sym]
                icon = "🔺" if d['change'] > 0 else "Vk" if d['change'] < 0 else "-"
                msg += f"{icon} {name}: {d['change']:+.2f}%\n"
        msg += "\n"
        
        # 2. ETFs
        msg += "🛡️ <b>배당 ETF</b>\n"
        sorted_etfs = sorted([k for k in data.keys() if data[k]['type'] == 'ETF'], 
                           key=lambda x: data[x]['change'], reverse=True)
                           
        for sym in sorted_etfs:
            d = data[sym]
            color = "🔴" if d['change'] < 0 else "🟢"
            msg += f"{color} {sym}: ${d['price']:.2f} ({d['change']:+.2f}%)\n"
        msg += "\n"
        
        # 3. Dividend Stocks
        msg += "👑 <b>배당 개별주</b>\n"
        sorted_stocks = sorted([k for k in data.keys() if data[k]['type'] == 'STOCK'], 
                             key=lambda x: data[x]['change'], reverse=True)
                             
        for sym in sorted_stocks:
            d = data[sym]
            color = "🔴" if d['change'] < 0 else "🟢"
            # Highlight big movers
            highlight = " 🔥" if abs(d['change']) >= 5.0 else ""
            msg += f"{color} {sym}: ${d['price']:.2f} ({d['change']:+.2f}%){highlight}\n"
            
        return msg
