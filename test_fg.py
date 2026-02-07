"""CNN Fear & Greed 스크린샷 테스트"""
import asyncio
from playwright.async_api import async_playwright

async def test_capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # headless=False로 브라우저 표시

        context = await browser.new_context(
            viewport={'width': 1400, 'height': 1200},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        print("페이지 로딩 중...")
        await page.goto('https://edition.cnn.com/markets/fear-and-greed',
                       wait_until='networkidle', timeout=60000)

        await asyncio.sleep(3)

        # OneTrust 팝업만 숨김
        await page.add_style_tag(content='''
            #onetrust-consent-sdk,
            #onetrust-banner-sdk,
            .onetrust-pc-dark-filter,
            [class*="onetrust"] {
                display: none !important;
            }
            body {
                overflow: auto !important;
            }
        ''')
        print("OneTrust 팝업 숨김 적용")

        await asyncio.sleep(1)

        # 스크린샷
        await page.screenshot(
            path='test_fg_css.png',
            clip={'x': 20, 'y': 480, 'width': 1020, 'height': 620}
        )
        print("스크린샷 저장: test_fg_css.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_capture())
