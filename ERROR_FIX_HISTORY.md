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

### 4.3 main.py 누락 오류 (2026-01-27)

**에러**:
```
python: can't open file '/opt/render/project/src/main.py': [Errno 2] No such file or directory
Exited with status 2
```

**원인**:
- Render 대시보드에서 Start Command가 `python main.py`로 설정됨
- 하지만 프로젝트에 `main.py` 파일이 없었음
- `render.yaml`의 `startCommand: python python/scheduler.py`가 무시됨

**해결**:
- `main.py` 엔트리포인트 파일 생성 (커밋 `81509b9`)
- `render.yaml`도 `startCommand: python main.py`로 수정

### 4.4 배포 타임아웃 오류 (2026-01-27)

**에러**:
```
Deploy failed - Timed out
January 27, 2026 at 3:05 PM
```

**원인**:
1. Playwright 브라우저 설치 (`playwright install chromium`) 시간 초과
2. Render 무료 티어의 빌드 시간 제한
3. 무거운 의존성: numpy, pandas, matplotlib, playwright

**현재 설정**:
```yaml
# render.yaml
services:
  - type: worker
    name: telebot-scheduler
    env: python
    buildCommand: pip install -r requirements.txt && playwright install chromium
    startCommand: python main.py
```

**Render 대시보드 설정 (확인 필요)**:
- Service Type: WEB SERVICE (❌ worker여야 함)
- Build Command: ?
- Start Command: python main.py

**가능한 해결책**:

1. **Docker 이미지 사용** (권장)
   - `mcr.microsoft.com/playwright/python:v1.40.0-focal` 사용
   - Playwright가 미리 설치된 이미지

2. **Playwright 제거하고 텍스트만 사용**
   - 스크린샷 기능 제거
   - API 기반 텍스트 메시지만 발송

3. **Render 유료 티어로 업그레이드**
   - 빌드 시간 제한 없음

4. **다른 플랫폼 사용**
   - Railway, Fly.io, DigitalOcean 등

### 4.5 Service Type 불일치 (2026-01-27)

**문제**:
- `render.yaml`: `type: worker`
- Render 대시보드: WEB SERVICE

**영향**:
- render.yaml 설정이 무시될 수 있음
- WEB SERVICE는 HTTP 요청을 기대하지만, 스케줄러는 백그라운드 워커

**해결**:
- Render 대시보드에서 새 서비스를 **Background Worker**로 생성
- 또는 기존 서비스 삭제 후 render.yaml로 재생성

---

## 변경 이력

| 날짜 | 섹션 | 변경 내용 |
|------|------|----------|
| 2026-01-27 | 4.3 | main.py 누락 오류 추가 |
| 2026-01-27 | 4.4 | 배포 타임아웃 오류 추가 |
| 2026-01-27 | 4.5 | Service Type 불일치 추가 |
| 2026-01-26 | 전체 | 초기 문서 생성 |

---

> **규칙**: 새 에러 해결 시 이 문서에 추가 → 커밋 → Push
