"""
실제 ETF 주가 데이터 조회 및 발송
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
import io

# 인코딩 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# src 디렉토리를 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.telegram_bot import NewsChannelBot
from src.config import TELEGRAM_BOT_TOKEN, CHANNEL_ID
from src.etf_table_generator import ETFTableGenerator

try:
    import yfinance as yf
except ImportError:
    print("yfinance 설치 필요: pip install yfinance")


async def get_real_etf_data():
    """실제 ETF 데이터 조회"""
    
    etf_symbols = [
        "TQQQ", "SPXL", "UPRO", "TECL", "SOXL", "FNGU", "TMF", "FAS",
        "TNA", "UDOW", "DPST", "LABU", "URTY", "NAIL", "DFEN", "CURE",
        "KORU", "MIDU", "EDC", "DRN", "TYD", "RETL", "UTSL", "OILU",
        "UMDD", "DUSL", "MEXX", "TPOR", "EURL", "PILL"
    ]
    
    etf_data = []
    
    print("\n[+] ETF 실시간 데이터 조회 중...")
    
    for symbol in etf_symbols:
        try:
            ticker = yf.Ticker(symbol)
            
            # 1년 데이터 조회
            hist = ticker.history(period="1y")
            
            if hist.empty:
                print(f"  [-] {symbol}: 데이터 없음")
                continue
            
            # 현재가 및 이전 종가
            current_price = hist['Close'].iloc[-1]
            previous_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            
            # 52주 신고가
            high_52w = hist['High'].max()
            high_52w_date = hist['High'].idxmax().strftime("%Y-%m-%d")
            
            # DD (현재 하락률)
            dd = ((current_price - high_52w) / high_52w) * 100 if high_52w > 0 else 0
            
            # 연초 대비 수익률
            year_start = datetime.now().replace(month=1, day=1)
            year_start_data = hist.loc[hist.index >= year_start]
            year_start_price = year_start_data.iloc[0]['Close'] if len(year_start_data) > 0 else hist['Close'].iloc[0]
            ytd_return = ((current_price - year_start_price) / year_start_price) * 100 if year_start_price > 0 else 0
            
            # 전일 변동률
            daily_change = ((current_price - previous_close) / previous_close) * 100 if previous_close > 0 else 0
            
            data = {
                "symbol": symbol,
                "current_price": round(float(current_price), 2),
                "high_52w": round(float(high_52w), 2),
                "high_52w_date": high_52w_date,
                "dd": round(float(dd), 2),
                "ytd_return": round(float(ytd_return), 2),
                "daily_change": round(float(daily_change), 2),
            }
            
            etf_data.append(data)
            print(f"  [OK] {symbol}: ${current_price:.2f} (변동: {daily_change:+.2f}%)")
            
        except Exception as e:
            print(f"  [ERROR] {symbol}: {str(e)[:50]}")
            continue
    
    return etf_data


async def main():
    """메인 함수"""
    
    bot = NewsChannelBot(TELEGRAM_BOT_TOKEN, CHANNEL_ID)
    
    print("=" * 50)
    print("3X ETF LIST - 실제 데이터 발송")
    print("=" * 50)
    
    # 1. 봇 연결 확인
    print("\n[1] 봇 연결 확인 중...")
    if not await bot.check_connection():
        print("[ERROR] 봇 연결 실패!")
        return
    print("[OK] 봇 연결 성공!")
    
    # 2. 실제 데이터 조회
    etf_data = await get_real_etf_data()
    
    if not etf_data:
        print("[ERROR] ETF 데이터 조회 실패!")
        return
    
    print(f"\n[OK] {len(etf_data)}개 ETF 데이터 조회 성공!")
    
    # 3. 테이블 이미지 생성
    print("\n[2] 테이블 이미지 생성 중...")
    table_gen = ETFTableGenerator()
    img_buffer = table_gen.create_table_image(etf_data)
    
    if not img_buffer:
        print("[ERROR] 테이블 이미지 생성 실패!")
        return
    
    print("[OK] 테이블 이미지 생성 성공!")
    
    # 4. 이미지 발송
    print("\n[3] 테이블 이미지 발송 중...")
    img_data = img_buffer.getvalue()
    
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
        return
    
    # 5. 상세 정보 발송
    print("\n[4] 상세 정보 발송 중...")
    
    message = "3X ETF LIST - Detailed Report\n\n"
    message += "<code>"
    for etf in sorted(etf_data, key=lambda x: x['daily_change'], reverse=True)[:10]:
        message += f"{etf['symbol']:6} | Current: ${etf['current_price']:8.2f} | High: ${etf['high_52w']:8.2f} ({etf['high_52w_date']}) | DD: {etf['dd']:7.2f}% | Daily: {etf['daily_change']:+7.2f}%\n"
    message += "</code>"
    
    if await bot.send_news(message):
        print("[OK] 상세 정보 발송 성공!")
    else:
        print("[ERROR] 상세 정보 발송 실패!")
    
    print("\n" + "=" * 50)
    print("발송 완료!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
