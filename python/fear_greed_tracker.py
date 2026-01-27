"""
CNN Fear & Greed Index 및 네이버 금융 데이터 트래커
- Playwright 스크린샷 방식만 사용
"""
import requests
import logging
from io import BytesIO
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class FearGreedTracker:
    """CNN Fear & Greed Index 트래커 (스크린샷 방식)"""

    def __init__(self):
        self.api_url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"

    def fetch_fear_greed_data(self):
        """Fear & Greed Index 데이터 가져오기 (텍스트 폴백용)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(self.api_url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            fear_greed = data.get('fear_and_greed', {})
            current_score = fear_greed.get('score', 50)
            current_rating = fear_greed.get('rating', 'Neutral')

            return {
                'score': round(current_score),
                'rating': current_rating,
                'previous_close': round(fear_greed.get('previous_close', current_score)),
                'one_week_ago': round(fear_greed.get('previous_1_week', current_score)),
                'one_month_ago': round(fear_greed.get('previous_1_month', current_score)),
                'one_year_ago': round(fear_greed.get('previous_1_year', current_score)),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
        except Exception as e:
            logger.error(f"Fear & Greed 데이터 가져오기 실패: {e}")
            return None

    def get_rating_korean(self, rating):
        """영문 등급을 한글로 변환"""
        rating_lower = rating.lower() if rating else ''
        ratings = {
            'extreme fear': '극단적 공포',
            'fear': '공포',
            'neutral': '중립',
            'greed': '탐욕',
            'extreme greed': '극단적 탐욕'
        }
        return ratings.get(rating_lower, rating)

    def format_text_message(self, data):
        """스크린샷 실패 시 텍스트 메시지 생성"""
        if not data:
            return None

        rating_kr = self.get_rating_korean(data['rating'])
        emoji = '😱' if data['score'] <= 25 else '😰' if data['score'] <= 45 else '😐' if data['score'] <= 55 else '😏' if data['score'] <= 75 else '🤑'

        msg = f"{emoji} <b>Fear & Greed Index</b>\n\n"
        msg += f"📊 현재: <b>{data['score']}</b> ({rating_kr})\n\n"
        msg += f"📈 이전 종가: {data['previous_close']}\n"
        msg += f"📅 1주 전: {data['one_week_ago']}\n"
        msg += f"📅 1달 전: {data['one_month_ago']}\n"
        msg += f"📅 1년 전: {data['one_year_ago']}\n"
        msg += f"\n🕐 {data['timestamp']}"

        return msg

    async def capture_fear_greed_screenshot(self):
        """CNN Fear & Greed 페이지 스크린샷 캡처"""
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                # 클라우드 환경(Render)용 브라우저 설정
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-blink-features=AutomationControlled',
                    ]
                )

                context = await browser.new_context(
                    viewport={'width': 1400, 'height': 1200},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = await context.new_page()

                await page.goto('https://edition.cnn.com/markets/fear-and-greed',
                              wait_until='networkidle', timeout=60000)

                # 페이지 로딩 대기
                await asyncio.sleep(8)

                # Fear & Greed 게이지 + 히스토리 영역 캡처
                screenshot_bytes = await page.screenshot(
                    clip={'x': 20, 'y': 480, 'width': 1020, 'height': 620}
                )

                await browser.close()

                buf = BytesIO(screenshot_bytes)
                buf.seek(0)
                logger.info("Fear & Greed 스크린샷 캡처 완료")
                return buf

        except Exception as e:
            logger.error(f"Fear & Greed 스크린샷 캡처 실패: {e}")
            return None


class NaverFinanceTracker:
    """네이버 금융 데이터 트래커 (스크린샷 방식)"""

    def __init__(self):
        self.indices = [
            ('%5EDJI', '다우존스'),
            ('%5EIXIC', '나스닥 종합'),
            ('%5EGSPC', 'S&P 500'),
            ('%5ESOX', '필라델피아 반도체'),
            ('%5ENDX', '나스닥 100'),
        ]
        self._headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def fetch_us_market_data(self):
        """미국 시장 데이터 가져오기 (텍스트 폴백용)"""
        results = []

        for symbol, name in self.indices:
            try:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                params = {"interval": "1d", "range": "5d"}

                response = requests.get(url, params=params, headers=self._headers, timeout=10)

                if response.status_code != 200:
                    continue

                data = response.json()
                result = data.get("chart", {}).get("result", [])

                if not result:
                    continue

                meta = result[0].get("meta", {})
                quotes = result[0].get("indicators", {}).get("quote", [{}])[0]
                closes = quotes.get("close", [])

                valid_closes = [c for c in closes if c is not None]

                if len(valid_closes) >= 2:
                    price = valid_closes[-1]
                    prev_close = valid_closes[-2]
                elif len(valid_closes) == 1:
                    price = valid_closes[-1]
                    prev_close = meta.get("chartPreviousClose", price)
                else:
                    continue

                change = price - prev_close
                change_pct = (change / prev_close) * 100 if prev_close != 0 else 0

                results.append({
                    'name': name,
                    'price': price,
                    'change': change,
                    'change_pct': change_pct
                })

            except Exception as e:
                logger.warning(f"{name} 데이터 가져오기 실패: {e}")

        return results

    def format_text_message(self, data):
        """스크린샷 실패 시 텍스트 메시지 생성"""
        if not data:
            return None

        msg = "🌍 <b>세계 증시 현황</b>\n\n"

        for item in data:
            arrow = '🔺' if item['change'] >= 0 else '🔻'
            color_sign = '+' if item['change'] >= 0 else ''
            msg += f"{arrow} <b>{item['name']}</b>\n"
            msg += f"   {item['price']:,.2f} ({color_sign}{item['change_pct']:.2f}%)\n\n"

        msg += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        return msg

    async def capture_naver_world_screenshot(self):
        """네이버 금융 세계 증시 페이지 스크린샷 캡처 (deprecated - use capture_naver_us_market_screenshot)"""
        return await self.capture_naver_us_market_screenshot()

    async def capture_naver_us_market_screenshot(self):
        """네이버 증권 미국 시장 스크린샷 캡처 (stock.naver.com)"""
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                # 클라우드 환경(Render)용 브라우저 설정
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                    ]
                )

                context = await browser.new_context(
                    viewport={'width': 1400, 'height': 900},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = await context.new_page()

                # 네이버 증권 미국 시장 URL
                await page.goto('https://stock.naver.com/market/stock/usa',
                              wait_until='networkidle', timeout=60000)

                await asyncio.sleep(5)

                # 다우존스, 나스닥, S&P 500 영역만 캡처 (상단 탭 포함)
                screenshot_bytes = await page.screenshot(
                    clip={'x': 150, 'y': 120, 'width': 880, 'height': 350}
                )

                await browser.close()

                buf = BytesIO(screenshot_bytes)
                buf.seek(0)
                logger.info("네이버 미국 증시 스크린샷 캡처 완료")
                return buf

        except Exception as e:
            logger.error(f"네이버 미국 증시 스크린샷 캡처 실패: {e}")
            return None

    async def capture_naver_kr_market_screenshot(self):
        """네이버 증권 한국 시장 스크린샷 캡처 (stock.naver.com)"""
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                # 클라우드 환경(Render)용 브라우저 설정
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                    ]
                )

                context = await browser.new_context(
                    viewport={'width': 1400, 'height': 900},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = await context.new_page()

                # 네이버 증권 한국 시장 URL
                await page.goto('https://stock.naver.com/market/stock/kr',
                              wait_until='networkidle', timeout=60000)

                await asyncio.sleep(5)

                # KOSPI, KOSDAQ 영역만 캡처 (우측 잘린 차트 제거)
                screenshot_bytes = await page.screenshot(
                    clip={'x': 150, 'y': 120, 'width': 780, 'height': 350}
                )

                await browser.close()

                buf = BytesIO(screenshot_bytes)
                buf.seek(0)
                logger.info("네이버 한국 증시 스크린샷 캡처 완료")
                return buf

        except Exception as e:
            logger.error(f"네이버 한국 증시 스크린샷 캡처 실패: {e}")
            return None
