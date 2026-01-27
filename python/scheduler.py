"""
자동 뉴스 발행, ETF 추적 및 주가 변동 알림 스케줄러

기능:
- 주가 변동 알림 (5분마다)
- 오전 브리핑 (08:00 KST) - Fear & Greed + 미국 증시
- 오후 브리핑 (15:30 KST) - 한국 증시
"""
import logging
import asyncio
import json
import os
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import TELEGRAM_BOT_TOKEN, CHANNEL_ID, STOCK_CHECK_INTERVAL, UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN
from telegram_bot import NewsChannelBot
from stock_monitor import StockMonitor
from market_holidays import is_us_market_holiday
from fear_greed_tracker import FearGreedTracker, NaverFinanceTracker

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

# 알림 최소 간격 (초) - 30분
MIN_ALERT_INTERVAL_SECONDS = 30 * 60

# 브리핑 쿨다운 시간 (초) - 12시간 (하루 1회 보장)
BRIEFING_COOLDOWN_SECONDS = 12 * 60 * 60

# 마지막 알림 발송 시간 Redis 키
LAST_ALERT_TIME_KEY = "last_alert_time"


class NewsScheduler:
    """주가 변동 알림 및 브리핑 스케줄러"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.bot = NewsChannelBot(TELEGRAM_BOT_TOKEN, CHANNEL_ID)
        self.stock_monitor = StockMonitor()
        self.fear_greed_tracker = FearGreedTracker()
        self.naver_tracker = NaverFinanceTracker()
        self.stock_alerted_today: dict = self._load_alert_history()
        self.last_alert_time: datetime = None  # 마지막 알림 발송 시간

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

        # 인메모리에도 저장
        today = datetime.now().strftime("%Y-%m-%d")
        self.stock_alerted_today[symbol] = {"date": today, "level": level}

        # 즉시 파일에 저장 (Redis 미사용 시)
        if not redis_client:
            self._save_alert_history()

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

    def _check_briefing_sent(self, briefing_type: str) -> bool:
        """브리핑이 이미 발송되었는지 확인 (Redis 기반)"""
        key = f"briefing:{briefing_type}:{datetime.now().strftime('%Y-%m-%d')}"

        if redis_client:
            try:
                exists = redis_client.exists(key)
                if exists:
                    logger.info(f"Redis: {briefing_type} 브리핑 이미 발송됨 (오늘)")
                return bool(exists)
            except Exception as e:
                logger.error(f"Redis 조회 오류: {e}")

        return False

    def _mark_briefing_sent(self, briefing_type: str):
        """브리핑 발송 기록 저장 (Redis 기반, 12시간 TTL)"""
        key = f"briefing:{briefing_type}:{datetime.now().strftime('%Y-%m-%d')}"

        if redis_client:
            try:
                redis_client.setex(key, BRIEFING_COOLDOWN_SECONDS, "1")
                logger.info(f"Redis: {briefing_type} 브리핑 발송 기록 저장")
            except Exception as e:
                logger.error(f"Redis 저장 오류: {e}")

    def _get_last_alert_time(self) -> datetime | None:
        """마지막 알림 발송 시간 조회 (Redis 기반)"""
        if redis_client:
            try:
                timestamp = redis_client.get(LAST_ALERT_TIME_KEY)
                if timestamp:
                    return datetime.fromisoformat(timestamp)
            except Exception as e:
                logger.error(f"Redis 조회 오류 (last_alert_time): {e}")
        return self.last_alert_time  # 폴백: 메모리

    def _set_last_alert_time(self, dt: datetime):
        """마지막 알림 발송 시간 저장 (Redis 기반, 1시간 TTL)"""
        self.last_alert_time = dt  # 메모리에도 저장
        if redis_client:
            try:
                # 1시간 TTL (30분 간격 체크에 충분)
                redis_client.setex(LAST_ALERT_TIME_KEY, 3600, dt.isoformat())
                logger.info(f"Redis: 마지막 알림 시간 저장 ({dt.strftime('%H:%M:%S')})")
            except Exception as e:
                logger.error(f"Redis 저장 오류 (last_alert_time): {e}")

    def _get_threshold_level(self, change_percent: float, category: str) -> int:
        """
        변동률에 해당하는 임계값 레벨 반환
        - 지수/암호화폐: 1%, 2%, 3%, 4%, 5%... 단위
        - 개별주/ETF: 5%, 10%, 15%... 단위
        """
        abs_change = abs(change_percent)
        if category in ('index', 'crypto'):
            return int(abs_change)
        else:
            return int(abs_change // 5) * 5

    async def check_stock_alerts(self):
        """
        주가 변동 알림 체크
        - 지수/암호화폐: 1%, 2%, 3%... 각 구간 돌파 시 알림
        - 개별주/레버리지 ETF: 5%, 10%, 15%... 각 구간 돌파 시 알림
        - 같은 종목/레벨은 24시간 내 재알림 안 함 (Redis TTL)
        - 주말: 나스닥 선물 + 비트코인만 체크
        """
        try:
            # 주말 여부 확인
            is_weekend = datetime.now().weekday() >= 5

            if is_weekend:
                logger.info("주가 변동 체크 시작 (주말 모드: NQ선물 + BTC)...")
                alerts = self.stock_monitor.check_weekend()
            else:
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

            # 30분 최소 간격 체크 (Redis 기반)
            now = datetime.now()
            last_time = self._get_last_alert_time()
            if last_time:
                elapsed = (now - last_time).total_seconds()
                if elapsed < MIN_ALERT_INTERVAL_SECONDS:
                    remaining = int((MIN_ALERT_INTERVAL_SECONDS - elapsed) / 60)
                    logger.info(f"알림 발송 대기 중 (최소 간격 30분, {remaining}분 남음)")
                    return

            # 파일 백업 저장 (Redis 미사용 시 폴백)
            self._save_alert_history()

            # 알림 메시지 생성 및 전송
            message = self.stock_monitor.format_alert_message(new_alerts)

            if message:
                success = await self.bot.send_news(message)

                if success:
                    self._set_last_alert_time(now)  # 발송 시간 기록 (Redis)
                    logger.info(f"주가 변동 알림 발송 성공 ({len(new_alerts)}개 항목)")
                else:
                    logger.error("주가 변동 알림 발송 실패")

        except Exception as e:
            logger.error(f"주가 변동 체크 오류: {e}")

    async def send_morning_briefing(self):
        """
        오전 브리핑 발송 (08:00 KST)
        - Fear & Greed 스크린샷
        - 미국 증시 스크린샷
        """
        try:
            # 중복 발송 방지 (Redis)
            if self._check_briefing_sent("morning"):
                logger.info("오전 브리핑 스킵 (이미 발송됨)")
                return

            logger.info("오전 브리핑 발송 시작...")

            # 1. Fear & Greed 스크린샷
            fg_screenshot = await self.fear_greed_tracker.capture_fear_greed_screenshot()
            if fg_screenshot:
                await self.bot.send_photo_buffer(fg_screenshot, "🌅 <b>오전 브리핑</b> - Fear & Greed Index")
                logger.info("Fear & Greed 스크린샷 발송 완료")
            else:
                # 스크린샷 실패 시 텍스트 폴백
                fg_data = self.fear_greed_tracker.fetch_fear_greed_data()
                if fg_data:
                    msg = self.fear_greed_tracker.format_text_message(fg_data)
                    await self.bot.send_news(msg)
                    logger.info("Fear & Greed 텍스트 폴백 발송 완료")

            # 2. 미국 증시 스크린샷
            us_screenshot = await self.naver_tracker.capture_naver_us_market_screenshot()
            if us_screenshot:
                await self.bot.send_photo_buffer(us_screenshot, "📊 <b>미국 증시 현황</b>")
                logger.info("미국 증시 스크린샷 발송 완료")
            else:
                # 스크린샷 실패 시 텍스트 폴백
                us_data = self.naver_tracker.fetch_us_market_data()
                if us_data:
                    msg = self.naver_tracker.format_text_message(us_data)
                    await self.bot.send_news(msg)
                    logger.info("미국 증시 텍스트 폴백 발송 완료")

            # 발송 완료 기록 (Redis)
            self._mark_briefing_sent("morning")
            logger.info("오전 브리핑 발송 완료")

        except Exception as e:
            logger.error(f"오전 브리핑 발송 오류: {e}")

    async def send_afternoon_briefing(self):
        """
        오후 브리핑 발송 (15:30 KST)
        - 한국 증시 스크린샷
        """
        try:
            # 중복 발송 방지 (Redis)
            if self._check_briefing_sent("afternoon"):
                logger.info("오후 브리핑 스킵 (이미 발송됨)")
                return

            logger.info("오후 브리핑 발송 시작...")

            # 한국 증시 스크린샷
            kr_screenshot = await self.naver_tracker.capture_naver_kr_market_screenshot()
            if kr_screenshot:
                await self.bot.send_photo_buffer(kr_screenshot, "🇰🇷 <b>오후 브리핑</b> - 한국 증시 마감")
                logger.info("한국 증시 스크린샷 발송 완료")
            else:
                logger.warning("한국 증시 스크린샷 캡처 실패")

            # 발송 완료 기록 (Redis)
            self._mark_briefing_sent("afternoon")
            logger.info("오후 브리핑 발송 완료")

        except Exception as e:
            logger.error(f"오후 브리핑 발송 오류: {e}")

    def start(self):
        """스케줄러 시작"""
        try:
            logger.info("스케줄러 시작...")

            # 주가 변동 알림 체크 (주기적 - 5분마다)
            self.scheduler.add_job(
                self.check_stock_alerts,
                'interval',
                seconds=STOCK_CHECK_INTERVAL,
                id='check_stock_alerts',
                name='주가 변동 알림',
                replace_existing=True
            )

            # 오전 브리핑 (08:00 KST, 평일만)
            self.scheduler.add_job(
                self.send_morning_briefing,
                'cron',
                hour=8,
                minute=0,
                day_of_week='mon-fri',
                id='morning_briefing',
                name='오전 브리핑',
                replace_existing=True
            )

            # 오후 브리핑 (15:30 KST, 평일만)
            self.scheduler.add_job(
                self.send_afternoon_briefing,
                'cron',
                hour=15,
                minute=30,
                day_of_week='mon-fri',
                id='afternoon_briefing',
                name='오후 브리핑',
                replace_existing=True
            )

            self.scheduler.start()
            logger.info("스케줄러 시작 완료")
            logger.info(f"  - 주가 변동 알림 ({STOCK_CHECK_INTERVAL}초 간격)")
            logger.info("  - 오전 브리핑 (08:00 KST, 평일)")
            logger.info("  - 오후 브리핑 (15:30 KST, 평일)")

        except Exception as e:
            logger.error(f"스케줄러 시작 오류: {e}")

    def stop(self):
        """스케줄러 중지"""
        try:
            self.scheduler.shutdown()
            logger.info("스케줄러 중지됨")
        except Exception as e:
            logger.error(f"스케줄러 중지 오류: {e}")
