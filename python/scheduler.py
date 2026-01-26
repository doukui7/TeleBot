"""
자동 뉴스 발행, ETF 추적 및 주가 변동 알림 스케줄러
"""
import logging
import asyncio
import json
import os
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import UPDATE_INTERVAL, NEWS_CATEGORY, TELEGRAM_BOT_TOKEN, CHANNEL_ID, NEWS_API_KEY, STOCK_CHECK_INTERVAL, ETF_REPORT_HOUR, ETF_REPORT_MINUTE, UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN
from news_fetcher import NewsFetcher
from telegram_bot import NewsChannelBot
from etf_tracker import ETFTracker
from stock_monitor import StockMonitor
from tqbus_tracker import TqBusTracker
from market_chart_generator import MarketChartGenerator
from fear_greed_tracker import FearGreedTracker, NaverFinanceTracker
from weekend_nasdaq_tracker import WeekendNasdaqTracker
from market_holidays import (
    is_us_market_holiday, is_kr_market_holiday, is_both_markets_closed,
    get_us_holidays_in_month, get_kr_holidays_in_month,
    get_upcoming_holidays, is_tomorrow_holiday, is_first_trading_day_of_week
)

logger = logging.getLogger(__name__)

# Upstash Redis 연결 (선택적)
redis_client = None
if UPSTASH_REDIS_URL and UPSTASH_REDIS_TOKEN:
    try:
        from upstash_redis import Redis
        redis_client = Redis(url=UPSTASH_REDIS_URL, token=UPSTASH_REDIS_TOKEN)
        logger.info("Upstash Redis 연결 성공")
    except Exception as e:
        logger.warning(f"Upstash Redis 연결 실패 (인메모리 사용): {e}")

# 알림 기록 파일 경로 (Redis 미사용 시 폴백)
ALERT_HISTORY_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'alert_history.json')

# 알림 쿨다운 시간 (초) - 24시간
ALERT_COOLDOWN_SECONDS = 24 * 60 * 60


