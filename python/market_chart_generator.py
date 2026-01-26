"""
시장 현황 차트 생성 모듈
"""
import logging
import requests
from typing import List, Dict, Optional
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import io

logger = logging.getLogger(__name__)

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False


class MarketChartGenerator:
    """시장 현황 차트 생성 클래스"""

    INDICES = {
        "^IXIC": ("NASDAQ", "#00BFFF"),      # 파란색
        "^GSPC": ("S&P 500", "#FF6B6B"),     # 빨간색
        "^KS11": ("KOSPI", "#4CAF50"),       # 초록색
    }

    CRYPTO = {
        "BTC-USD": ("Bitcoin", "#F7931A"),   # 비트코인 오렌지
    }

    def __init__(self):
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def get_chart_data(self, symbol: str) -> Optional[Dict]:
        """
        1년 차트 데이터 가져오기

        Returns:
            {'dates': [], 'closes': [], 'name': str, 'color': str}
        """
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                "interval": "1d",
                "range": "1y"
            }

            response = requests.get(url, params=params, headers=self._headers, timeout=15)

            if response.status_code != 200:
                logger.warning(f"{symbol}: API 오류 ({response.status_code})")
                return None

            data = response.json()
            result = data.get("chart", {}).get("result", [{}])[0]

            if not result:
                return None

            timestamps = result.get("timestamp", [])
            quotes = result.get("indicators", {}).get("quote", [{}])[0]
            closes = quotes.get("close", [])

            # 유효한 데이터만 필터링
            valid_data = [(ts, c) for ts, c in zip(timestamps, closes) if c is not None]
            if not valid_data:
                return None

            dates = [datetime.fromtimestamp(ts) for ts, _ in valid_data]
            closes = [c for _, c in valid_data]

            # 심볼 정보
            if symbol in self.INDICES:
                name, color = self.INDICES[symbol]
            elif symbol in self.CRYPTO:
                name, color = self.CRYPTO[symbol]
            else:
                name, color = symbol, "#666666"

            return {
                'dates': dates,
                'closes': closes,
                'name': name,
                'color': color,
                'current': closes[-1] if closes else 0,
                'change_1y': ((closes[-1] - closes[0]) / closes[0] * 100) if closes else 0
            }

        except Exception as e:
            logger.error(f"{symbol} 차트 데이터 오류: {e}")
            return None

    def create_market_chart(self) -> Optional[io.BytesIO]:
        """
        시장 현황 차트 생성 (4개 지수를 2x2 스파크라인으로)

        Returns:
            이미지 바이트 스트림
        """
        try:
            symbols = list(self.INDICES.keys()) + list(self.CRYPTO.keys())
            chart_data = {}

            for symbol in symbols:
                data = self.get_chart_data(symbol)
                if data:
                    chart_data[symbol] = data

            if not chart_data:
                logger.warning("차트 데이터 없음")
                return None

            # 2x2 차트 (높이 절반)
            fig, axes = plt.subplots(2, 2, figsize=(8, 3))
            axes = axes.flatten()

            for idx, (symbol, data) in enumerate(chart_data.items()):
                if idx >= 4:
                    break

                ax = axes[idx]
                closes = data['closes']
                color = data['color']
                name = data['name']
                current = data['current']
                change = data['change_1y']

                # 차트 그리기
                ax.plot(closes, color=color, linewidth=1.5)
                ax.fill_between(range(len(closes)), closes, alpha=0.2, color=color)

                # 축 스타일 (xy축 표시)
                ax.tick_params(axis='both', labelsize=6)
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)

                # 제목 (이름, 가격, 수익률)
                change_sign = "+" if change >= 0 else ""
                title = f"{name}\n${current:,.0f} ({change_sign}{change:.1f}%)"
                ax.set_title(title, fontsize=9, fontweight='bold', color=color)

            # 빈 축 숨기기
            for idx in range(len(chart_data), 4):
                axes[idx].set_visible(False)

            plt.tight_layout()

            # 이미지로 저장
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=120, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            img_buffer.seek(0)
            plt.close()

            logger.info("시장 현황 차트 생성 성공")
            return img_buffer

        except Exception as e:
            logger.error(f"차트 생성 오류: {e}")
            return None

    def create_single_chart(self, symbol: str) -> Optional[io.BytesIO]:
        """
        단일 종목 차트 생성

        Returns:
            이미지 바이트 스트림
        """
        try:
            data = self.get_chart_data(symbol)
            if not data:
                return None

            fig, ax = plt.subplots(figsize=(8, 4))

            dates = data['dates']
            closes = data['closes']
            color = data['color']
            name = data['name']
            current = data['current']
            change = data['change_1y']

            # 차트 그리기
            ax.plot(dates, closes, color=color, linewidth=2)
            ax.fill_between(dates, closes, alpha=0.15, color=color)

            # 현재가 표시
            ax.axhline(y=current, color=color, linestyle='--', alpha=0.5)

            # 제목
            change_sign = "+" if change >= 0 else ""
            ax.set_title(f"{name} - ${current:,.2f} ({change_sign}{change:.1f}% YTD)",
                        fontsize=14, fontweight='bold')

            # 축 설정
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, alpha=0.3)

            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

            plt.tight_layout()

            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight',
                       facecolor='white')
            img_buffer.seek(0)
            plt.close()

            return img_buffer

        except Exception as e:
            logger.error(f"단일 차트 생성 오류: {e}")
            return None


# 테스트용
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    generator = MarketChartGenerator()

    print("Creating market chart...")
    chart = generator.create_market_chart()

    if chart:
        with open("market_chart_test.png", "wb") as f:
            f.write(chart.read())
        print("Saved to market_chart_test.png")
    else:
        print("Failed to create chart")
