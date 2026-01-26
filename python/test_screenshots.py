"""
스크린샷 기능 테스트 스크립트
CNN Fear & Greed Index + 네이버 세계 증시
"""
import asyncio
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(__file__))

from fear_greed_tracker import FearGreedTracker, NaverFinanceTracker


async def test_screenshots():
    """스크린샷 기능 테스트"""
    print("=" * 50)
    print("스크린샷 테스트 시작")
    print("=" * 50)

    # 1. Fear & Greed Index 테스트
    print("\n[1] CNN Fear & Greed Index 테스트...")
    fg_tracker = FearGreedTracker()

    # API 데이터 먼저 테스트
    data = fg_tracker.fetch_fear_greed_data()
    if data:
        print(f"  ✅ API 데이터: 점수 {data['score']}, 등급 {data['rating']}")
    else:
        print("  ❌ API 데이터 가져오기 실패")

    # 스크린샷 캡처 테스트
    try:
        screenshot = await fg_tracker.capture_fear_greed_screenshot()
        if screenshot:
            # 파일로 저장
            with open("test_fear_greed.png", "wb") as f:
                f.write(screenshot.getvalue())
            print("  ✅ Fear & Greed 스크린샷 저장: test_fear_greed.png")
        else:
            print("  ⚠️ 스크린샷 실패 (폴백 차트 생성됨)")
    except Exception as e:
        print(f"  ❌ 스크린샷 오류: {e}")
        print("  💡 Playwright 설치 필요: pip install playwright && playwright install chromium")

    # 2. 네이버 세계 증시 테스트
    print("\n[2] 네이버 세계 증시 테스트...")
    naver_tracker = NaverFinanceTracker()

    # API 데이터 먼저 테스트
    market_data = naver_tracker.fetch_us_market_data()
    if market_data:
        print(f"  ✅ API 데이터: {len(market_data)}개 지수")
        for item in market_data[:3]:
            print(f"     - {item['name']}: {item['price']:,.2f} ({item['change_pct']:+.2f}%)")
    else:
        print("  ❌ API 데이터 가져오기 실패")

    # 스크린샷 캡처 테스트
    try:
        screenshot = await naver_tracker.capture_naver_world_screenshot()
        if screenshot:
            # 파일로 저장
            with open("test_naver_world.png", "wb") as f:
                f.write(screenshot.getvalue())
            print("  ✅ 네이버 증시 스크린샷 저장: test_naver_world.png")
        else:
            print("  ⚠️ 스크린샷 실패 (폴백 차트 생성됨)")
    except Exception as e:
        print(f"  ❌ 스크린샷 오류: {e}")
        print("  💡 Playwright 설치 필요: pip install playwright && playwright install chromium")

    print("\n" + "=" * 50)
    print("테스트 완료!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_screenshots())
