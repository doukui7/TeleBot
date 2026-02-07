"""
TQ버스 단계별 알림 테스트
"""
import sys
import os
import logging

# python/ 폴더를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from tqbus_tracker import TqBusTracker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_tqbus_levels():
    """TQ버스 단계별 알림 테스트"""
    tracker = TqBusTracker()

    print("=" * 60)
    print("TQ버스 현재 상태")
    print("=" * 60)

    status = tracker.get_current_status()
    if status:
        print(f"TQQQ 가격: ${status.tqqq_price}")
        print(f"193 SMA: ${status.sma_193}")
        print(f"차이: {status.diff_percent:+.2f}%")
        print(f"포지션: {status.position}")
        print()

        # 현재 알림 레벨
        alert_level = tracker.get_current_alert_level()
        if alert_level:
            print(f"현재 알림 레벨: {alert_level:+.1f}%")
            print()
            print("=" * 60)
            print("알림 메시지 미리보기")
            print("=" * 60)
            msg = tracker.format_alert_message(alert_level)
            print(msg)
        else:
            print("현재 알림 범위 밖 (±3% ~ ±7% 범위 밖)")

        # 모든 레벨 메시지 샘플
        print("\n" + "=" * 60)
        print("모든 레벨 메시지 샘플")
        print("=" * 60)

        for level in [7.0, 5.0, 3.0, -3.0, -5.0, -7.0]:
            print(f"\n--- 레벨: {level:+.1f}% ---")
            msg = tracker.format_alert_message(level)
            if msg:
                # HTML 태그 제거해서 출력
                import re
                clean_msg = re.sub('<[^<]+?>', '', msg)
                print(clean_msg)
    else:
        print("데이터를 가져올 수 없습니다")


if __name__ == "__main__":
    test_tqbus_levels()
