"""
3배 레버리지 ETF 전체 목록 확인
"""
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# 알려진 모든 3배 Bull ETF 목록
ALL_3X_BULL_ETFS = {
    # 현재 목록에 있는 것
    "TQQQ": "나스닥 3배 (QQQ)",
    "SOXL": "반도체 3배",
    "FNGU": "빅테크 FANG+ 3배",
    "UPRO": "S&P500 3배 (ProShares)",
    "SPXL": "S&P500 3배 (Direxion)",
    "TECL": "기술 3배",
    "FAS": "금융 3배",
    "TNA": "소형주 3배 (Russell 2000)",
    "LABU": "바이오 3배",
    "UDOW": "다우30 3배",
    "TMF": "장기국채 3배 (20Y+)",
    "NAIL": "주택건설 3배",
    "DFEN": "방산/항공 3배",
    "CURE": "헬스케어 3배",
    "KORU": "한국 3배",
    "RETL": "리테일 3배",
    "DRN": "부동산 3배",
    "DUSL": "산업 3배",
    "EDC": "이머징마켓 3배",
    "MIDU": "중형주 3배",

    # 추가 가능한 3배 Bull ETF
    "NUGT": "금광주 3배",
    "JNUG": "주니어금광 3배",
    "GUSH": "석유/가스 E&P 3배",
    "ERX": "에너지 3배",
    "PILL": "제약 3배",
    "WANT": "소비재 3배",
    "UTSL": "유틸리티 3배",
    "TPOR": "운송 3배",
    "DPST": "지방은행 3배",
    "HIBL": "S&P 고베타 3배",
    "WEBL": "인터넷 3배",
    "MEXX": "멕시코 3배",
    "YINN": "중국 3배 (FTSE)",
    "EURL": "유럽 3배",
    "INDL": "인도 3배",
    "TYD": "7-10년 국채 3배",
    "UBOT": "로봇/AI 3배",
    "BULZ": "빅테크 3배 (MicroSectors)",
}

def check_etf(symbol):
    """ETF 존재 여부 및 현재가 확인"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {"interval": "1d", "range": "5d"}

    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = response.json()
        result = data.get("chart", {}).get("result", [])

        if result:
            meta = result[0].get("meta", {})
            price = meta.get("regularMarketPrice", 0)
            return True, price
        return False, 0
    except:
        return False, 0

def main():
    current_list = [
        "TQQQ", "SOXL", "FNGU", "UPRO", "SPXL", "TECL", "FAS", "TNA",
        "LABU", "UDOW", "TMF", "NAIL", "DFEN", "CURE", "KORU", "RETL",
        "DRN", "DUSL", "EDC", "MIDU"
    ]

    print("=" * 70)
    print("  3배 레버리지 Bull ETF 전체 확인")
    print("=" * 70)

    print(f"\n{'Symbol':<8} {'이름':<25} {'현재가':>10} {'상태':<10}")
    print("-" * 70)

    valid_etfs = []
    missing_etfs = []

    for symbol, name in ALL_3X_BULL_ETFS.items():
        exists, price = check_etf(symbol)
        in_list = "✅ 포함" if symbol in current_list else "❌ 누락"

        if exists:
            valid_etfs.append((symbol, name, price, symbol in current_list))
            print(f"{symbol:<8} {name:<25} ${price:>8.2f}  {in_list}")
        else:
            missing_etfs.append((symbol, name))
            print(f"{symbol:<8} {name:<25} {'N/A':>10}  ⚠️ 조회불가")

    print("\n" + "=" * 70)
    print(f"  총 {len(valid_etfs)}개 유효 / {len(missing_etfs)}개 조회불가")
    print("=" * 70)

    # 누락된 ETF 목록
    not_included = [e for e in valid_etfs if not e[3]]
    if not_included:
        print(f"\n[추가 필요한 ETF - {len(not_included)}개]")
        for symbol, name, price, _ in not_included:
            print(f'    "{symbol}",   # {name}')

if __name__ == "__main__":
    main()
