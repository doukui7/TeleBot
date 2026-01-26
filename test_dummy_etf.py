"""
더미 ETF 테스트 발송 스크립트
"""
import asyncio
import sys
import os
from datetime import datetime
import io

# 인코딩 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# src 디렉토리를 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.telegram_bot import NewsChannelBot
from src.config import TELEGRAM_BOT_TOKEN, CHANNEL_ID
from src.etf_table_generator import ETFTableGenerator

async def test_send_dummy_etf():
    """더미 ETF 데이터로 테스트 발송"""
    
    # 봇 초기화
    bot = NewsChannelBot(TELEGRAM_BOT_TOKEN, CHANNEL_ID)
    
    print("=" * 50)
    print("텔레그램 봇 ETF 테스트 발송 (더미 데이터)")
    print("=" * 50)
    
    # 1. 봇 연결 확인
    print("\n[1] 봇 연결 확인 중...")
    if await bot.check_connection():
        print("[OK] 봇 연결 성공!")
    else:
        print("[ERROR] 봇 연결 실패!")
        return
    
    # 2. 더미 ETF 데이터 생성
    print("\n[2] 테스트 ETF 리포트 생성 중...")
    
    dummy_etf_data = [
        {"symbol": "TQQQ", "current_price": 47.89, "high_52w": 52.45, "high_52w_date": "2025-12-15", "dd": -8.69, "ytd_return": 12.34, "daily_change": 2.15},
        {"symbol": "SPXL", "current_price": 89.23, "high_52w": 94.67, "high_52w_date": "2025-11-28", "dd": -5.68, "ytd_return": 9.87, "daily_change": 1.23},
        {"symbol": "UPRO", "current_price": 68.45, "high_52w": 72.34, "high_52w_date": "2025-12-20", "dd": -5.38, "ytd_return": 10.45, "daily_change": 1.56},
        {"symbol": "TECL", "current_price": 34.67, "high_52w": 38.92, "high_52w_date": "2025-12-10", "dd": -10.92, "ytd_return": 15.67, "daily_change": 2.34},
        {"symbol": "SOXL", "current_price": 42.15, "high_52w": 47.89, "high_52w_date": "2025-12-22", "dd": -12.01, "ytd_return": 18.90, "daily_change": 3.21},
        {"symbol": "FNGU", "current_price": 31.45, "high_52w": 35.67, "high_52w_date": "2025-12-18", "dd": -11.84, "ytd_return": 14.56, "daily_change": 2.45},
        {"symbol": "TMF", "current_price": 28.92, "high_52w": 31.23, "high_52w_date": "2025-11-30", "dd": -7.41, "ytd_return": 5.23, "daily_change": 1.87},
        {"symbol": "FAS", "current_price": 45.78, "high_52w": 51.34, "high_52w_date": "2025-12-12", "dd": -10.84, "ytd_return": 16.78, "daily_change": 2.78},
        {"symbol": "TNA", "current_price": 38.56, "high_52w": 42.89, "high_52w_date": "2025-12-08", "dd": -10.10, "ytd_return": 13.45, "daily_change": 2.12},
        {"symbol": "UDOW", "current_price": 52.34, "high_52w": 56.78, "high_52w_date": "2025-12-19", "dd": -7.81, "ytd_return": 8.67, "daily_change": 1.34},
        {"symbol": "DPST", "current_price": 25.67, "high_52w": 28.91, "high_52w_date": "2025-12-15", "dd": -11.20, "ytd_return": 17.34, "daily_change": 2.56},
        {"symbol": "LABU", "current_price": 33.45, "high_52w": 37.89, "high_52w_date": "2025-12-10", "dd": -11.73, "ytd_return": 19.12, "daily_change": 3.45},
        {"symbol": "URTY", "current_price": 41.23, "high_52w": 45.67, "high_52w_date": "2025-12-22", "dd": -9.73, "ytd_return": 12.78, "daily_change": 2.34},
        {"symbol": "NAIL", "current_price": 29.78, "high_52w": 33.45, "high_52w_date": "2025-12-20", "dd": -10.97, "ytd_return": 20.34, "daily_change": 2.89},
        {"symbol": "DFEN", "current_price": 44.56, "high_52w": 48.34, "high_52w_date": "2025-12-15", "dd": -7.82, "ytd_return": 14.56, "daily_change": 2.01},
        {"symbol": "CURE", "current_price": 27.34, "high_52w": 30.67, "high_52w_date": "2025-12-12", "dd": -10.86, "ytd_return": 13.89, "daily_change": 1.67},
        {"symbol": "KORU", "current_price": 35.67, "high_52w": 39.23, "high_52w_date": "2025-12-22", "dd": -9.08, "ytd_return": 15.67, "daily_change": 2.34},
        {"symbol": "MIDU", "current_price": 42.89, "high_52w": 47.12, "high_52w_date": "2025-12-15", "dd": -9.00, "ytd_return": 11.89, "daily_change": 1.89},
        {"symbol": "EDC", "current_price": 38.23, "high_52w": 42.34, "high_52w_date": "2025-12-18", "dd": -9.70, "ytd_return": 16.78, "daily_change": 2.56},
        {"symbol": "DRN", "current_price": 31.45, "high_52w": 34.67, "high_52w_date": "2025-12-20", "dd": -9.29, "ytd_return": 12.45, "daily_change": 1.78},
        {"symbol": "TYD", "current_price": 24.67, "high_52w": 27.34, "high_52w_date": "2025-12-08", "dd": -9.78, "ytd_return": 4.56, "daily_change": 0.89},
        {"symbol": "RETL", "current_price": 33.89, "high_52w": 37.56, "high_52w_date": "2025-12-15", "dd": -9.78, "ytd_return": 17.89, "daily_change": 2.67},
        {"symbol": "UTSL", "current_price": 41.23, "high_52w": 45.34, "high_52w_date": "2025-12-12", "dd": -9.08, "ytd_return": 13.45, "daily_change": 1.56},
        {"symbol": "OILU", "current_price": 35.67, "high_52w": 39.45, "high_52w_date": "2025-12-20", "dd": -9.58, "ytd_return": 14.23, "daily_change": 2.12},
        {"symbol": "UMDD", "current_price": 47.89, "high_52w": 52.34, "high_52w_date": "2025-12-15", "dd": -8.51, "ytd_return": 12.67, "daily_change": 1.89},
        {"symbol": "DUSL", "current_price": 38.45, "high_52w": 42.12, "high_52w_date": "2025-12-18", "dd": -8.71, "ytd_return": 13.56, "daily_change": 2.34},
        {"symbol": "MEXX", "current_price": 24.56, "high_52w": 27.34, "high_52w_date": "2025-12-20", "dd": -10.17, "ytd_return": 8.45, "daily_change": 1.23},
        {"symbol": "TPOR", "current_price": 40.78, "high_52w": 44.56, "high_52w_date": "2025-12-15", "dd": -8.48, "ytd_return": 15.67, "daily_change": 2.45},
        {"symbol": "EURL", "current_price": 35.23, "high_52w": 39.12, "high_52w_date": "2025-12-12", "dd": -9.92, "ytd_return": 11.23, "daily_change": 1.67},
        {"symbol": "PILL", "current_price": 32.45, "high_52w": 36.78, "high_52w_date": "2025-12-18", "dd": -11.78, "ytd_return": 14.89, "daily_change": 2.34},
    ]
    
    # ETF 리포트 포맷 (테이블 형식)
    message = "📊 <b>3배 레버리지 ETF 일일 리포트</b>\n"
    message += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # 테이블 헤더
    message += "<code>"
    message += "┌─────────┬────────────┬──────────┬──────────┬──────────┐\n"
    message += "│ ETF    │ 현재가     │ 52주高   │   DD(%) │ 전일(%) │\n"
    message += "├─────────┼────────────┼──────────┼──────────┼──────────┤\n"
    
    for etf in dummy_etf_data:
        symbol = etf['symbol']
        current = f"${etf['current_price']:.2f}"
        high52 = f"${etf['high_52w']:.2f}"
        dd = f"{etf['dd']:>6.2f}"
        daily = f"{etf['daily_change']:>+7.2f}"
        
        message += f"│ {symbol:<6} │ {current:>10} │ {high52:>8} │ {dd:>8} │ {daily:>8} │\n"
    
    message += "└─────────┴────────────┴──────────┴──────────┴──────────┘\n"
    message += "</code>\n\n"
    
    # 상세 정보
    message += "<b>상세 정보:</b>\n"
    for etf in dummy_etf_data:
        symbol = etf['symbol']
        high_52w_date = etf['high_52w_date']
        ytd_return = etf['ytd_return']
        
        message += f"• {symbol}: 52주高 {high_52w_date} | 연초대비 {ytd_return:+.2f}%\n"
    
    # 3. 메시지 발송
    print("\n[3] ETF 리포트 발송 중...")
    if await bot.send_news(message):
        print("[OK] ETF 리포트 발송 성공!")
        print("\n[발송 내용]")
        print(message)
    else:
        print("[ERROR] ETF 리포트 발송 실패!")
    
    # 4. 테이블 이미지 생성 및 발송
    print("\n[4] ETF 테이블 이미지 생성 중...")
    table_gen = ETFTableGenerator()
    img_buffer = table_gen.create_table_image(dummy_etf_data)
    
    if img_buffer:
        print("[OK] 테이블 이미지 생성 성공!")
        
        # 이미지 바이트로 변환
        img_data = img_buffer.getvalue()
        
        print("\n[5] 테이블 이미지 발송 중...")
        # 채널에 이미지 발송
        try:
            await bot.bot.send_photo(
                chat_id=bot.channel_id,
                photo=io.BytesIO(img_data),
                caption="3X ETF LIST - Daily Report",
                parse_mode="HTML"
            )
            print("[OK] 테이블 이미지 발송 성공!")
        except Exception as e:
            print(f"[ERROR] 테이블 이미지 발송 실패: {e}")
    else:
        print("[ERROR] 테이블 이미지 생성 실패!")
    
    print("\n" + "=" * 50)
    print("테스트 완료!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_send_dummy_etf())
