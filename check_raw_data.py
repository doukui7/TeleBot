"""
Yahoo Finance API 원본 데이터 확인 스크립트
"""
import requests
import json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def check_symbol(symbol, name):
    print(f"\n{'='*60}")
    print(f"  {symbol} - {name}")
    print('='*60)

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {"interval": "1d", "range": "5d"}

    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = response.json()
        result = data.get("chart", {}).get("result", [{}])[0]

        meta = result.get("meta", {})
        quotes = result.get("indicators", {}).get("quote", [{}])[0]
        timestamps = result.get("timestamp", [])
        closes = quotes.get("close", [])

        print(f"\n[META 데이터]")
        print(f"  regularMarketPrice:  ${meta.get('regularMarketPrice', 'N/A')}")
        print(f"  previousClose:       ${meta.get('previousClose', 'N/A')}")
        print(f"  chartPreviousClose:  ${meta.get('chartPreviousClose', 'N/A')}")

        print(f"\n[CHART 데이터 - 최근 5일 종가]")
        from datetime import datetime
        for i, (ts, close) in enumerate(zip(timestamps[-5:], closes[-5:])):
            date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            close_str = f"${close:.2f}" if close else "None"
            print(f"  {date}: {close_str}")

        # 변동률 계산 비교
        print(f"\n[변동률 계산 비교]")

        # 방법 1: meta 사용 (etf_tracker 방식)
        current = meta.get('regularMarketPrice', 0)
        prev_meta = meta.get('chartPreviousClose') or meta.get('previousClose', 0)
        if current and prev_meta:
            change1 = ((current - prev_meta) / prev_meta) * 100
            print(f"  방법1 (meta): {current:.2f} / {prev_meta:.2f} = {change1:+.2f}%")

        # 방법 2: closes 배열 사용 (stock_monitor 방식)
        valid_closes = [c for c in closes if c is not None]
        if len(valid_closes) >= 2:
            current2 = valid_closes[-1]
            prev2 = valid_closes[-2]
            change2 = ((current2 - prev2) / prev2) * 100
            print(f"  방법2 (closes): {current2:.2f} / {prev2:.2f} = {change2:+.2f}%")

    except Exception as e:
        print(f"  ERROR: {e}")

def main():
    print("#" * 60)
    print("#  Yahoo Finance API 원본 데이터 확인")
    print("#" * 60)

    # 지수
    symbols = [
        ("^KS11", "코스피"),
        ("^IXIC", "나스닥"),
        ("^GSPC", "S&P 500"),
        ("NQ=F", "나스닥 선물"),
        ("BTC-USD", "비트코인"),
        ("ETH-USD", "이더리움"),
    ]

    print("\n" + "=" * 60)
    print("  [1] 주요 지수 & 암호화폐")
    print("=" * 60)

    for symbol, name in symbols:
        check_symbol(symbol, name)

    # ETF
    etfs = [
        ("TQQQ", "나스닥 3배"),
        ("SOXL", "반도체 3배"),
        ("UPRO", "S&P 3배"),
    ]

    print("\n" + "=" * 60)
    print("  [2] 3X 레버리지 ETF")
    print("=" * 60)

    for symbol, name in etfs:
        check_symbol(symbol, name)

    print("\n" + "#" * 60)
    print("#  확인 완료")
    print("#" * 60)

if __name__ == "__main__":
    main()
