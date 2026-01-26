"""
미국/한국 증시 휴장일 관리
"""
from datetime import datetime, date

# 미국 증시 휴장일 (2024-2026)
US_HOLIDAYS = {
    # 2024
    "2024-01-01",  # New Year's Day
    "2024-01-15",  # MLK Day
    "2024-02-19",  # Presidents Day
    "2024-03-29",  # Good Friday
    "2024-05-27",  # Memorial Day
    "2024-06-19",  # Juneteenth
    "2024-07-04",  # Independence Day
    "2024-09-02",  # Labor Day
    "2024-11-28",  # Thanksgiving
    "2024-12-25",  # Christmas
    # 2025
    "2025-01-01",  # New Year's Day
    "2025-01-20",  # MLK Day
    "2025-02-17",  # Presidents Day
    "2025-04-18",  # Good Friday
    "2025-05-26",  # Memorial Day
    "2025-06-19",  # Juneteenth
    "2025-07-04",  # Independence Day
    "2025-09-01",  # Labor Day
    "2025-11-27",  # Thanksgiving
    "2025-12-25",  # Christmas
    # 2026
    "2026-01-01",  # New Year's Day
    "2026-01-19",  # MLK Day
    "2026-02-16",  # Presidents Day
    "2026-04-03",  # Good Friday
    "2026-05-25",  # Memorial Day
    "2026-06-19",  # Juneteenth
    "2026-07-03",  # Independence Day (observed)
    "2026-09-07",  # Labor Day
    "2026-11-26",  # Thanksgiving
    "2026-12-25",  # Christmas
}

# 한국 증시 휴장일 (2024-2026)
KR_HOLIDAYS = {
    # 2024
    "2024-01-01",  # 신정
    "2024-02-09",  # 설날 연휴
    "2024-02-10",  # 설날
    "2024-02-11",  # 설날 연휴
    "2024-02-12",  # 대체공휴일
    "2024-03-01",  # 삼일절
    "2024-04-10",  # 총선
    "2024-05-01",  # 근로자의 날
    "2024-05-06",  # 대체공휴일(어린이날)
    "2024-05-15",  # 부처님오신날
    "2024-06-06",  # 현충일
    "2024-08-15",  # 광복절
    "2024-09-16",  # 추석 연휴
    "2024-09-17",  # 추석
    "2024-09-18",  # 추석 연휴
    "2024-10-03",  # 개천절
    "2024-10-09",  # 한글날
    "2024-12-25",  # 성탄절
    "2024-12-31",  # 폐장일
    # 2025
    "2025-01-01",  # 신정
    "2025-01-28",  # 설날 연휴
    "2025-01-29",  # 설날
    "2025-01-30",  # 설날 연휴
    "2025-03-01",  # 삼일절
    "2025-03-03",  # 대체공휴일
    "2025-05-01",  # 근로자의 날
    "2025-05-05",  # 어린이날
    "2025-05-06",  # 부처님오신날
    "2025-06-06",  # 현충일
    "2025-08-15",  # 광복절
    "2025-10-03",  # 개천절
    "2025-10-05",  # 추석 연휴
    "2025-10-06",  # 추석
    "2025-10-07",  # 추석 연휴
    "2025-10-08",  # 대체공휴일
    "2025-10-09",  # 한글날
    "2025-12-25",  # 성탄절
    "2025-12-31",  # 폐장일
    # 2026
    "2026-01-01",  # 신정
    "2026-02-16",  # 설날 연휴
    "2026-02-17",  # 설날
    "2026-02-18",  # 설날 연휴
    "2026-03-01",  # 삼일절
    "2026-03-02",  # 대체공휴일
    "2026-05-01",  # 근로자의 날
    "2026-05-05",  # 어린이날
    "2026-05-24",  # 부처님오신날
    "2026-05-25",  # 대체공휴일
    "2026-06-06",  # 현충일
    "2026-08-15",  # 광복절
    "2026-08-17",  # 대체공휴일
    "2026-09-24",  # 추석 연휴
    "2026-09-25",  # 추석
    "2026-09-26",  # 추석 연휴
    "2026-10-03",  # 개천절
    "2026-10-05",  # 대체공휴일
    "2026-10-09",  # 한글날
    "2026-12-25",  # 성탄절
    "2026-12-31",  # 폐장일
}


