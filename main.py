"""
TeleBot - Telegram Bot Scheduler
텔레그램 봇 스케줄러 엔트리포인트
"""
import asyncio
import logging
import sys
import os

# python/ 폴더를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


async def send_test_briefing():
    """시작 시 테스트 브리핑 발송"""
    from fear_greed_tracker import FearGreedTracker, NaverFinanceTracker
    from telegram_bot import NewsChannelBot
    from config import TELEGRAM_BOT_TOKEN, CHANNEL_ID

    logger.info("=" * 50)
    logger.info("테스트 브리핑 발송 시작")
    logger.info("=" * 50)

    bot = NewsChannelBot(TELEGRAM_BOT_TOKEN, CHANNEL_ID)

    # 1. Fear & Greed Index
    logger.info("CNN Fear & Greed 캡처 중...")
    fg_tracker = FearGreedTracker()
    fg_screenshot = await fg_tracker.capture_fear_greed_screenshot()
    if fg_screenshot:
        await bot.send_photo_buffer(fg_screenshot, "😱 <b>Fear & Greed Index</b> (Render Test)")
        logger.info("Fear & Greed 발송 완료")
    else:
        logger.error("Fear & Greed 캡처 실패")

    # 2. 네이버 세계 증시
    logger.info("네이버 세계 증시 캡처 중...")
    naver_tracker = NaverFinanceTracker()
    naver_screenshot = await naver_tracker.capture_naver_world_screenshot()
    if naver_screenshot:
        await bot.send_photo_buffer(naver_screenshot, "🌍 <b>세계 증시 현황</b> (Render Test)")
        logger.info("네이버 증시 발송 완료")
    else:
        logger.error("네이버 증시 캡처 실패")

    logger.info("테스트 브리핑 발송 완료!")


async def main():
    logger.info("=" * 50)
    logger.info("TeleBot 스케줄러 시작")
    logger.info("=" * 50)
    logger.info(f"Python: {sys.version}")
    logger.info(f"TZ: {os.environ.get('TZ', 'Not set')}")
    logger.info(f"TELEGRAM_BOT_TOKEN: {'Set' if os.environ.get('TELEGRAM_BOT_TOKEN') else 'Not set'}")
    logger.info(f"CHANNEL_ID: {'Set' if os.environ.get('CHANNEL_ID') else 'Not set'}")

    # 테스트 브리핑 발송 (시작 시 1회)
    await send_test_briefing()

    # 스케줄러 import 및 실행
    from scheduler import NewsScheduler

    scheduler = NewsScheduler()
    scheduler.start()

    # 무한 루프로 스케줄러 유지
    logger.info("스케줄러 실행 중... (Ctrl+C로 종료)")
    try:
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        logger.info("종료 신호 수신")
        scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main())
