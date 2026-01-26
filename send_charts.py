"""
차트와 ETF 테이블 이미지 발송 스크립트
"""
import asyncio
import sys
import os

# src 디렉토리 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.market_chart_generator import MarketChartGenerator
from src.etf_table_generator import ETFTableGenerator
from src.etf_tracker import ETFTracker
from src.telegram_bot import NewsChannelBot
from src.config import TELEGRAM_BOT_TOKEN, CHANNEL_ID

async def main():
    print("=" * 50)
    print("차트 및 ETF 테이블 발송 시작")
    print("=" * 50)

    # 텔레그램 봇 초기화
    bot = NewsChannelBot(TELEGRAM_BOT_TOKEN, CHANNEL_ID)

    # 연결 확인
    if not await bot.check_connection():
        print("봇 연결 실패!")
        return

    # 1. 시장 차트 생성 및 발송
    print("\n[1] 시장 차트 생성 중...")
    chart_gen = MarketChartGenerator()
    chart = chart_gen.create_market_chart()

    if chart:
        caption = "📊 시장 현황 차트 (1년)"
        success = await bot.send_photo_buffer(chart, caption)
        if success:
            print("✅ 시장 차트 발송 완료")
        else:
            print("❌ 시장 차트 발송 실패")
    else:
        print("❌ 시장 차트 생성 실패")

    # 2. ETF 테이블 생성 및 발송
    print("\n[2] ETF 테이블 생성 중...")
    etf_tracker = ETFTracker()
    etf_data = etf_tracker.get_all_etf_data()

    if etf_data:
        print(f"  - {len(etf_data)}개 ETF 데이터 수집 완료")

        table_img = ETFTableGenerator.create_table_image(etf_data)

        if table_img:
            caption = "📋 3X ETF 리스트"
            success = await bot.send_photo_buffer(table_img, caption)
            if success:
                print("✅ ETF 테이블 발송 완료")
            else:
                print("❌ ETF 테이블 발송 실패")
        else:
            print("❌ ETF 테이블 이미지 생성 실패")
    else:
        print("❌ ETF 데이터 수집 실패")

    print("\n" + "=" * 50)
    print("발송 완료!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