def is_us_market_holiday(check_date: date = None) -> bool:
    """미국 증시 휴장일인지 확인"""
    if check_date is None:
        check_date = datetime.now().date()

    # 주말 체크
    if check_date.weekday() >= 5:  # 토(5), 일(6)
        return True

    # 휴장일 체크
    date_str = check_date.strftime("%Y-%m-%d")
    return date_str in US_HOLIDAYS


def is_kr_market_holiday(check_date: date = None) -> bool:
    """한국 증시 휴장일인지 확인"""
    if check_date is None:
        check_date = datetime.now().date()

    # 주말 체크
    if check_date.weekday() >= 5:  # 토(5), 일(6)
        return True

    # 휴장일 체크
    date_str = check_date.strftime("%Y-%m-%d")
    return date_str in KR_HOLIDAYS


def is_both_markets_closed(check_date: date = None) -> bool:
    """미국/한국 모두 휴장인지 확인"""
    return is_us_market_holiday(check_date) and is_kr_market_holiday(check_date)


def get_us_holidays_in_month(year: int, month: int) -> list:
    """해당 월의 미국 휴장일 목록 반환"""
    prefix = f"{year}-{month:02d}"
    return sorted([d for d in US_HOLIDAYS if d.startswith(prefix)])


def get_kr_holidays_in_month(year: int, month: int) -> list:
    """해당 월의 한국 휴장일 목록 반환"""
    prefix = f"{year}-{month:02d}"
    return sorted([d for d in KR_HOLIDAYS if d.startswith(prefix)])


def get_upcoming_holidays(days: int = 7) -> dict:
    """
    앞으로 N일 내 휴장일 반환
    Returns: {"us": [...], "kr": [...]}
    """
    from datetime import timedelta
    today = datetime.now().date()
    us_holidays = []
    kr_holidays = []

    for i in range(1, days + 1):
        check_date = today + timedelta(days=i)
        date_str = check_date.strftime("%Y-%m-%d")
        weekday = check_date.weekday()

        # 주말 제외, 공휴일만
        if weekday < 5:
            if date_str in US_HOLIDAYS:
                us_holidays.append(date_str)
            if date_str in KR_HOLIDAYS:
                kr_holidays.append(date_str)

    return {"us": us_holidays, "kr": kr_holidays}


def is_tomorrow_holiday() -> dict:
    """
    내일이 휴장일인지 확인
    Returns: {"us": bool, "kr": bool, "us_name": str, "kr_name": str}
    """
    from datetime import timedelta
    tomorrow = datetime.now().date() + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")

    return {
        "us": tomorrow_str in US_HOLIDAYS,
        "kr": tomorrow_str in KR_HOLIDAYS,
        "date": tomorrow_str
    }


def is_first_trading_day_of_week() -> bool:
    """오늘이 이번 주 첫 거래일인지 확인 (월요일 또는 월요일이 휴일이면 화요일...)"""
    today = datetime.now().date()
    weekday = today.weekday()

    # 주말이면 거래일 아님
    if weekday >= 5:
        return False

    # 월요일이면 첫 거래일
    if weekday == 0:
        return True

    # 화~금요일인 경우, 이전 날들이 모두 휴장일이면 첫 거래일
    from datetime import timedelta
    for i in range(weekday):
        check_date = today - timedelta(days=weekday - i)
        if check_date.weekday() < 5:  # 평일
            date_str = check_date.strftime("%Y-%m-%d")
            # 미국 또는 한국 중 하나라도 개장했으면 False
            if date_str not in US_HOLIDAYS or date_str not in KR_HOLIDAYS:
                return False

    return True
