"""
차트와 ETF 테이블 이미지 발송 스크립트
"""
import asyncio
import sys
import os

# 한글 인코딩 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# python 디렉토리 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from python.etf_tracker import ETFTracker
from python.telegram_bot import NewsChannelBot
from python.config import TELEGRAM_BOT_TOKEN, CHANNEL_ID
from python.advanced_etf_table_generator import AdvancedETFTableGenerator

async def main():
    print("=" * 50)
    print("Chart and ETF table sending started")
    print("=" * 50)

    # 텔레그램 봇 초기화
    bot = NewsChannelBot(TELEGRAM_BOT_TOKEN, CHANNEL_ID)

    # 연결 확인
    if not await bot.check_connection():
        print("[FAIL] Bot connection failed!")
        return

    # 1. 3배 ETF만 발송 (지수 제거)
    print("\n[1] Creating 3X ETF message...")
    etf_tracker = ETFTracker()
    etf_data = etf_tracker.get_all_etf_data()

    if etf_data:
        print(f"  - {len(etf_data)} ETFs collected")
    else:
        print("[WARN] ETF data collection failed")

    etf_msg = AdvancedETFTableGenerator.create_etf_message(etf_data)

    if etf_msg:
        success = await bot.send_news(etf_msg)
        if success:
            print("[OK] 3X ETF message sent")
        else:
            print("[FAIL] 3X ETF message failed")
    else:
        print("[FAIL] 3X ETF message generation failed")

    print("\n" + "=" * 50)
    print("Sending complete!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
