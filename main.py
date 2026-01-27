"""
TeleBot - Minimal Test
배포 테스트용 최소 코드
"""
import asyncio
import logging
import sys
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


async def main():
    logger.info("=" * 50)
    logger.info("TeleBot 배포 테스트 시작")
    logger.info("=" * 50)
    logger.info(f"Python: {sys.version}")
    logger.info(f"TZ: {os.environ.get('TZ', 'Not set')}")
    logger.info(f"TELEGRAM_BOT_TOKEN: {'Set' if os.environ.get('TELEGRAM_BOT_TOKEN') else 'Not set'}")
    logger.info(f"CHANNEL_ID: {'Set' if os.environ.get('CHANNEL_ID') else 'Not set'}")

    # 10초 대기 후 종료 (테스트용)
    logger.info("10초 후 종료...")
    await asyncio.sleep(10)
    logger.info("테스트 완료!")


if __name__ == "__main__":
    asyncio.run(main())
