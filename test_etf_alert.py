"""
3X ETF 테스트 메시지 발송
"""
import asyncio
import sys
import os
import logging

# python/ 폴더를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from etf_tracker import ETFTracker
from telegram_bot import NewsChannelBot
from config import TELEGRAM_BOT_TOKEN, CHANNEL_ID

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def send_etf_test():
    """3X ETF 테스트 메시지 발송"""
    logger.info("3X ETF 테스트 메시지 발송 시작...")

    bot = NewsChannelBot(TELEGRAM_BOT_TOKEN, CHANNEL_ID)
    tracker = ETFTracker()

    # ETF 데이터 가져오기
    etf_data = tracker.get_all_etf_data()

    if etf_data:
        # 메시지 포맷
        msg = tracker.format_etf_report(etf_data)

        # 발송
        await bot.send_news(msg)
        logger.info("3X ETF 테스트 메시지 발송 완료!")
        print("\n" + "="*50)
        print("메시지 미리보기:")
        print("="*50)
        print(msg)
        print("="*50)
    else:
        logger.error("ETF 데이터를 가져올 수 없습니다")


if __name__ == "__main__":
    asyncio.run(send_etf_test())
