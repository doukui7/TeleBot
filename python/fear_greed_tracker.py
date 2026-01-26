"""
CNN Fear & Greed Index 및 네이버 금융 데이터 트래커
"""
import requests
import logging
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.font_manager as fm
import numpy as np
from datetime import datetime
import platform
import asyncio

logger = logging.getLogger(__name__)

# 한글 폰트 설정
def setup_korean_font():
    """한글 폰트 설정"""
    system = platform.system()
    if system == 'Windows':
        font_path = 'C:/Windows/Fonts/malgun.ttf'
        try:
            fm.fontManager.addfont(font_path)
            plt.rcParams['font.family'] = 'Malgun Gothic'
        except:
            plt.rcParams['font.family'] = 'sans-serif'
    elif system == 'Darwin':  # macOS
        plt.rcParams['font.family'] = 'AppleGothic'
    else:  # Linux
        plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.unicode_minus'] = False

setup_korean_font()


class FearGreedTracker:
    """CNN Fear & Greed Index 트래커"""

    def __init__(self):
        self.api_url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"

    def fetch_fear_greed_data(self):
        """Fear & Greed Index 데이터 가져오기"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(self.api_url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            # 현재 지수
            fear_greed = data.get('fear_and_greed', {})
            current_score = fear_greed.get('score', 50)
            current_rating = fear_greed.get('rating', 'Neutral')

            # 이전 데이터
            previous_close = fear_greed.get('previous_close', current_score)
            one_week_ago = fear_greed.get('previous_1_week', current_score)
            one_month_ago = fear_greed.get('previous_1_month', current_score)
            one_year_ago = fear_greed.get('previous_1_year', current_score)

            return {
                'score': round(current_score),
                'rating': current_rating,
                'previous_close': round(previous_close),
                'one_week_ago': round(one_week_ago),
                'one_month_ago': round(one_month_ago),
                'one_year_ago': round(one_year_ago),
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

    def get_rating_korean_short(self, score):
        """점수에 따른 등급 반환 (짧은 버전)"""
        if score <= 25:
            return 'Extreme Fear'
        elif score <= 45:
            return 'Fear'
        elif score <= 55:
            return 'Neutral'
        elif score <= 75:
            return 'Greed'
        else:
            return 'Extreme Greed'

    def get_rating_color(self, score):
        """점수에 따른 색상 반환"""
        if score <= 25:
            return '#e74c3c'  # 빨강 (극단적 공포)
        elif score <= 45:
            return '#e67e22'  # 주황 (공포)
        elif score <= 55:
            return '#f1c40f'  # 노랑 (중립)
        elif score <= 75:
            return '#2ecc71'  # 초록 (탐욕)
        else:
            return '#27ae60'  # 진한 초록 (극단적 탐욕)

    def create_fear_greed_chart(self, data):
        """Fear & Greed 게이지 차트 생성 (CNN 스타일)"""
        if not data:
            return None

        try:
            fig, ax = plt.subplots(figsize=(8, 10), facecolor='white')
            ax.set_facecolor('white')

            score = data['score']
            rating = data['rating']

            # 게이지 중심점과 반지름
            cx, cy = 0.5, 0.55
            outer_r = 0.38
            inner_r = 0.28

            # 색상 구간 (CNN 스타일)
            segments = [
                (0, 25, '#c41e3a'),     # Extreme Fear - 빨강
                (25, 45, '#d35400'),    # Fear - 주황
                (45, 55, '#f4d03f'),    # Neutral - 노랑
                (55, 75, '#58d68d'),    # Greed - 연두
                (75, 100, '#27ae60')    # Extreme Greed - 초록
            ]

            # 게이지 배경 그리기
            for start, end, color in segments:
                start_angle = 180 - (start / 100) * 180
                end_angle = 180 - (end / 100) * 180
                wedge = patches.Wedge(
                    (cx, cy), outer_r,
                    end_angle, start_angle,
                    width=outer_r - inner_r,
                    facecolor=color,
                    transform=ax.transAxes
                )
                ax.add_patch(wedge)

            # 바늘 그리기
            needle_angle = np.radians(180 - (score / 100) * 180)
            needle_length = outer_r - 0.02
            needle_x = cx + needle_length * np.cos(needle_angle)
            needle_y = cy + needle_length * np.sin(needle_angle)

            # 바늘 (삼각형 모양)
            ax.plot([cx, needle_x], [cy, needle_y], color='#2c3e50', linewidth=4,
                   solid_capstyle='round', transform=ax.transAxes, zorder=10)
            # 중앙 원
            center_circle = plt.Circle((cx, cy), 0.04, color='#2c3e50',
                                       transform=ax.transAxes, zorder=11)
            ax.add_patch(center_circle)

            # 제목
            ax.text(0.5, 0.95, 'Fear & Greed Index', fontsize=28, fontweight='bold',
                   ha='center', va='center', color='#2c3e50', transform=ax.transAxes)

            # 점수 크게 표시
            ax.text(cx, cy - 0.08, str(score), fontsize=64, fontweight='bold',
                   ha='center', va='center', color='#2c3e50', transform=ax.transAxes)

            # 등급 레이블 (게이지 아래)
            rating_colors = {
                'extreme fear': '#c41e3a',
                'fear': '#d35400',
                'neutral': '#f4d03f',
                'greed': '#58d68d',
                'extreme greed': '#27ae60'
            }
            rating_lower = rating.lower()
            rating_color = rating_colors.get(rating_lower, '#2c3e50')
            rating_korean = self.get_rating_korean(rating)

            ax.text(cx, 0.08, rating_korean, fontsize=18, fontweight='bold',
                   ha='center', va='center', color=rating_color, transform=ax.transAxes)

            # 게이지 라벨
            ax.text(0.08, cy, 'EXTREME\nFEAR', fontsize=9, ha='center', va='center',
                   color='#c41e3a', fontweight='bold', transform=ax.transAxes)
            ax.text(0.24, cy + 0.28, 'FEAR', fontsize=9, ha='center', va='center',
                   color='#d35400', fontweight='bold', transform=ax.transAxes)
            ax.text(0.5, cy + 0.35, 'NEUTRAL', fontsize=9, ha='center', va='center',
                   color='#7f8c8d', fontweight='bold', transform=ax.transAxes)
            ax.text(0.76, cy + 0.28, 'GREED', fontsize=9, ha='center', va='center',
                   color='#58d68d', fontweight='bold', transform=ax.transAxes)
            ax.text(0.92, cy, 'EXTREME\nGREED', fontsize=9, ha='center', va='center',
                   color='#27ae60', fontweight='bold', transform=ax.transAxes)

            # 숫자 눈금
            for val in [0, 25, 50, 75, 100]:
                angle = np.radians(180 - (val / 100) * 180)
                label_r = outer_r + 0.06
                lx = cx + label_r * np.cos(angle)
                ly = cy + label_r * np.sin(angle)
                ax.text(lx, ly, str(val), fontsize=10, ha='center', va='center',
                       color='#7f8c8d', transform=ax.transAxes)

            # 히스토리 섹션 (하단)
            history_items = [
                ('Previous close', data['previous_close'], self.get_rating_korean_short(data['previous_close'])),
                ('1 week ago', data['one_week_ago'], self.get_rating_korean_short(data['one_week_ago'])),
                ('1 month ago', data['one_month_ago'], self.get_rating_korean_short(data['one_month_ago'])),
                ('1 year ago', data['one_year_ago'], self.get_rating_korean_short(data['one_year_ago'])),
            ]

            # 히스토리 박스
            box_y = -0.08
            for i, (label, value, rating_text) in enumerate(history_items):
                x_pos = 0.125 + i * 0.25
                # 라벨
                ax.text(x_pos, box_y + 0.04, label, fontsize=9, ha='center',
                       color='#7f8c8d', transform=ax.transAxes)
                # 등급
                ax.text(x_pos, box_y - 0.02, rating_text, fontsize=10, ha='center',
                       color='#2c3e50', fontweight='bold', transform=ax.transAxes)
                # 점수 (원 안에)
                circle_color = self.get_rating_color(value)
                score_circle = plt.Circle((x_pos + 0.08, box_y - 0.01), 0.025,
                                         facecolor=circle_color, edgecolor='none',
                                         transform=ax.transAxes)
                ax.add_patch(score_circle)
                ax.text(x_pos + 0.08, box_y - 0.01, str(value), fontsize=9,
                       ha='center', va='center', color='white', fontweight='bold',
                       transform=ax.transAxes)

            ax.set_xlim(0, 1)
            ax.set_ylim(-0.15, 1)
            ax.axis('off')

            plt.tight_layout()

            # 이미지를 바이트로 변환
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=150, facecolor='#1a1a2e',
                       bbox_inches='tight', pad_inches=0.2)
            buf.seek(0)
            plt.close(fig)

            logger.info("Fear & Greed 차트 생성 완료")
            return buf

        except Exception as e:
            logger.error(f"Fear & Greed 차트 생성 실패: {e}")
            return None

    async def capture_fear_greed_screenshot(self):
        """CNN Fear & Greed 페이지 스크린샷 캡처 (게이지 + 히스토리 포함)"""
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(viewport={'width': 1400, 'height': 1200})

                await page.goto('https://edition.cnn.com/markets/fear-and-greed',
                              wait_until='domcontentloaded', timeout=60000)

                # 페이지 로딩 대기
                await asyncio.sleep(5)

                # Fear & Greed 제목 + 게이지 + 히스토리 영역 캡처
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
            # 실패 시 기존 차트 생성 방식으로 폴백
            data = self.fetch_fear_greed_data()
            return self.create_fear_greed_chart(data)


class NaverFinanceTracker:
    """네이버 금융 데이터 트래커 (Yahoo Finance API 사용)"""

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
        """미국 시장 데이터 가져오기 (Yahoo Finance Chart API)"""
        results = []

        for symbol, name in self.indices:
            try:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                params = {"interval": "1d", "range": "5d"}

                response = requests.get(url, params=params, headers=self._headers, timeout=10)

                if response.status_code != 200:
                    logger.warning(f"{name}: API 응답 오류 ({response.status_code})")
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

    def create_market_chart(self, data):
        """미국 시장 현황 차트 생성"""
        if not data:
            return None

        try:
            fig, ax = plt.subplots(figsize=(10, 8), facecolor='#1a1a2e')
            ax.set_facecolor('#1a1a2e')

            # 제목
            ax.text(0.5, 0.95, '🇺🇸 미국 증시 현황', fontsize=24, fontweight='bold',
                   ha='center', va='center', color='white', transform=ax.transAxes)
            ax.text(0.5, 0.89, datetime.now().strftime('%Y-%m-%d %H:%M'), fontsize=12,
                   ha='center', va='center', color='#888888', transform=ax.transAxes)

            # 각 지수 표시
            y_positions = [0.75, 0.58, 0.41, 0.24, 0.07]

            for i, item in enumerate(data[:5]):
                y = y_positions[i] if i < len(y_positions) else 0.07

                name = item['name']
                price = item['price']
                change = item['change']
                change_pct = item['change_pct']

                # 색상 결정
                if change >= 0:
                    color = '#e74c3c'  # 빨강 (상승)
                    arrow = '▲'
                else:
                    color = '#3498db'  # 파랑 (하락)
                    arrow = '▼'

                # 지수명
                ax.text(0.08, y, name, fontsize=16, fontweight='bold',
                       ha='left', va='center', color='white', transform=ax.transAxes)

                # 가격
                ax.text(0.5, y, f'{price:,.2f}', fontsize=20, fontweight='bold',
                       ha='center', va='center', color='white', transform=ax.transAxes)

                # 변동
                ax.text(0.85, y, f'{arrow} {abs(change):,.2f} ({change_pct:+.2f}%)',
                       fontsize=14, ha='right', va='center', color=color, transform=ax.transAxes)

                # 구분선
                if i < len(data) - 1:
                    ax.plot([0.05, 0.95], [y - 0.06, y - 0.06], color='#333333',
                           linewidth=1, transform=ax.transAxes)

            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')

            plt.tight_layout()

            # 이미지를 바이트로 변환
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=150, facecolor='#1a1a2e',
                       bbox_inches='tight', pad_inches=0.2)
            buf.seek(0)
            plt.close(fig)

            logger.info("미국 시장 차트 생성 완료")
            return buf

        except Exception as e:
            logger.error(f"미국 시장 차트 생성 실패: {e}")
            return None

    async def capture_naver_world_screenshot(self):
        """네이버 금융 세계 증시 페이지 스크린샷 캡처 (세계 주요 증시 현황)"""
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(viewport={'width': 1100, 'height': 900})

                await page.goto('https://finance.naver.com/world/',
                              wait_until='domcontentloaded', timeout=60000)

                # 페이지 로딩 대기
                await asyncio.sleep(3)

                # "세계 주요 증시 현황" 섹션 캡처 (제목 + 차트 + 하단 지수)
                screenshot_bytes = await page.screenshot(
                    clip={'x': 70, 'y': 220, 'width': 960, 'height': 400}
                )

                await browser.close()

                buf = BytesIO(screenshot_bytes)
                buf.seek(0)
                logger.info("네이버 세계 증시 스크린샷 캡처 완료")
                return buf

        except Exception as e:
            logger.error(f"네이버 세계 증시 스크린샷 캡처 실패: {e}")
            # 실패 시 기존 차트 생성 방식으로 폴백
            data = self.fetch_us_market_data()
            return self.create_market_chart(data)
