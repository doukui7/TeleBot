"""Screenshot capture test"""
import asyncio
import sys
sys.path.insert(0, 'src')

from fear_greed_tracker import FearGreedTracker, NaverFinanceTracker

async def test_screenshots():
    # CNN Fear & Greed screenshot test
    print("Capturing CNN Fear & Greed screenshot...")
    fg_tracker = FearGreedTracker()
    fg_screenshot = await fg_tracker.capture_fear_greed_screenshot()
    if fg_screenshot:
        with open('fear_greed_screenshot.png', 'wb') as f:
            f.write(fg_screenshot.read())
        print("[OK] fear_greed_screenshot.png saved")
    else:
        print("[FAIL] Fear & Greed screenshot failed")

    # Naver Finance screenshot test
    print("\nCapturing Naver Finance world screenshot...")
    naver_tracker = NaverFinanceTracker()
    naver_screenshot = await naver_tracker.capture_naver_world_screenshot()
    if naver_screenshot:
        with open('naver_world_screenshot.png', 'wb') as f:
            f.write(naver_screenshot.read())
        print("[OK] naver_world_screenshot.png saved")
    else:
        print("[FAIL] Naver Finance screenshot failed")

if __name__ == '__main__':
    asyncio.run(test_screenshots())
