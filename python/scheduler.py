"""
자동 뉴스 발행, ETF 추적 및 주가 변동 알림 스케줄러

기능:
- 주가 변동 알림 (5분마다, 최소 10분 간격)
- 오전 브리핑 (미국 장 마감 후 10분) - Fear & Greed + 미국 증시 + 3X ETF
- 오후 브리핑 (15:40 KST) - 한국 증시
"""
import logging
import asyncio
import json
import os
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import TELEGRAM_BOT_TOKEN, CHANNEL_ID, DIVIDEND_CHANNEL_ID, STOCK_CHECK_INTERVAL, UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN, get_us_market_close_time_kst
from telegram_bot import NewsChannelBot
from stock_monitor import StockMonitor
from market_holidays import is_us_market_holiday, is_us_extended_market_hours
from fear_greed_tracker import FearGreedTracker, NaverFinanceTracker
from etf_tracker import ETFTracker
from etf_table_generator import ETFTableGenerator
from tqbus_tracker import TqBusTracker
from dividend_monitor import DividendMonitor

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

# 알림 최소 간격 (초) - 10분
MIN_ALERT_INTERVAL_SECONDS = 10 * 60

# 브리핑 쿨다운 시간 (초) - 12시간 (하루 1회 보장)
BRIEFING_COOLDOWN_SECONDS = 12 * 60 * 60

# 마지막 알림 발송 시간 Redis 키
LAST_ALERT_TIME_KEY = "last_alert_time"


