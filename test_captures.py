"""
모든 캡처 테스트 스크립트
- CNN Fear & Greed Index
- 네이버 미국 증시 (stock.naver.com)
- 네이버 한국 증시 (stock.naver.com)
"""
import asyncio
import sys
import os
import logging

# python/ 폴더를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_all_captures():
    from fear_greed_tracker import FearGreedTracker, NaverFinanceTracker
    from telegram_bot import NewsChannelBot
    from config import TELEGRAM_BOT_TOKEN, CHANNEL_ID

    bot = NewsChannelBot(TELEGRAM_BOT_TOKEN, CHANNEL_ID)
    fg_tracker = FearGreedTracker()
    naver_tracker = NaverFinanceTracker()

    logger.info("=" * 50)
    logger.info("모든 캡처 테스트 시작")
    logger.info("=" * 50)

    # 1. CNN Fear & Greed Index
    logger.info("1. CNN Fear & Greed Index 캡처 중...")
    fg_screenshot = await fg_tracker.capture_fear_greed_screenshot()
    if fg_screenshot:
        await bot.send_photo_buffer(fg_screenshot, "😱 <b>Fear & Greed Index</b> (테스트)")
        logger.info("✓ Fear & Greed 발송 완료")
    else:
        logger.error("✗ Fear & Greed 캡처 실패")

    # 2. 네이버 미국 증시
    logger.info("2. 네이버 미국 증시 캡처 중...")
    us_screenshot = await naver_tracker.capture_naver_us_market_screenshot()
    if us_screenshot:
        await bot.send_photo_buffer(us_screenshot, "🇺🇸 <b>미국 증시</b> (테스트)")
        logger.info("✓ 미국 증시 발송 완료")
    else:
        logger.error("✗ 미국 증시 캡처 실패")

    # 3. 네이버 한국 증시
    logger.info("3. 네이버 한국 증시 캡처 중...")
    kr_screenshot = await naver_tracker.capture_naver_kr_market_screenshot()
    if kr_screenshot:
        await bot.send_photo_buffer(kr_screenshot, "🇰🇷 <b>한국 증시</b> (테스트)")
        logger.info("✓ 한국 증시 발송 완료")
    else:
        logger.error("✗ 한국 증시 캡처 실패")

    logger.info("=" * 50)
    logger.info("모든 캡처 테스트 완료")
    logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_all_captures())
