"""
TQ버스 승하차 알리미 모듈

전략: TQQQ 193일 이동평균선 기반
- 가격 > SMA → TQQQ 보유 (승차)
- 가격 <= SMA → 현금 보유 (하차)
- 가격이 SMA와 7% 이내로 가까워지면 승하차 준비 알림
"""
import logging
import json
import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

# 거래 기록 저장 파일
TRADES_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'tqbus_trades.json')


@dataclass
class TqBusData:
    """TQ버스 데이터"""
    date: str
    tqqq_price: float
    sma_193: float
    position: str  # 'TQQQ' or 'CASH'
    signal: str    # 'BUY', 'SELL', 'NONE'
    diff_percent: float  # 가격과 SMA 차이 (%)


@dataclass
class Trade:
    """거래 기록"""
    date: str
    action: str       # 'BUY' or 'SELL'
    price: float
    profit_percent: Optional[float] = None  # SELL일 때만


class TqBusTracker:
    """TQ버스 전략 추적 클래스"""

    SMA_PERIOD = 193
    # 알림 레벨 (이평선과의 거리 %)
    ALERT_THRESHOLDS = [7.0, 5.0, 3.0, -3.0, -5.0, -7.0]

    def __init__(self):
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.trades: List[Trade] = []
        self._load_trades()

    def _load_trades(self):
        """저장된 거래 기록 로드"""
        try:
            os.makedirs(os.path.dirname(TRADES_FILE), exist_ok=True)
            if os.path.exists(TRADES_FILE):
                with open(TRADES_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.trades = [Trade(**t) for t in data]
                logger.info(f"거래 기록 {len(self.trades)}건 로드됨")
        except Exception as e:
            logger.error(f"거래 기록 로드 오류: {e}")
            self.trades = []

    def _save_trades(self):
        """거래 기록 저장"""
        try:
            os.makedirs(os.path.dirname(TRADES_FILE), exist_ok=True)
            with open(TRADES_FILE, 'w', encoding='utf-8') as f:
                data = [{'date': t.date, 'action': t.action, 'price': t.price, 'profit_percent': t.profit_percent}
                        for t in self.trades]
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"거래 기록 저장 오류: {e}")

    def get_tqqq_data(self) -> Optional[Tuple[List[float], List[int], float]]:
        """
        TQQQ 과거 데이터 가져오기 (Yahoo Finance Chart API)

        Returns:
            (종가 리스트, 타임스탬프 리스트, 현재가)
        """
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/TQQQ"
            params = {
                "interval": "1d",
                "range": "3y"  # 3년 데이터 (193일 SMA 정확한 계산용)
            }

            response = requests.get(url, params=params, headers=self._headers, timeout=15)

            if response.status_code != 200:
                logger.error(f"TQQQ API 오류: {response.status_code}")
                return None

            data = response.json()
            result = data.get("chart", {}).get("result", [{}])[0]

            if not result:
                return None

            meta = result.get("meta", {})
            timestamps = result.get("timestamp", [])
            quotes = result.get("indicators", {}).get("quote", [{}])[0]
            closes = quotes.get("close", [])

            current_price = meta.get("regularMarketPrice", 0)

            # None 값 제거
            valid_data = [(ts, c) for ts, c in zip(timestamps, closes) if c is not None]
            if not valid_data:
                return None

            timestamps, closes = zip(*valid_data)

            return list(closes), list(timestamps), current_price

        except Exception as e:
            logger.error(f"TQQQ 데이터 조회 오류: {e}")
            return None

    def calculate_sma(self, closes: List[float], period: int = 193) -> Optional[float]:
        """
        단순이동평균 계산

        Args:
            closes: 종가 리스트
            period: 이동평균 기간

        Returns:
            SMA 값
        """
        if len(closes) < period:
            logger.warning(f"데이터 부족: {len(closes)}일 < {period}일")
            return None

        return sum(closes[-period:]) / period

    def calculate_sma_series(self, closes: List[float], period: int = 193) -> List[Optional[float]]:
        """
        전체 기간에 대한 SMA 시리즈 계산

        Args:
            closes: 종가 리스트
            period: 이동평균 기간

        Returns:
            SMA 값 리스트 (앞부분은 None)
        """
        sma_series = []
        for i in range(len(closes)):
            if i < period - 1:
                sma_series.append(None)
            else:
                sma = sum(closes[i - period + 1:i + 1]) / period
                sma_series.append(sma)
        return sma_series

    def find_last_entry_point(self) -> Optional[Dict]:
        """
        마지막 승차 시점 찾기 (193 이평선 상향 돌파 지점)

        Returns:
            {'date': 승차일, 'price': 승차가격} 또는 None
        """
        result = self.get_tqqq_data()
        if not result:
            return None

        closes, timestamps, current_price = result

        # SMA 시리즈 계산
        sma_series = self.calculate_sma_series(closes, self.SMA_PERIOD)

        # 뒤에서부터 탐색하여 상향 돌파 지점 찾기
        # 현재 가격이 SMA 위에 있어야 함 (승차 중)
        if len(closes) < self.SMA_PERIOD + 1:
            return None

        last_sma = sma_series[-1]
        if last_sma is None or current_price <= last_sma:
            return None  # 현재 하차 중이면 승차 정보 없음

        # 마지막 상향 돌파 지점 찾기
        entry_idx = None
        for i in range(len(closes) - 1, self.SMA_PERIOD, -1):
            prev_close = closes[i - 1]
            prev_sma = sma_series[i - 1]
            curr_close = closes[i]
            curr_sma = sma_series[i]

            if prev_sma is None or curr_sma is None:
                continue

            # 전일: 이평선 아래, 당일: 이평선 위 → 상향 돌파
            if prev_close <= prev_sma and curr_close > curr_sma:
                entry_idx = i
                break

        if entry_idx is None:
            # 전체 기간 동안 계속 승차 중이면 첫 SMA 계산 가능일을 승차일로
            entry_idx = self.SMA_PERIOD - 1

        entry_date = datetime.fromtimestamp(timestamps[entry_idx]).strftime('%Y-%m-%d')
        entry_price = closes[entry_idx]

        return {
            'date': entry_date,
            'price': round(entry_price, 2)
        }

    def get_current_status(self) -> Optional[TqBusData]:
        """
        현재 TQ버스 상태 조회

        Returns:
            TqBusData 객체
        """
        result = self.get_tqqq_data()
        if not result:
            return None

        closes, timestamps, current_price = result

        sma = self.calculate_sma(closes, self.SMA_PERIOD)
        if sma is None:
            return None

        # 현재 포지션 결정
        position = 'TQQQ' if current_price > sma else 'CASH'

        # 이전 포지션과 비교하여 시그널 결정
        signal = 'NONE'
        if self.trades:
            last_trade = self.trades[-1]
            if last_trade.action == 'SELL' and position == 'TQQQ':
                signal = 'BUY'
            elif last_trade.action == 'BUY' and position == 'CASH':
                signal = 'SELL'
        elif position == 'TQQQ':
            signal = 'BUY'  # 첫 진입

        # SMA와의 차이 (%)
        diff_percent = ((current_price - sma) / sma) * 100

        today = datetime.now().strftime('%Y-%m-%d')

        return TqBusData(
            date=today,
            tqqq_price=round(current_price, 2),
            sma_193=round(sma, 2),
            position=position,
            signal=signal,
            diff_percent=round(diff_percent, 2)
        )

    def record_trade(self, action: str, price: float, date: str = None):
        """
        거래 기록

        Args:
            action: 'BUY' or 'SELL'
            price: 거래 가격
            date: 거래 날짜 (기본값: 오늘)
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        profit_percent = None

        # SELL인 경우 수익률 계산
        if action == 'SELL' and self.trades:
            # 마지막 BUY 찾기
            for trade in reversed(self.trades):
                if trade.action == 'BUY':
                    profit_percent = round(((price - trade.price) / trade.price) * 100, 2)
                    break

        trade = Trade(date=date, action=action, price=price, profit_percent=profit_percent)
        self.trades.append(trade)
        self._save_trades()

        logger.info(f"거래 기록: {action} @ ${price} ({date})")

    def get_recent_trades(self, count: int = 5) -> List[Trade]:
        """최근 거래 기록 조회"""
        return self.trades[-count:] if self.trades else []

    def get_current_profit(self, current_price: float) -> Optional[float]:
        """
        현재 보유 중인 포지션의 미실현 수익률

        Args:
            current_price: 현재 가격

        Returns:
            미실현 수익률 (%) 또는 None (보유 중이 아닌 경우)
        """
        if not self.trades:
            return None

        last_trade = self.trades[-1]

        # 마지막 거래가 BUY인 경우에만 미실현 수익 계산
        if last_trade.action == 'BUY':
            return round(((current_price - last_trade.price) / last_trade.price) * 100, 2)

        return None

    def get_current_alert_level(self) -> Optional[float]:
        """
        현재 가격이 속한 알림 레벨 반환

        Returns:
            알림 레벨 (7.0, 5.0, 3.0, -3.0, -5.0, -7.0) 또는 None
        """
        status = self.get_current_status()
        if status is None:
            return None

        diff = status.diff_percent

        # 양수 레벨 체크 (이평선 위)
        if diff > 0:
            # +7% 이상 → +7% 레벨
            if diff >= 7.0:
                return 7.0
            # +5% ~ +7% → +5% 레벨
            elif diff >= 5.0:
                return 5.0
            # +3% ~ +5% → +3% 레벨
            elif diff >= 3.0:
                return 3.0
        # 음수 레벨 체크 (이평선 아래)
        elif diff < 0:
            # -7% 이하 → -7% 레벨
            if diff <= -7.0:
                return -7.0
            # -5% ~ -7% → -5% 레벨
            elif diff <= -5.0:
                return -5.0
            # -3% ~ -5% → -3% 레벨
            elif diff <= -3.0:
                return -3.0

        return None

    def should_alert(self) -> Optional[float]:
        """
        승하차 준비 알림 필요 여부

        Returns:
            알림 레벨 (7.0, 5.0, 3.0, -3.0, -5.0, -7.0) 또는 None
        """
        return self.get_current_alert_level()

    def detect_crossover(self) -> Optional[str]:
        """
        SMA 돌파 감지 (종가 기준)

        Returns:
            'BUY' (상향 돌파), 'SELL' (하향 돌파), None (돌파 없음)
        """
        result = self.get_tqqq_data()
        if not result:
            return None

        closes, timestamps, current_price = result

        if len(closes) < self.SMA_PERIOD + 2:
            return None

        sma_series = self.calculate_sma_series(closes, self.SMA_PERIOD)

        # 어제와 오늘의 종가 및 SMA
        today_close = closes[-1]
        yesterday_close = closes[-2]
        today_sma = sma_series[-1]
        yesterday_sma = sma_series[-2]

        if today_sma is None or yesterday_sma is None:
            return None

        # 상향 돌파: 어제 SMA 아래, 오늘 SMA 위
        if yesterday_close <= yesterday_sma and today_close > today_sma:
            return 'BUY'

        # 하향 돌파: 어제 SMA 위, 오늘 SMA 아래
        if yesterday_close > yesterday_sma and today_close <= today_sma:
            return 'SELL'

        return None

    def format_crossover_message(self, crossover_type: str) -> Optional[str]:
        """
        SMA 돌파 알림 메시지

        Args:
            crossover_type: 'BUY' or 'SELL'

        Returns:
            알림 메시지
        """
        status = self.get_current_status()
        if status is None:
            return None

        if crossover_type == 'BUY':
            message = "🚌💨 <b>TQ버스 승차!</b>\n\n"
            message += "📈 <b>193일 이평선 상향 돌파!</b>\n\n"
            message += f"TQQQ: ${status.tqqq_price}\n"
            message += f"193 SMA: ${status.sma_193}\n"
            message += f"차이: {status.diff_percent:+.2f}%\n\n"
            message += "💡 TQQQ 매수 신호"
        else:
            message = "🚏🔻 <b>TQ버스 하차!</b>\n\n"
            message += "📉 <b>193일 이평선 하향 돌파!</b>\n\n"
            message += f"TQQQ: ${status.tqqq_price}\n"
            message += f"193 SMA: ${status.sma_193}\n"
            message += f"차이: {status.diff_percent:+.2f}%\n\n"
            message += "💡 TQQQ 매도 신호"

        return message

    def format_status_message(self) -> str:
        """
        현재 상태 메시지 포맷

        Returns:
            포맷된 텔레그램 메시지
        """
        status = self.get_current_status()
        if status is None:
            return "TQ버스 데이터를 가져올 수 없습니다"

        # 포지션 이모지
        pos_emoji = "🚌" if status.position == 'TQQQ' else "🚏"
        pos_text = "승차 중 (TQQQ 보유)" if status.position == 'TQQQ' else "하차 중 (현금 보유)"

        # 차이 이모지
        diff_emoji = "📈" if status.diff_percent > 0 else "📉"

        message = f"🚌 <b>TQ버스 승하차 알리미</b>\n"
        message += f"📅 {status.date}\n\n"

        message += f"<b>📊 현재 상태</b>\n"
        message += f"  TQQQ 현재가: <b>${status.tqqq_price}</b>\n"
        message += f"  193일 이평선: <b>${status.sma_193}</b>\n"
        message += f"  {diff_emoji} 이평선 대비: <b>{status.diff_percent:+.2f}%</b>\n\n"

        message += f"<b>{pos_emoji} 현재 포지션</b>\n"
        message += f"  {pos_text}\n\n"

        # 승차 중인 경우 승차 정보 및 수익률 표시
        if status.position == 'TQQQ':
            entry_point = self.find_last_entry_point()
            if entry_point:
                entry_profit = ((status.tqqq_price - entry_point['price']) / entry_point['price']) * 100
                profit_emoji = "🟢" if entry_profit >= 0 else "🔴"

                message += f"<b>💰 승차 정보</b>\n"
                message += f"  승차일: <b>{entry_point['date']}</b>\n"
                message += f"  승차 가격: <b>${entry_point['price']}</b>\n"
                message += f"  {profit_emoji} 현재 수익률: <b>{entry_profit:+.2f}%</b>\n\n"

        # 최근 5거래
        recent_trades = self.get_recent_trades(5)
        if recent_trades:
            message += f"<b>📋 최근 거래 내역</b>\n"
            for trade in recent_trades:
                action_emoji = "🟢" if trade.action == 'BUY' else "🔴"
                profit_str = ""
                if trade.profit_percent is not None:
                    p_emoji = "+" if trade.profit_percent >= 0 else ""
                    profit_str = f" ({p_emoji}{trade.profit_percent}%)"
                message += f"  {action_emoji} {trade.date}: {trade.action} @ ${trade.price}{profit_str}\n"
        else:
            message += f"<b>📋 거래 내역</b>\n"
            message += f"  거래 기록 없음\n"

        return message

    def format_alert_message(self, level: float = None) -> Optional[str]:
        """
        승하차 준비 알림 메시지 포맷 (레벨별)

        Args:
            level: 알림 레벨 (7.0, 5.0, 3.0, -3.0, -5.0, -7.0)

        Returns:
            알림 메시지 또는 None
        """
        status = self.get_current_status()
        if status is None:
            return None

        # 레벨이 지정되지 않았으면 현재 레벨 사용
        if level is None:
            level = self.get_current_alert_level()

        if level is None:
            return None

        # 레벨별 메시지 생성
        level_int = int(abs(level))

        if level > 0:
            # 이평선 위
            if status.position == 'CASH':
                alert_type = f"🚌 승차 준비! (이평선 +{level_int}% 이내)"
                alert_desc = f"가격이 이평선 위 {level_int}% 이내로 접근 중\n💡 상향 돌파 시 TQQQ 매수 신호"
            else:
                alert_type = f"⚠️ 주의! (이평선 +{level_int}% 이내)"
                alert_desc = f"가격이 이평선 위 {level_int}% 이내로 하락 중\n💡 이평선 근처 접근 중 - 주의 필요"
        else:
            # 이평선 아래
            if status.position == 'TQQQ':
                alert_type = f"🚏 하차 준비! (이평선 -{level_int}% 이내)"
                alert_desc = f"가격이 이평선 아래 {level_int}% 이내로 하락 중\n💡 추가 하락 시 TQQQ 매도 신호"
            else:
                alert_type = f"⚠️ 주의! (이평선 -{level_int}% 이내)"
                alert_desc = f"가격이 이평선 아래 {level_int}% 이내\n💡 이평선 아래 유지 중 - 관망 필요"

        message = f"<b>{alert_type}</b>\n\n"
        message += f"TQQQ: <b>${status.tqqq_price}</b>\n"
        message += f"193 SMA: <b>${status.sma_193}</b>\n"
        message += f"차이: <b>{status.diff_percent:+.2f}%</b>\n\n"
        message += f"{alert_desc}"

        return message


# 테스트용
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    tracker = TqBusTracker()

    print("=== TQ버스 현재 상태 ===")
    status = tracker.get_current_status()
    if status:
        print(f"TQQQ: ${status.tqqq_price}")
        print(f"SMA 193: ${status.sma_193}")
        print(f"차이: {status.diff_percent:+.2f}%")
        print(f"포지션: {status.position}")
        print(f"시그널: {status.signal}")

    print("\n=== 메시지 포맷 ===")
    print(tracker.format_status_message())

    if tracker.should_alert():
        print("\n=== 알림 메시지 ===")
        print(tracker.format_alert_message())
