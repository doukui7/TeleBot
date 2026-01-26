"""
IG Weekend US Tech 100 트래커
- 주말 나스닥 합성 지수 조회
- 스크린샷 캡처 및 가격 알림
"""
import logging
import asyncio
import re
from io import BytesIO
from datetime import datetime

logger = logging.getLogger(__name__)


class WeekendNasdaqTracker:
    """IG Weekend US Tech 100 트래커"""

    def __init__(self):
        self.url = "https://www.ig.com/en/indices/markets-indices/weekend-us-tech-100-e1"
        self.last_price = None
        self.friday_close = None  # 금요일 종가 (기준점)

    async def capture_screenshot(self):
        """IG Weekend US Tech 100 우측 패널 스크린샷 캡처"""
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(viewport={'width': 1400, 'height': 900})

                await page.goto(self.url, wait_until='domcontentloaded', timeout=60000)

                # 페이지 로딩 대기 (차트 및 가격 데이터)
                await asyncio.sleep(5)

                # 쿠키 동의 버튼 클릭 (있으면)
                try:
                    agree_btn = page.locator('button:has-text("Agree")')
                    if await agree_btn.count() > 0:
                        await agree_btn.click()
                        await asyncio.sleep(1)
                except:
                    pass

                # 우측 패널 캡처 (SELL/BUY 가격, 변동, 센티먼트)
                # 대략적인 좌표: x=920, y=280, width=320, height=400
                screenshot_bytes = await page.screenshot(
                    clip={'x': 920, 'y': 280, 'width': 320, 'height': 400}
                )

                await browser.close()

                buf = BytesIO(screenshot_bytes)
                buf.seek(0)
                logger.info("Weekend Nasdaq 스크린샷 캡처 완료")
                return buf

        except Exception as e:
            logger.error(f"Weekend Nasdaq 스크린샷 캡처 실패: {e}")
            return None

    async def fetch_price_data(self):
        """IG 페이지에서 가격 데이터 스크래핑"""
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(viewport={'width': 1400, 'height': 900})

                await page.goto(self.url, wait_until='domcontentloaded', timeout=60000)
                await asyncio.sleep(5)

                # 쿠키 동의
                try:
                    agree_btn = page.locator('button:has-text("Agree")')
                    if await agree_btn.count() > 0:
                        await agree_btn.click()
                        await asyncio.sleep(1)
                except:
                    pass

                # 가격 정보 추출
                content = await page.content()

                # SELL 가격 추출
                sell_match = re.search(r'SELL[^0-9]*(\d{4,5}\.?\d*)', content)
                # BUY 가격 추출
                buy_match = re.search(r'BUY[^0-9]*(\d{4,5}\.?\d*)', content)
                # 변동 추출 (-56.7 형태)
                change_match = re.search(r'([+-]?\d+\.?\d*)\s*\(\s*([+-]?\d+\.?\d*)%\s*\)', content)

                await browser.close()

                sell_price = float(sell_match.group(1)) if sell_match else None
                buy_price = float(buy_match.group(1)) if buy_match else None

                if change_match:
                    change = float(change_match.group(1))
                    change_pct = float(change_match.group(2))
                else:
                    change = None
                    change_pct = None

                mid_price = (sell_price + buy_price) / 2 if sell_price and buy_price else None

                data = {
                    'sell': sell_price,
                    'buy': buy_price,
                    'mid': mid_price,
                    'change': change,
                    'change_pct': change_pct,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                }

                logger.info(f"Weekend Nasdaq 가격 조회: {data}")
                return data

        except Exception as e:
            logger.error(f"Weekend Nasdaq 가격 조회 실패: {e}")
            return None

    def format_text_message(self, data):
        """텍스트 메시지 생성"""
        if not data:
            return None

        msg = "📊 <b>Weekend US Tech 100</b>\n\n"

        if data.get('sell') and data.get('buy'):
            msg += f"🔴 SELL: {data['sell']:,.1f}\n"
            msg += f"🟢 BUY: {data['buy']:,.1f}\n\n"

        if data.get('change') is not None and data.get('change_pct') is not None:
            emoji = '📈' if data['change'] >= 0 else '📉'
            color = '+' if data['change'] >= 0 else ''
            msg += f"{emoji} 변동: <b>{color}{data['change']:,.1f}</b> ({color}{data['change_pct']:.2f}%)\n"

        msg += f"\n🕐 {data['timestamp']}"
        msg += "\n\n<i>IG Weekend Trading</i>"

        return msg

    def should_alert(self, data, threshold=1.0):
        """
        알림 조건 확인
        - 변동률이 threshold% 이상이면 알림
        """
        if not data or data.get('change_pct') is None:
            return False

        return abs(data['change_pct']) >= threshold

    def format_alert_message(self, data):
        """알림 메시지 생성"""
        if not data:
            return None

        change_pct = data.get('change_pct', 0)
        emoji = '🚨📈' if change_pct >= 0 else '🚨📉'
        direction = '상승' if change_pct >= 0 else '하락'

        msg = f"{emoji} <b>Weekend Nasdaq {direction} 알림!</b>\n\n"
        msg += f"📊 US Tech 100: {data.get('mid', 0):,.1f}\n"
        msg += f"📈 변동: {data.get('change', 0):+,.1f} ({change_pct:+.2f}%)\n"
        msg += f"\n🕐 {data['timestamp']}"

        return msg
