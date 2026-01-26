"""
ETF 가격 확인 스크립트 - 콘솔 출력용
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.etf_tracker import ETFTracker

def main():
    tracker = ETFTracker(etf_list=['TQQQ', 'SOXL', 'UPRO', 'SPXL', 'TECL', 'FNGU', 'LABU', 'TNA'])

    print('=' * 90)
    print('3X ETF LIST - 실시간 데이터 확인')
    print('=' * 90)
    print(f'{"Symbol":<8} {"Current":>10} {"52W High":>10} {"High Date":>12} {"DD%":>8} {"YTD%":>8} {"Daily%":>8}')
    print('-' * 90)

    for symbol in tracker.etf_list:
        data = tracker.get_etf_data(symbol)
        if data:
            print(f'{data["symbol"]:<8} ${data["current_price"]:>8.2f} ${data["high_52w"]:>8.2f} {data["high_52w_date"]:>12} {data["dd"]:>7.2f}% {data["ytd_return"]:>7.2f}% {data["daily_change"]:>+7.2f}%')
        else:
            print(f'{symbol:<8} ERROR: 데이터 조회 실패')

    print('=' * 90)

if __name__ == "__main__":
    main()