class NewsScheduler:
    """뉴스 발행, ETF 추적 및 주가 변동 알림 스케줄러"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.news_fetcher = NewsFetcher(NEWS_API_KEY, NEWS_CATEGORY)
        self.bot = NewsChannelBot(TELEGRAM_BOT_TOKEN, CHANNEL_ID)
        self.etf_tracker = ETFTracker()
        self.stock_monitor = StockMonitor()
        self.tqbus_tracker = TqBusTracker()
        self.chart_generator = MarketChartGenerator()
        self.fear_greed_tracker = FearGreedTracker()
        self.naver_tracker = NaverFinanceTracker()
        self.weekend_nasdaq_tracker = WeekendNasdaqTracker()
        self.last_published_urls = set()
        self.sent_yonhap_urls = set()  # 연합뉴스 실시간 알림용
        self.stock_alerted_today: dict = self._load_alert_history()  # 파일에서 로드
        self.tqbus_alerted_today = False  # TQ버스 하루 1회 알림 (준비 알림)
        self.tqbus_crossover_count = 0  # TQ버스 돌파 알림 횟수 (하루 최대 3회)
        self.last_crossover_type = None  # 마지막 돌파 타입 (중복 방지)

    def _get_alert_key(self, symbol: str, level: int) -> str:
        """Redis 키 생성: alert:{symbol}:{level}"""
        return f"alert:{symbol}:{level}"

    def _check_alert_exists(self, symbol: str, level: int) -> bool:
        """해당 종목/레벨의 알림이 24시간 내에 발송되었는지 확인"""
        key = self._get_alert_key(symbol, level)

        # Redis 사용 시
        if redis_client:
            try:
                exists = redis_client.exists(key)
                if exists:
                    logger.info(f"Redis: {symbol} 레벨 {level} 알림 이미 존재 (24시간 내)")
                return bool(exists)
            except Exception as e:
                logger.error(f"Redis 조회 오류: {e}")

        # 인메모리 폴백
        record = self.stock_alerted_today.get(symbol, {})
        if isinstance(record, dict) and record.get("level", 0) >= level:
            return True
        return False

    def _save_alert_record(self, symbol: str, level: int):
        """알림 기록 저장 (24시간 TTL)"""
        key = self._get_alert_key(symbol, level)

        # Redis 사용 시 - 24시간 TTL로 저장
        if redis_client:
            try:
                redis_client.setex(key, ALERT_COOLDOWN_SECONDS, "1")
                logger.info(f"Redis: {symbol} 레벨 {level} 알림 기록 저장 (24시간 TTL)")
            except Exception as e:
                logger.error(f"Redis 저장 오류: {e}")

        # 인메모리에도 저장 (폴백용)
        today = datetime.now().strftime("%Y-%m-%d")
        self.stock_alerted_today[symbol] = {"date": today, "level": level}

    def _load_alert_history(self) -> dict:
        """알림 기록 로드 (인메모리 초기화용)"""
        # Redis 사용 시 인메모리는 비워둠 (Redis가 source of truth)
        if redis_client:
            logger.info("Redis 사용 중 - 인메모리 알림 기록 비움")
            return {}

        # 파일 폴백
        try:
            os.makedirs(os.path.dirname(ALERT_HISTORY_FILE), exist_ok=True)
            if os.path.exists(ALERT_HISTORY_FILE):
                with open(ALERT_HISTORY_FILE, 'r') as f:
                    data = json.load(f)
                    today = datetime.now().strftime("%Y-%m-%d")
                    return {
                        k: v for k, v in data.items()
                        if isinstance(v, dict) and v.get("date") == today
                    }
            return {}
        except Exception as e:
            logger.error(f"알림 기록 로드 실패: {e}")
            return {}

    def _save_alert_history(self):
        """알림 기록을 파일에 저장 (Redis 미사용 시 폴백)"""
        if redis_client:
            return  # Redis 사용 시 파일 저장 불필요

        try:
            os.makedirs(os.path.dirname(ALERT_HISTORY_FILE), exist_ok=True)
            with open(ALERT_HISTORY_FILE, 'w') as f:
                json.dump(self.stock_alerted_today, f)
        except Exception as e:
            logger.error(f"알림 기록 저장 실패: {e}")

    async def publish_daily_briefing(self, market_type: str = "all"):
        """
        일일 브리핑 발행 (주가 + 뉴스)

        Args:
            market_type: 'us' (미국장 마감 후), 'kr' (한국장 마감 후), 'all' (전체)
        """
        try:
            logger.info(f"일일 브리핑 발행 시작 (market_type: {market_type})...")

            # 주가 정보 가져오기
            summary = self.stock_monitor.get_market_summary()
            stock_message = self.stock_monitor.format_market_summary_message(summary, market_type)

            # 뉴스 가져오기 (카테고리별 limit 설정 사용)
            all_news = self.news_fetcher.fetch_all_news(translate=True)
            news_message = self.news_fetcher.format_briefing_message(all_news)

            # 헤더 설정
            if market_type == "us":
                header = "🌙 <b>미국장 마감 브리핑</b>\n\n"
            elif market_type == "kr":
                header = "🌅 <b>한국장 마감 브리핑</b>\n\n"
            else:
                header = ""

            # 1. 시장 차트 발송
            chart = self.chart_generator.create_market_chart()
            if chart:
                chart_caption = header + stock_message if header else stock_message
                await self.bot.send_photo_buffer(chart, chart_caption)
                logger.info("시장 차트 발송 성공")

            # 2. 뉴스 메시지 발송
            success = await self.bot.send_news(news_message)

            if success:
                logger.info(f"일일 브리핑 발행 성공")
            else:
                logger.error("일일 브리핑 발행 실패")

        except Exception as e:
            logger.error(f"브리핑 발행 오류: {e}")

    async def publish_morning_briefing(self):
        """오전 8시 브리핑 (미국장 마감 후)"""
        # 미국장 휴장일이면 스킵
        if is_us_market_holiday():
            logger.info("오전 브리핑 스킵 (미국장 휴장일)")
            return
        await self.publish_daily_briefing("us")

    async def publish_evening_briefing(self):
        """오후 5시 브리핑 (한국장 마감 후)"""
        # 한국장 휴장일이면 스킵
        if is_kr_market_holiday():
            logger.info("오후 브리핑 스킵 (한국장 휴장일)")
            return
        await self.publish_daily_briefing("kr")

    async def publish_premarket_briefing(self):
        """오전 7시 프리마켓 브리핑 (공탐지수 + 미국 증시) - 스크린샷 방식"""
        # 미국장 휴장일이면 스킵
        if is_us_market_holiday():
            logger.info("프리마켓 브리핑 스킵 (미국장 휴장일)")
            return

        try:
            logger.info("프리마켓 브리핑 발행 시작 (스크린샷 방식)...")

            # 1. CNN Fear & Greed Index 스크린샷 발송
            fg_screenshot = await self.fear_greed_tracker.capture_fear_greed_screenshot()
            if fg_screenshot:
                await self.bot.send_photo_buffer(fg_screenshot, "😱 <b>Fear & Greed Index</b>")
                logger.info("CNN Fear & Greed 스크린샷 발송 성공")
            else:
                logger.warning("CNN Fear & Greed 스크린샷 캡처 실패")

            # 2. 네이버 세계 증시 스크린샷 발송
            naver_screenshot = await self.naver_tracker.capture_naver_world_screenshot()
            if naver_screenshot:
                await self.bot.send_photo_buffer(naver_screenshot, "🌍 <b>세계 증시 현황</b>")
                logger.info("네이버 세계 증시 스크린샷 발송 성공")
            else:
                logger.warning("네이버 세계 증시 스크린샷 캡처 실패")

            logger.info("프리마켓 브리핑 발행 완료")

        except Exception as e:
            logger.error(f"프리마켓 브리핑 발행 오류: {e}")

    async def publish_etf_report(self):
        """ETF 일일 리포트 발행"""
        # 미국장 휴장일이면 스킵
        if is_us_market_holiday():
            logger.info("ETF 리포트 스킵 (미국장 휴장일)")
            return

        try:
            logger.info("ETF 리포트 발행 시작...")

            # 모든 ETF 데이터 수집
            etf_data = self.etf_tracker.get_all_etf_data()

            if not etf_data:
                logger.warning("ETF 데이터가 없습니다")
                return

            # 리포트 생성
            message = self.etf_tracker.format_etf_report(etf_data)

            # 채널에 발행
            success = await self.bot.send_news(message)

            if success:
                logger.info(f"ETF 리포트 발행 성공 ({len(etf_data)}개 ETF)")
            else:
                logger.error("ETF 리포트 발행 실패")

        except Exception as e:
            logger.error(f"ETF 리포트 발행 오류: {e}")

    def _get_threshold_level(self, change_percent: float, category: str) -> int:
        """
        변동률에 해당하는 임계값 레벨 반환
        - 지수/암호화폐: 1%, 2%, 3%, 4%, 5%... 단위
        - 개별주/ETF: 10%, 15%, 20%... 단위
        """
        abs_change = abs(change_percent)
        if category in ('index', 'crypto'):
            # 1% 단위로 레벨 계산 (1% → 1, 2.5% → 2, 3.1% → 3)
            return int(abs_change)
        else:
            # 5% 단위로 레벨 계산 (10% → 10, 15% → 15)
            return int(abs_change // 5) * 5

    async def check_stock_alerts(self):
        """
        주가 변동 알림 체크
        - 지수/암호화폐: 1%, 2%, 3%... 각 구간 돌파 시 알림
        - 개별주/레버리지 ETF: 10%, 15%, 20%... 각 구간 돌파 시 알림
        - 같은 종목/레벨은 24시간 내 재알림 안 함 (Redis TTL)
        - 주말: 나스닥 선물 + 비트코인만 체크
        """
        try:
            # 주말 여부 확인
            is_weekend = datetime.now().weekday() >= 5

            if is_weekend:
                # 주말: 나스닥 선물 + 비트코인만 체크
                logger.info("주가 변동 체크 시작 (주말 모드: NQ선물 + BTC)...")
                alerts = self.stock_monitor.check_weekend()
            else:
                # 평일: 전체 체크
                logger.info("주가 변동 체크 시작...")
                alerts = self.stock_monitor.check_all()

            if not alerts:
                logger.info("변동 임계값을 초과한 항목 없음")
                return

            # 24시간 내 중복 알림 필터링 (Redis 기반)
            new_alerts = []
            for alert in alerts:
                current_level = self._get_threshold_level(alert.change_percent, alert.category)

                # 24시간 내 같은 레벨 알림이 있는지 확인
                if self._check_alert_exists(alert.symbol, current_level):
                    logger.info(f"스킵: {alert.symbol} 레벨 {current_level} (24시간 내 알림 발송됨)")
                    continue

                new_alerts.append(alert)
                # 알림 기록 저장 (Redis: 24시간 TTL)
                self._save_alert_record(alert.symbol, current_level)
                logger.info(f"알림 대상: {alert.symbol} ({alert.change_percent:+.2f}%, 레벨 {current_level})")

            if not new_alerts:
                logger.info("새로운 알림 없음 (24시간 내 중복 필터링)")
                return

            # 파일 백업 저장 (Redis 미사용 시 폴백)
            self._save_alert_history()

            # 알림 메시지 생성 및 전송
            message = self.stock_monitor.format_alert_message(new_alerts)

            if message:
                success = await self.bot.send_news(message)

                if success:
                    logger.info(f"주가 변동 알림 발송 성공 ({len(new_alerts)}개 항목)")
                else:
                    logger.error("주가 변동 알림 발송 실패")

        except Exception as e:
            logger.error(f"주가 변동 체크 오류: {e}")

    async def check_tqbus_alert(self):
        """
        TQ버스 승하차 준비 알림 체크
        - 가격이 193일 이평선과 7% 이내로 가까워지면 알림
        - 하루에 한 번만 알림
        """
        # 미국장 휴장일이면 스킵
        if is_us_market_holiday():
            logger.info("TQ버스 알림 체크 스킵 (미국장 휴장일)")
            return

        try:
            logger.info("TQ버스 알림 체크 시작...")

            # 하루 1회 알림 리셋 (자정 이후)
            now = datetime.now()
            if now.hour == 0 and now.minute < 5:
                self.tqbus_alerted_today = False

            # 이미 오늘 알림을 보냈으면 스킵
            if self.tqbus_alerted_today:
                logger.info("TQ버스: 오늘 이미 알림 발송됨")
                return

            # 승하차 준비 알림 필요 여부 확인
            if self.tqbus_tracker.should_alert():
                alert_message = self.tqbus_tracker.format_alert_message()

                if alert_message:
                    success = await self.bot.send_news(alert_message)

                    if success:
                        self.tqbus_alerted_today = True
                        logger.info("TQ버스 승하차 준비 알림 발송 성공")
                    else:
                        logger.error("TQ버스 알림 발송 실패")
            else:
                logger.info("TQ버스: 알림 조건 미충족 (이평선 대비 10% 초과)")

        except Exception as e:
            logger.error(f"TQ버스 알림 체크 오류: {e}")

    async def check_tqbus_crossover(self):
        """
        TQ버스 SMA 돌파 알림 체크
        - 종가가 193일 이평선을 돌파하면 승차/하차 알림
        - 하루 최대 3회 발송
        """
        # 미국장 휴장일이면 스킵
        if is_us_market_holiday():
            logger.info("TQ버스 돌파 체크 스킵 (미국장 휴장일)")
            return

        try:
            logger.info("TQ버스 돌파 체크 시작...")

            # 하루 카운터 리셋 (자정 이후)
            now = datetime.now()
            if now.hour == 0 and now.minute < 5:
                self.tqbus_crossover_count = 0
                self.last_crossover_type = None

            # 하루 3회 초과하면 스킵
            if self.tqbus_crossover_count >= 3:
                logger.info("TQ버스: 오늘 돌파 알림 3회 발송 완료")
                return

            # 돌파 감지
            crossover = self.tqbus_tracker.detect_crossover()

            if crossover and crossover != self.last_crossover_type:
                message = self.tqbus_tracker.format_crossover_message(crossover)

                if message:
                    success = await self.bot.send_news(message)

                    if success:
                        self.tqbus_crossover_count += 1
                        self.last_crossover_type = crossover
                        logger.info(f"TQ버스 돌파 알림 발송 성공 ({crossover}, {self.tqbus_crossover_count}/3)")
                    else:
                        logger.error("TQ버스 돌파 알림 발송 실패")
            else:
                logger.info("TQ버스: 돌파 없음")

        except Exception as e:
            logger.error(f"TQ버스 돌파 체크 오류: {e}")

    async def publish_yonhap_news(self):
        """
        연합뉴스 정기 발송 (오전 9시, 오후 1시, 오후 8시)
        - 주말: 오전 9시 1회만 발송
        - 중복 기사 제외
        - 하루 발송 이력 추적
        """
        try:
            now = datetime.now()
            is_weekend = now.weekday() >= 5

            # 주말에는 오전 9시만 발송 (오후 1시, 8시 스킵)
            if is_weekend and now.hour != 9:
                logger.info(f"연합뉴스 스킵 (주말 - 오전 9시만 발송)")
                return

            logger.info("연합뉴스 발송 시작...")

            # 자정에 발송 이력 리셋
            if now.hour == 0 and now.minute < 10:
                self.sent_yonhap_urls.clear()
                logger.info("연합뉴스 발송 이력 리셋")

            # 연합뉴스 RSS 가져오기
            url = self.news_fetcher.NEWS_FEEDS['yonhap']['url_ko']
            articles = self.news_fetcher.fetch_google_news_rss(url, limit=20)

            # 중복 제외한 새 기사 필터링
            new_articles = []
            for article in articles:
                link = article.get('link', '')
                if link and link not in self.sent_yonhap_urls:
                    new_articles.append(article)
                    self.sent_yonhap_urls.add(link)

            if not new_articles:
                logger.info("연합뉴스: 새 기사 없음")
                return

            # 메시지 포맷
            time_label = "오전" if now.hour < 12 else "오후"
            msg = f"📰 <b>연합뉴스 {time_label} 브리핑</b>\n"
            msg += f"📅 {now.strftime('%Y-%m-%d %H:%M')}\n\n"

            for i, article in enumerate(new_articles[:10], 1):  # 최대 10개
                title = article.get('title', '')
                link = article.get('link', '')
                if link:
                    msg += f"{i}. <a href=\"{link}\">{title}</a>\n"
                else:
                    msg += f"{i}. {title}\n"

            success = await self.bot.send_news(msg)
            if success:
                logger.info(f"연합뉴스 {len(new_articles[:10])}개 기사 발송 완료")
            else:
                logger.error("연합뉴스 발송 실패")

        except Exception as e:
            logger.error(f"연합뉴스 발송 오류: {e}")

    async def publish_holiday_notice(self):
        """
        휴장일 사전 알림
        - 매월 1일: 이번 달 휴장일 안내
        - 매주 첫 거래일: 이번 주 휴장일 안내
        - 휴일 전날: 내일 휴장 알림
        """
        try:
            now = datetime.now()
            messages = []

            # 1. 매월 1일: 이번 달 휴장일 안내
            if now.day == 1:
                us_holidays = get_us_holidays_in_month(now.year, now.month)
                kr_holidays = get_kr_holidays_in_month(now.year, now.month)

                if us_holidays or kr_holidays:
                    msg = f"📅 <b>{now.month}월 증시 휴장일 안내</b>\n\n"

                    if us_holidays:
                        msg += "🇺🇸 <b>미국</b>\n"
                        for d in us_holidays:
                            msg += f"  • {d}\n"
                        msg += "\n"

                    if kr_holidays:
                        msg += "🇰🇷 <b>한국</b>\n"
                        for d in kr_holidays:
                            msg += f"  • {d}\n"

                    messages.append(msg)
                    logger.info(f"월간 휴장일 알림 생성 (미국 {len(us_holidays)}일, 한국 {len(kr_holidays)}일)")

            # 2. 매주 첫 거래일: 이번 주 휴장일 안내
            elif is_first_trading_day_of_week():
                upcoming = get_upcoming_holidays(days=7)

                if upcoming["us"] or upcoming["kr"]:
                    msg = "📅 <b>이번 주 휴장일 안내</b>\n\n"

                    if upcoming["us"]:
                        msg += "🇺🇸 <b>미국</b>\n"
                        for d in upcoming["us"]:
                            msg += f"  • {d}\n"
                        msg += "\n"

                    if upcoming["kr"]:
                        msg += "🇰🇷 <b>한국</b>\n"
                        for d in upcoming["kr"]:
                            msg += f"  • {d}\n"

                    messages.append(msg)
                    logger.info("주간 휴장일 알림 생성")

            # 3. 휴일 전날: 내일 휴장 알림
            tomorrow = is_tomorrow_holiday()
            if tomorrow["us"] or tomorrow["kr"]:
                msg = f"⚠️ <b>내일 ({tomorrow['date']}) 휴장 안내</b>\n\n"

                if tomorrow["us"]:
                    msg += "🇺🇸 미국 증시 휴장\n"
                if tomorrow["kr"]:
                    msg += "🇰🇷 한국 증시 휴장\n"

                messages.append(msg)
                logger.info("내일 휴장일 알림 생성")

            # 메시지 발송
            for msg in messages:
                await self.bot.send_news(msg)
                logger.info("휴장일 알림 발송 완료")

        except Exception as e:
            logger.error(f"휴장일 알림 오류: {e}")

    async def publish_tqbus_status(self):
        """TQ버스 상태 리포트 발행 (오전 8시 브리핑과 함께)"""
        # 미국장 휴장일이면 스킵
        if is_us_market_holiday():
            logger.info("TQ버스 상태 리포트 스킵 (미국장 휴장일)")
            return

        try:
            logger.info("TQ버스 상태 리포트 발행 시작...")

            message = self.tqbus_tracker.format_status_message()

            success = await self.bot.send_news(message)

            if success:
                logger.info("TQ버스 상태 리포트 발행 성공")
            else:
                logger.error("TQ버스 상태 리포트 발행 실패")

        except Exception as e:
            logger.error(f"TQ버스 상태 리포트 발행 오류: {e}")

    def start(self):
        """스케줄러 시작"""
        try:
            logger.info("스케줄러 시작...")

            # 오전 7시 프리마켓 브리핑 (공탐지수 + 미국 증시)
            self.scheduler.add_job(
                self.publish_premarket_briefing,
                'cron',
                hour=7,
                minute=0,
                id='premarket_briefing',
                name='프리마켓 브리핑 (공탐지수)',
                replace_existing=True
            )

            # 오전 8시 브리핑 (미국장 마감 후)
            self.scheduler.add_job(
                self.publish_morning_briefing,
                'cron',
                hour=8,
                minute=0,
                id='morning_briefing',
                name='오전 브리핑 (미국장 마감)',
                replace_existing=True
            )

            # 오후 5시 브리핑 (한국장 마감 후)
            self.scheduler.add_job(
                self.publish_evening_briefing,
                'cron',
                hour=17,
                minute=0,
                id='evening_briefing',
                name='오후 브리핑 (한국장 마감)',
                replace_existing=True
            )

            # 주가 변동 알림 체크 (주기적 - 5분마다)
            self.scheduler.add_job(
                self.check_stock_alerts,
                'interval',
                seconds=STOCK_CHECK_INTERVAL,
                id='check_stock_alerts',
                name='주가 변동 알림',
                replace_existing=True
            )

            # ETF 리포트 (매일 미국 장종료 후)
            self.scheduler.add_job(
                self.publish_etf_report,
                'cron',
                hour=ETF_REPORT_HOUR,
                minute=ETF_REPORT_MINUTE,
                id='publish_etf_report',
                name='ETF 일일 리포트',
                replace_existing=True
            )

            # TQ버스 상태 리포트 (오전 8시 - 미국장 마감 후)
            self.scheduler.add_job(
                self.publish_tqbus_status,
                'cron',
                hour=8,
                minute=5,
                id='tqbus_status',
                name='TQ버스 상태 리포트',
                replace_existing=True
            )

            # TQ버스 승하차 준비 알림 (1시간마다 체크, 7% 이내일 때만 하루 1회)
            self.scheduler.add_job(
                self.check_tqbus_alert,
                'interval',
                hours=1,
                id='tqbus_alert',
                name='TQ버스 승하차 준비 알림',
                replace_existing=True
            )

            # TQ버스 SMA 돌파 알림 (1시간마다 체크, 하루 최대 3회)
            self.scheduler.add_job(
                self.check_tqbus_crossover,
                'interval',
                hours=1,
                id='tqbus_crossover',
                name='TQ버스 돌파 알림',
                replace_existing=True
            )

            # 휴장일 사전 알림 (오전 7시 30분)
            self.scheduler.add_job(
                self.publish_holiday_notice,
                'cron',
                hour=7,
                minute=30,
                id='holiday_notice',
                name='휴장일 사전 알림',
                replace_existing=True
            )

            # 연합뉴스 정기 발송 (오전 9시, 오후 1시, 오후 8시)
            self.scheduler.add_job(
                self.publish_yonhap_news,
                'cron',
                hour=9,
                minute=0,
                id='yonhap_morning',
                name='연합뉴스 오전',
                replace_existing=True
            )
            self.scheduler.add_job(
                self.publish_yonhap_news,
                'cron',
                hour=13,
                minute=0,
                id='yonhap_afternoon',
                name='연합뉴스 오후',
                replace_existing=True
            )
            self.scheduler.add_job(
                self.publish_yonhap_news,
                'cron',
                hour=20,
                minute=0,
                id='yonhap_evening',
                name='연합뉴스 저녁',
                replace_existing=True
            )

            self.scheduler.start()
            logger.info("스케줄러 시작 완료")
            logger.info("  - 오전 7:00 프리마켓 브리핑 (공탐지수 + 미국 증시)")
            logger.info("  - 오전 8:00 브리핑 (미국장 마감 후)")
            logger.info("  - 오후 5:00 브리핑 (한국장 마감 후)")
            logger.info(f"  - 주가 변동 알림 ({STOCK_CHECK_INTERVAL}초 간격)")
            logger.info("  - TQ버스 상태 리포트 (오전 8:05)")
            logger.info("  - TQ버스 승하차 준비 알림 (1시간마다, 7% 이내시)")
            logger.info("  - TQ버스 돌파 알림 (1시간마다, 하루 최대 3회)")
            logger.info("  - 휴장일 사전 알림 (오전 7:30)")
            logger.info("  - 연합뉴스 (오전 9시, 오후 1시, 오후 8시)")

        except Exception as e:
            logger.error(f"스케줄러 시작 오류: {e}")

    def stop(self):
        """스케줄러 중지"""
        try:
            self.scheduler.shutdown()
            logger.info("스케줄러 중지됨")
        except Exception as e:
            logger.error(f"스케줄러 중지 오류: {e}")
