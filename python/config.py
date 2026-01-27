"""
설정 관리 모듈
"""
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz

# .env 파일 로드
load_dotenv()

# Telegram 설정
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# 뉴스 API 설정
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
NEWS_CATEGORY = os.getenv('NEWS_CATEGORY', 'business')

# Upstash Redis 설정 (알림 기록 영구 저장용)
# Upstash에서 제공하는 변수명: UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN
UPSTASH_REDIS_URL = os.getenv('UPSTASH_REDIS_REST_URL') or os.getenv('UPSTASH_REDIS_URL')
UPSTASH_REDIS_TOKEN = os.getenv('UPSTASH_REDIS_REST_TOKEN') or os.getenv('UPSTASH_REDIS_TOKEN')

# 업데이트 간격 (초)
UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', '3600'))

# 주가 모니터링 간격 (초) - 기본 5분
STOCK_CHECK_INTERVAL = int(os.getenv('STOCK_CHECK_INTERVAL', '300'))

# 미국 시장 장 마감 시간 자동 설정 (서머타임 고려)
def get_us_market_close_time_kst():
    """
    미국 시장 장 마감 시간을 한국 시간으로 변환
    일반: EST 16:00 → KST 06:00 (다음날)
    서머: EDT 16:00 → KST 05:00 (다음날)
    """
    ny_tz = pytz.timezone('America/New_York')
    now = datetime.now(ny_tz)
    
    # 서머타임 확인
    is_dst = bool(now.dst())
    
    # 서머타임 기간: EDT 16:00 → KST 05:00
    # 일반 기간: EST 16:00 → KST 06:00
    if is_dst:
        return (5, 0)  # 다음날 05:00 KST
    else:
        return (6, 0)  # 다음날 06:00 KST

# ETF 리포트 발송 시간
ETF_REPORT_HOUR, ETF_REPORT_MINUTE = get_us_market_close_time_kst()

# 검증
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN이 설정되지 않았습니다")
if not CHANNEL_ID:
    raise ValueError("CHANNEL_ID가 설정되지 않았습니다")
# NEWS_API_KEY는 선택적 (Google News RSS 사용시 불필요)
