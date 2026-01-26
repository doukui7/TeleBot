"""
테스트 발송 스크립트
"""
import asyncio
import sys
import os

# 인코딩 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# src 디렉토리를 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.telegram_bot import NewsChannelBot
from src.etf_tracker import ETFTracker
from src.config import TELEGRAM_BOT_TOKEN, CHANNEL_ID

async def test_send():
    """테스트 메시지 발송"""
    
    # 봇 초기화
    bot = NewsChannelBot(TELEGRAM_BOT_TOKEN, CHANNEL_ID)
    
    print("=" * 50)
    print("텔레그램 봇 ETF 테스트 발송")
    print("=" * 50)
    
    # 1. 봇 연결 확인
    print("\n[1] 봇 연결 확인 중...")
    if await bot.check_connection():
        print("[OK] 봇 연결 성공!")
    else:
        print("[ERROR] 봇 연결 실패!")
        return
    
    # 2. ETF 데이터 수집 (상위 10개)
    print("\n[2] ETF 데이터 수집 중...")
    tracker = ETFTracker(etf_list=[
        "TQQQ", "SPXL", "UPRO", "TECL", "SOXL",
        "FAS", "URTY", "TNA", "LABU", "NAIL"
    ])
    
    etf_data = tracker.get_all_etf_data()
    
    if etf_data:
        print(f"[OK] {len(etf_data)}개 ETF 데이터 수집 성공!")
        
        # 3. ETF 리포트 생성 및 발송
        print("\n[3] ETF 리포트 생성 및 발송 중...")
        etf_report = tracker.format_etf_report(etf_data)
        
        if await bot.send_news(etf_report):
            print("[OK] ETF 리포트 발송 성공!")
            print("\n[ETF Report]")
            print(etf_report)
        else:
            print("[ERROR] ETF 리포트 발송 실패!")
    else:
        print("[ERROR] ETF 데이터 수집 실패!")
        print("수동으로 테스트 메시지 발송...")
        
        # 수동 테스트 메시지
        test_message = """[TEST] 3배 레버리지 ETF 일일 리포트

테스트 메시지입니다.
데이터 수집에 문제가 발생했습니다.

수동 메시지 발송 테스트"""
        
        if await bot.send_news(test_message):
            print("[OK] 테스트 메시지 발송 성공!")
    
    print("\n" + "=" * 50)
    print("테스트 완료!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_send())