class NewsScheduler:
    """주가 변동 알림 및 브리핑 스케줄러"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.bot = NewsChannelBot(TELEGRAM_BOT_TOKEN, CHANNEL_ID)
        self.dividend_bot = NewsChannelBot(TELEGRAM_BOT_TOKEN, DIVIDEND_CHANNEL_ID)
        self.dividend_monitor = DividendMonitor()
        self.stock_monitor = StockMonitor()
        self.fear_greed_tracker = FearGreedTracker()
        self.naver_tracker = NaverFinanceTracker()
        self.etf_tracker = ETFTracker()
        self.etf_table_generator = ETFTableGenerator()
        self.tqbus_tracker = TqBusTracker()
        self.dividend_monitor = DividendMonitor()
        # self.dividend_alert_monitor = DividendAlertMonitor()  # TODO: 클래스 구현 필요
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

    def _get_last_alert_time(self):
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
        """마지막 알림 발송 시간 저장 (Redis 기반, 10분 TTL)"""
        self.last_alert_time = dt  # 메모리에도 저장
        if redis_client:
            try:
                # 10분 TTL (10분 간격 체크에 충분)
                redis_client.setex(LAST_ALERT_TIME_KEY, 600, dt.isoformat())
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
            # 주말 여부 확인 (미국 동부시간 기준)
            import pytz
            us_eastern = pytz.timezone('America/New_York')
            us_now = datetime.now(us_eastern)
            is_weekend = us_now.weekday() >= 5  # 미국 기준 토(5), 일(6)

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
                logger.info(f"알림 후보: {alert.symbol} ({alert.change_percent:+.2f}%, 레벨 {current_level})")

            if not new_alerts:
                logger.info("새로운 알림 없음 (24시간 내 중복 필터링)")
                return

            # 10분 최소 간격 체크 (Redis 기반)
            now = datetime.now()
            last_time = self._get_last_alert_time()
            if last_time:
                elapsed = (now - last_time).total_seconds()
                if elapsed < MIN_ALERT_INTERVAL_SECONDS:
                    remaining = int((MIN_ALERT_INTERVAL_SECONDS - elapsed) / 60)
                    logger.info(f"알림 발송 대기 중 (최소 간격 10분, {remaining}분 남음)")
                    return

            # 파일 백업 저장 (Redis 미사용 시 폴백)
            self._save_alert_history()

            # 발송 직전 이중 체크 (Render 동시 실행 방지)
            final_alerts = []
            for alert in new_alerts:
                current_level = self._get_threshold_level(alert.change_percent, alert.category)
                if not self._check_alert_exists(alert.symbol, current_level):
                    final_alerts.append(alert)
                    self._save_alert_record(alert.symbol, current_level)  # 즉시 저장
                else:
                    logger.info(f"이중 체크 스킵: {alert.symbol} 레벨 {current_level}")

            if not final_alerts:
                logger.info("발송 직전 이중 체크: 모든 알림 이미 발송됨")
                return

            # 알림 메시지 생성 및 전송
            message = self.stock_monitor.format_alert_message(final_alerts)

            if message:
                success = await self.bot.send_news(message)

                if success:
                    self._set_last_alert_time(now)  # 발송 시간 기록 (Redis)
                    logger.info(f"주가 변동 알림 발송 성공 ({len(final_alerts)}개 항목)")
                else:
                    logger.error("주가 변동 알림 발송 실패")

            # 배당주 리스트 별도 체크 (SCHD, VYM, HDV, JEPI, JEPQ, DIVO, O)
            await self._check_dividend_stocks()

        except Exception as e:
            logger.error(f"주가 변동 체크 오류: {e}")

    async def send_morning_briefing(self, force: bool = False):
        """
        오전 브리핑 발송 (08:00 KST)
        - Fear & Greed 스크린샷
        - 미국 증시 스크린샷

        Args:
            force: True면 중복 체크 무시 (수동 트리거용)
        """
        try:
            # 중복 발송 방지 (Redis) - force=True면 스킵
            if not force and self._check_briefing_sent("morning"):
                logger.info("오전 브리핑 스킵 (이미 발송됨)")
                return

            logger.info("오전 브리핑 발송 시작...")

            # 1. Fear & Greed (텍스트)
            fg_data = self.fear_greed_tracker.fetch_fear_greed_data()
            if fg_data:
                msg = self.fear_greed_tracker.format_text_message(fg_data)
                await self.bot.send_news(msg)
                logger.info("Fear & Greed 텍스트 발송 완료")

            # 2. 미국 증시 (텍스트)
            us_data = self.naver_tracker.fetch_us_market_data()
            if us_data:
                msg = self.naver_tracker.format_text_message(us_data)
                await self.bot.send_news(msg)
                logger.info("미국 증시 텍스트 발송 완료")

            # 3. 3X ETF 리스트 (텍스트)
            try:
                etf_data = self.etf_tracker.get_all_etf_data()
                if etf_data:
                    etf_msg = self.etf_tracker.format_etf_report(etf_data)
                    await self.bot.send_news(etf_msg)
                    logger.info("3X ETF 텍스트 발송 완료")
            except Exception as etf_err:
                logger.error(f"3X ETF 발송 오류: {etf_err}")

            # 발송 완료 기록 (Redis)
            self._mark_briefing_sent("morning")
            logger.info("오전 브리핑 발송 완료")

            # 배당주 채널로 Fear & Greed + 미국 증시 + 3X ETF 전송
            try:
                if fg_data:
                    msg = self.fear_greed_tracker.format_text_message(fg_data)
                    await self.dividend_bot.send_news(msg)
                if us_data:
                    msg = self.naver_tracker.format_text_message(us_data)
                    await self.dividend_bot.send_news(msg)
                if 'etf_msg' in locals() and etf_msg:
                    await self.dividend_bot.send_news(etf_msg)
                logger.info("배당주 채널 오전 브리핑 발송 완료 (Fear & Greed + 미국 증시 + 3X ETF)")
            except Exception as div_err:
                logger.error(f"배당주 채널 오전 브리핑 오류: {div_err}")

        except Exception as e:
            logger.error(f"오전 브리핑 발송 오류: {e}")

    async def send_afternoon_briefing(self, force: bool = False):
        """
        오후 브리핑 발송 (15:40 KST)
        - 한국 증시 스크린샷

        Args:
            force: True면 중복 체크 무시 (수동 트리거용)
        """
        try:
            # 중복 발송 방지 (Redis) - force=True면 스킵
            if not force and self._check_briefing_sent("afternoon"):
                logger.info("오후 브리핑 스킵 (이미 발송됨)")
                return

            logger.info("오후 브리핑 발송 시작...")

            # 한국 증시 (텍스트)
            kr_data = self.naver_tracker.fetch_kr_market_data()
            if kr_data:
                msg = self.naver_tracker.format_kr_text_message(kr_data)
                await self.bot.send_news(msg)
                logger.info("한국 증시 텍스트 발송 완료")
            else:
                logger.warning("한국 증시 데이터 가져오기 실패")

            # 발송 완료 기록 (Redis)
            self._mark_briefing_sent("afternoon")
            logger.info("오후 브리핑 발송 완료")

            # 배당주 채널로도 한국 증시 전송
            try:
                if kr_data:
                    msg = self.naver_tracker.format_kr_text_message(kr_data)
                    await self.dividend_bot.send_news(msg)
                    logger.info("배당주 채널 오후 브리핑 발송 완료")
            except Exception as div_err:
                logger.error(f"배당주 채널 오후 브리핑 오류: {div_err}")

        except Exception as e:
            logger.error(f"오후 브리핑 발송 오류: {e}")

    
    async def send_dividend_report(self):
        try:
            logger.info('배당주 리포트 전송 시작')
            
            # 배당 데이터 수집
            dividend_data = await self.dividend_monitor.fetch_dividend_data()
            
            if dividend_data:
                # 배당 정보 포맷팅
                message = await self.dividend_monitor.format_dividend_briefing(dividend_data)
                
                # 배당 채널로 전송
                await self.dividend_bot.send_news(message, parse_mode='HTML')
                logger.info('배당주 리포트 전송 완료')
            else:
                logger.warning('배당 데이터 수집 실패')
                
        except Exception as e:
            logger.error(f'배당주 리포트 전송 오류: {e}')


    async def _check_dividend_stocks(self):
        """
        배당주 리스트 가격 변동 체크 (SCHD, VYM, HDV, JEPI, JEPQ, DIVO, O)
        배당주 채널로만 알림 전송
        """
        try:
            # 배당주 심볼 리스트
            dividend_symbols = list(self.dividend_monitor.DIVIDEND_ETFS.keys())
            
            # 배당주만 체크
            alerts = self.stock_monitor.check_symbols(dividend_symbols)
            
            if not alerts:
                return
            
            # 중복 필터링 (DIV_ 접두사로 기존 채널과 분리)
            new_alerts = []
            for alert in alerts:
                current_level = self._get_threshold_level(alert.change_percent, alert.category)
                if not self._check_alert_exists(f"DIV_{alert.symbol}", current_level):
                    new_alerts.append(alert)
                    self._save_alert_record(f"DIV_{alert.symbol}", current_level)
            
            if new_alerts:
                message = self.stock_monitor.format_alert_message(new_alerts)
                if message:
                    await self.dividend_bot.send_news(message)
                    logger.info(f"배당주 가격 변동 알림 발송 ({len(new_alerts)}개)")
        
        except Exception as e:
            logger.error(f"배당주 가격 변동 체크 오류: {e}")

    async def send_tqbus_status(self, force: bool = False):
        """
        TQ버스 현재 상태 발송 (18:00 KST)

        Args:
            force: True면 중복 체크 무시 (수동 트리거용)
        """
        try:
            # 중복 발송 방지 (Redis) - force=True면 스킵
            if not force and self._check_briefing_sent("tqbus_status"):
                logger.info("TQ버스 상태 스킵 (이미 발송됨)")
                return

            logger.info("TQ버스 상태 발송 시작...")

            msg = self.tqbus_tracker.format_status_message()
            if msg:
                await self.bot.send_news(msg)
                logger.info("TQ버스 상태 발송 완료")

            # 발송 완료 기록 (Redis)
            self._mark_briefing_sent("tqbus_status")

        except Exception as e:
            logger.error(f"TQ버스 상태 발송 오류: {e}")

    async def send_dividend_briefing(self, force: bool = False):
        """
        배당주 브리핑 발송 (09:00 KST)
        """
        try:
            # 중복 발송 방지 (Redis) - force=True면 스킵
            if not force and self._check_briefing_sent("dividend"):
                logger.info("배당 브리핑 스킵 (이미 발송됨)")
                return

            logger.info("배당 브리핑 발송 시작...")

            # 배당 데이터 수집
            dividend_data = self.dividend_monitor.fetch_dividend_data()
            if dividend_data:
                msg = self.dividend_monitor.format_dividend_briefing(dividend_data)
                
                # 배당 채널로 발송 (config.py의 DIVIDEND_CHANNEL_ID 사용 필요)
                # 현재 NewsChannelBot은 기본 TOKEN/CHANNEL_ID만 사용하므로
                # 배당 채널용 봇 인스턴스를 따로 생성하거나, send_news에 chat_id 인자를 추가해야 함.
                # 편의상 기존 봇 인스턴스에 채널 ID만 바꿔서 호출 시도 (TelegramBot 클래스 수정 필요할 수 있음)
                # 여기서는 NewsChannelBot이 단일 채널 고정이라 가정하고,
                # 새로운 봇 인스턴스를 생성하여 배당 채널 ID를 주입.
                from config import TELEGRAM_BOT_TOKEN, DIVIDEND_CHANNEL_ID
                
                # DIVIDEND_CHANNEL_ID가 설정되어 있으면 그쪽으로, 아니면 기본 채널로
                target_channel = DIVIDEND_CHANNEL_ID if DIVIDEND_CHANNEL_ID else CHANNEL_ID
                
                dividend_bot = NewsChannelBot(TELEGRAM_BOT_TOKEN, target_channel)
                await dividend_bot.send_news(msg)
                logger.info(f"배당 브리핑 발송 완료 (Target: {target_channel})")
            else:
                logger.warning("배당 데이터 수집 실패 또는 데이터 없음")

            # 발송 완료 기록 (Redis)
            self._mark_briefing_sent("dividend")

        except Exception as e:
            logger.error(f"배당 브리핑 발송 오류: {e}")

    async def check_dividend_price_alerts(self):
        """
        배당 포트폴리오 가격 변동 알림 (5분 간격)
        """
        try:
             # 배당 채널 봇 인스턴스 생성
            from config import TELEGRAM_BOT_TOKEN, DIVIDEND_CHANNEL_ID
            target_channel = DIVIDEND_CHANNEL_ID if DIVIDEND_CHANNEL_ID else CHANNEL_ID
            dividend_bot = NewsChannelBot(TELEGRAM_BOT_TOKEN, target_channel)

            # 가격 알림 확인 - TODO: DividendAlertMonitor 구현 필요
            # alerts = self.dividend_alert_monitor.check_price_alerts()
            # for msg in alerts:
            #      await dividend_bot.send_news(msg)
            #      logger.info(f"배당 가격 알림 발송: {msg.splitlines()[0]}")
            pass
                 
        except Exception as e:
            logger.error(f"배당 가격 알림 체크 오류: {e}")

    async def check_dividend_news_alerts(self):
        """
        배당 포트폴리오 뉴스 알림 (1시간 간격)
        """
        try:
             # 배당 채널 봇 인스턴스 생성
            from config import TELEGRAM_BOT_TOKEN, DIVIDEND_CHANNEL_ID
            target_channel = DIVIDEND_CHANNEL_ID if DIVIDEND_CHANNEL_ID else CHANNEL_ID
            dividend_bot = NewsChannelBot(TELEGRAM_BOT_TOKEN, target_channel)

            # 뉴스 알림 확인 - TODO: DividendAlertMonitor 구현 필요
            # alerts = self.dividend_alert_monitor.check_news_alerts()
            # for msg in alerts:
            #      await dividend_bot.send_news(msg)
            #      logger.info(f"배당 뉴스 알림 발송: {msg.splitlines()[0]}")
            pass

        except Exception as e:
            logger.error(f"배당 뉴스 알림 체크 오류: {e}")

    async def send_dividend_closing_briefing(self, force: bool = False):
        """
        배당 포트폴리오 마감 브리핑 (장 마감 후)
        """
        try:
            if not force and self._check_briefing_sent("dividend_closing"):
                logger.info("배당 마감 브리핑 스킵 (이미 발송됨)")
                return

            # 배당 채널 봇 인스턴스 생성
            from config import TELEGRAM_BOT_TOKEN, DIVIDEND_CHANNEL_ID
            target_channel = DIVIDEND_CHANNEL_ID if DIVIDEND_CHANNEL_ID else CHANNEL_ID
            dividend_bot = NewsChannelBot(TELEGRAM_BOT_TOKEN, target_channel)

            # TODO: DividendAlertMonitor 구현 필요
            # msg = self.dividend_alert_monitor.format_closing_briefing()
            # await dividend_bot.send_news(msg)
            logger.info("배당 마감 브리핑 스킵 (DividendAlertMonitor 미구현)")
            
            self._mark_briefing_sent("dividend_closing")

        except Exception as e:
            logger.error(f"배당 마감 브리핑 오류: {e}")

    async def check_tqbus_crossover(self):
        """
        TQ버스 이평선 돌파 체크 (종가 기준, 미국 장 마감 시간)
        승차(상향 돌파) / 하차(하향 돌파) 신호
        """
        try:
            # 중복 발송 방지 (Redis)
            if self._check_briefing_sent("tqbus_crossover"):
                return  # 오늘 이미 발송됨

            crossover = self.tqbus_tracker.detect_crossover()
            if crossover:
                msg = self.tqbus_tracker.format_crossover_message(crossover)
                if msg:
                    await self.bot.send_news(msg)
                    logger.info(f"TQ버스 {crossover} 신호 발송 완료")

                    # 발송 완료 기록 (Redis)
                    self._mark_briefing_sent("tqbus_crossover")

        except Exception as e:
            logger.error(f"TQ버스 돌파 체크 오류: {e}")

    async def check_tqbus_alert(self):
        """
        TQ버스 이평선 단계별 알림 (실시간 가격 기준, 프리+정규+애프터 시간대)
        레벨: +7%, +5%, +3%, -3%, -5%, -7% (각 레벨당 하루 1회)
        """
        try:
            # 주말 체크
            if is_us_market_holiday():
                return  # 주말 또는 휴장일

            # 미국 확장 시간대(프리+정규+애프터) 체크
            if not is_us_extended_market_hours():
                return  # 장 시간 외

            # 현재 알림 레벨 확인
            alert_level = self.tqbus_tracker.should_alert()
            if alert_level is None:
                return  # 알림 범위 밖

            # 레벨별 중복 발송 방지 (Redis)
            level_key = f"tqbus_alert_{alert_level:+.1f}"  # 예: tqbus_alert_+7.0, tqbus_alert_-3.0
            if self._check_briefing_sent(level_key):
                return  # 해당 레벨 오늘 이미 발송됨

            # 알림 메시지 생성 및 발송
            msg = self.tqbus_tracker.format_alert_message(alert_level)
            if msg:
                await self.bot.send_news(msg)
                logger.info(f"TQ버스 {alert_level:+.1f}% 레벨 알림 발송 완료")

                # 발송 완료 기록 (Redis, 24시간 TTL)
                self._mark_briefing_sent(level_key)

        except Exception as e:
            logger.error(f"TQ버스 알림 체크 오류: {e}")

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

            # 오전 브리핑 (미국 장 마감 후 10분, 평일만)
            # 서머타임: 05:10 KST, 일반: 06:10 KST
            close_hour, close_minute = get_us_market_close_time_kst()
            briefing_hour = close_hour
            briefing_minute = close_minute
            self.scheduler.add_job(
                self.send_morning_briefing,
                'cron',
                hour=briefing_hour,
                minute=briefing_minute,
                day_of_week='sat',  # 토요일만 발송
                id='morning_briefing',
                name='오전 브리핑 (장마감 후 10분)',
                replace_existing=True
            )

            # 오후 브리핑 (한국 장 마감 후 10분, 15:40 KST)
            self.scheduler.add_job(
                self.send_afternoon_briefing,
                'cron',
                hour=15,
                minute=40,
                day_of_week='mon-fri',
                id='afternoon_briefing',
                name='오후 브리핑 (한국 장마감 후 10분)',
                replace_existing=True
            )

            # TQ버스 현재 상태 (18:00 KST, 화~토 = 미국 장 다음날)
            self.scheduler.add_job(
                self.send_tqbus_status,
                'cron',
                hour=18,
                minute=0,
                day_of_week='sat',
                id='tqbus_status',
                name='TQ버스 상태',
                replace_existing=True
            )

            # TQ버스 이평선 돌파 체크 (미국 장 마감 시간, 종가 기준)
            close_hour, close_minute = get_us_market_close_time_kst()
            self.scheduler.add_job(
                self.check_tqbus_crossover,
                'cron',
                hour=close_hour,
                minute=close_minute,
                day_of_week='tue-sat',  # 미국 월~금 마감 = 한국 화~토
                id='tqbus_crossover',
                name='TQ버스 돌파 체크 (종가)',
                replace_existing=True
            )

            # TQ버스 이평선 단계별 알림 (5분마다, 프리+정규+애프터)
            # 레벨: +7%, +5%, +3%, -3%, -5%, -7%
            self.scheduler.add_job(
                self.check_tqbus_alert,
                'interval',
                seconds=STOCK_CHECK_INTERVAL,
                id='tqbus_alert',
                name='TQ버스 단계별 알림',
                replace_existing=True
            )

            # 배당주 리포트 (매주 월요일 08:30 KST)
            self.scheduler.add_job(
                self.send_dividend_report,
                'cron',
                hour=8,
                minute=30,
                day_of_week=0,  # Monday
                id='send_dividend_report',
                name='배당주 리포트',
                replace_existing=True
            )

            # 배당 브리핑 (09:00 KST, 화~토 = 미국 장 다음날)
            self.scheduler.add_job(
                self.send_dividend_briefing,
                'cron',
                hour=9,
                minute=0,
                day_of_week='tue-sat',
                id='dividend_briefing',
                name='배당 브리핑',
                replace_existing=True
            )

            # 배당 가격 알림 (5분 간격)
            self.scheduler.add_job(
                self.check_dividend_price_alerts,
                'interval',
                seconds=STOCK_CHECK_INTERVAL,
                id='dividend_price_alert',
                name='배당 가격 알림',
                replace_existing=True
            )

            # 배당 뉴스 알림 (1시간 간격)
            self.scheduler.add_job(
                self.check_dividend_news_alerts,
                'interval',
                minutes=60,
                id='dividend_news_alert',
                name='배당 뉴스 알림',
                replace_existing=True
            )

            # 배당 마감 브리핑 (09:05 KST - 기존 배당 브리핑 직후)
            self.scheduler.add_job(
                self.send_dividend_closing_briefing,
                'cron',
                hour=9,
                minute=5,
                day_of_week='tue-sat',
                id='dividend_closing_briefing',
                name='배당 마감 브리핑',
                replace_existing=True
            )

            self.scheduler.start()
            logger.info("스케줄러 시작 완료")
            logger.info(f"  - 주가 변동 알림 ({STOCK_CHECK_INTERVAL}초 간격)")
            logger.info(f"  - 오전 브리핑 ({briefing_hour:02d}:{briefing_minute:02d} KST, 화~토 = 미국 장마감 후 10분)")
            logger.info("  - 오후 브리핑 (15:40 KST, 월~금 = 한국 장마감 후 10분)")
            logger.info("  - TQ버스 상태 (18:00 KST, 화~토)")
            logger.info(f"  - TQ버스 돌파 체크 ({STOCK_CHECK_INTERVAL}초 간격)")
            logger.info("  - 배당주 리포트 (매주 월요일 08:30 KST)")

        except Exception as e:
            logger.error(f"스케줄러 시작 오류: {e}")

    def stop(self):
        """스케줄러 중지"""
        try:
            self.scheduler.shutdown()
            logger.info("스케줄러 중지됨")
        except Exception as e:
            logger.error(f"스케줄러 중지 오류: {e}")
