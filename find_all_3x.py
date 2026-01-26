"""
모든 3배 Bull ETF 검색
"""
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# 현재 목록
CURRENT_LIST = [
    "TQQQ", "UPRO", "SPXL", "UDOW", "TNA", "MIDU", "HIBL",
    "SOXL", "TECL", "FNGU", "BULZ", "WEBL", "UBOT",
    "FAS", "DPST", "LABU", "CURE", "PILL",
    "NAIL", "DFEN", "DUSL", "TPOR", "RETL", "WANT", "DRN", "UTSL",
    "ERX", "GUSH", "NUGT",
    "TMF", "TYD"
]

# 추가로 확인할 3배 Bull ETF 후보
CANDIDATES = [
    # Direxion
    ("URTY", "Russell 2000 3배"),
    ("UMDD", "Mid Cap 3배"),
    ("UDOW", "다우 3배"),
    ("SPUU", "S&P 3배"),
    ("OILU", "원유 3배"),
    ("NRGU", "에너지 3배"),
    ("EURL", "유럽 3배"),
    ("YINN", "중국 3배"),
    ("INDL", "인도 3배"),
    ("KORU", "한국 3배"),
    ("EDC", "이머징 3배"),
    ("MEXX", "멕시코 3배"),
    ("RUSL", "러시아 3배"),
    # ProShares
    ("TPOR", "운송 3배"),
    ("UCO", "원유 2배"),
    ("BOIL", "천연가스 2배"),
    # MicroSectors
    ("BNKU", "은행 3배"),
    ("OILD", "원유 3배 인버스"),
    ("NRGD", "에너지 3배 인버스"),
    ("FNGD", "빅테크 3배 인버스"),
    # 기타
    ("ROM", "기술 2배"),
    ("UYG", "금융 2배"),
    ("DIG", "에너지 2배"),
    ("UGL", "금 2배"),
    ("AGQ", "은 2배"),
    ("URTY", "소형주 3배"),
    ("LBJ", "라틴아메리카 3배"),
    ("SQQQ", "나스닥 3배 인버스"),
    ("SPXU", "S&P 3배 인버스"),
    ("SDOW", "다우 3배 인버스"),
]

def check_etf(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {"interval": "1d", "range": "5d"}
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = response.json()
        result = data.get("chart", {}).get("result", [])
        if result:
            meta = result[0].get("meta", {})
            price = meta.get("regularMarketPrice", 0)
            name = meta.get("shortName", "")
            return True, price, name
        return False, 0, ""
    except:
        return False, 0, ""

def main():
    print("=" * 70)
    print("  3배 Bull ETF 전체 검색 (인버스/2배/해외 제외)")
    print("=" * 70)

    # 현재 목록 확인
    print(f"\n[현재 목록: {len(CURRENT_LIST)}개]")

    # 추가 후보 확인
    print(f"\n[추가 후보 확인 중...]")

    missing = []
    for symbol, desc in CANDIDATES:
        if symbol in CURRENT_LIST:
            continue

        exists, price, name = check_etf(symbol)
        if exists and price > 0:
            # 인버스/Bear 제외
            if "Bear" in name or "Short" in name or "Inverse" in name:
                continue
            # 2배 제외 (3배만)
            if "2X" in name or "2x" in name or "Ultra " in name and "UltraPro" not in name:
                continue
            # 해외 ETF 제외
            if symbol in ["EURL", "YINN", "INDL", "KORU", "EDC", "MEXX", "RUSL", "LBJ"]:
                continue

            missing.append((symbol, desc, price, name))
            print(f"  발견: {symbol} - {name} (${price:.2f})")

    print(f"\n[결과]")
    print(f"  현재: {len(CURRENT_LIST)}개")
    print(f"  추가 가능: {len(missing)}개")

    if missing:
        print(f"\n[추가 필요 ETF]")
        for symbol, desc, price, name in missing:
            print(f'    "{symbol}",   # {name}')

if __name__ == "__main__":
    main()
