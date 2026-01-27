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


async def main():
    logger.info("=" * 50)
    logger.info("TeleBot 스케줄러 시작")
    logger.info("=" * 50)
    logger.info(f"Python: {sys.version}")
    logger.info(f"TZ: {os.environ.get('TZ', 'Not set')}")
    logger.info(f"TELEGRAM_BOT_TOKEN: {'Set' if os.environ.get('TELEGRAM_BOT_TOKEN') else 'Not set'}")
    logger.info(f"CHANNEL_ID: {'Set' if os.environ.get('CHANNEL_ID') else 'Not set'}")

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
