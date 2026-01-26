# TeleBot 에러 수정 히스토리

> 반복되는 에러를 방지하기 위한 에러 수정 기록

---

## 목차

1. [텔레그램 API 관련](#1-텔레그램-api-관련)
2. [스크린샷 캡처 관련](#2-스크린샷-캡처-관련)
3. [스케줄러 관련](#3-스케줄러-관련)
4. [Render 배포 관련](#4-render-배포-관련)

---

## 1. 텔레그램 API 관련

### 1.1 Bot Token 환경변수

**에러**: `telegram.error.InvalidToken`

**원인**: 환경변수에서 Bot Token을 올바르게 읽지 못함

**해결**:
```python
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
```

**주의**: `.env` 파일에 공백 없이 토큰 입력

---

## 2. 스크린샷 캡처 관련

### 2.1 Playwright 초기화

**에러**: `playwright._impl._errors.Error: Browser closed`

**원인**: 비동기 컨텍스트에서 브라우저 관리 실패

**해결**:
```python
from playwright.async_api import async_playwright

async def capture_screenshot():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # ... 작업
        await browser.close()
```

### 2.2 CNN Fear & Greed 캡처

**에러**: 요소를 찾을 수 없음

**원인**: 페이지 로딩 전 캡처 시도

**해결**:
```python
await page.wait_for_selector('.market-fng-gauge', timeout=30000)
await page.wait_for_timeout(2000)  # 추가 대기
```

### 2.3 네이버 증권 캡처

**에러**: 로그인 필요 또는 봇 차단

**해결**: User-Agent 설정 및 헤더 추가
```python
await page.set_extra_http_headers({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...'
})
```

---

## 3. 스케줄러 관련

### 3.1 APScheduler 타임존

**에러**: 스케줄 시간이 맞지 않음

**원인**: 서버와 로컬 타임존 차이

**해결**:
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone

scheduler = AsyncIOScheduler(timezone=timezone('Asia/Seoul'))
```

### 3.2 미국 휴장일 체크

**문제**: 휴장일에도 브리핑 발송

**해결**: `market_holidays.py` 사용
```python
from src.market_holidays import is_us_market_holiday

if not is_us_market_holiday():
    await send_briefing()
```

---

## 4. Render 배포 관련

### 4.1 빌드 실패

**에러**: `Exited with status 1`

**원인**: 잘못된 레포지토리 연결 또는 종속성 문제

**해결**:
1. Render 대시보드 → Settings → Repository 확인
2. `requirements.txt` 종속성 확인
3. Python 버전 확인 (`runtime.txt`)

### 4.2 Playwright 설치

**에러**: Render에서 Playwright 브라우저 없음

**해결**: `render.yaml`에 빌드 명령 추가
```yaml
buildCommand: pip install -r requirements.txt && playwright install chromium --with-deps
```

---

## 변경 이력

| 날짜 | 섹션 | 변경 내용 |
|------|------|----------|
| 2025-01-26 | 전체 | 초기 문서 생성 |

---

> **규칙**: 새 에러 해결 시 이 문서에 추가 → 커밋 → Push
