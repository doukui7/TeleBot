# TeleBot 에러 수정 히스토리

> 반복되는 에러를 방지하기 위한 에러 수정 기록

---

## 목차

1. [텔레그램 API 관련](#1-텔레그램-api-관련)
2. [스크린샷 캡처 관련](#2-스크린샷-캡처-관련)
3. [스케줄러 관련](#3-스케줄러-관련)
4. [Render 배포 관련](#4-render-배포-관련)
5. [주가 모니터링 관련](#5-주가-모니터링-관련)

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

### 4.6 Port Scan Timeout 오류 (2026-01-27)

**에러**:
```
==> Timed Out
Port scan timeout reached, no open ports detected.
Bind your service to at least one port.
```

**원인**:
- Web Service는 HTTP 포트를 열어야 함
- 스케줄러가 포트를 바인딩하지 않음

**해결**:
- `main.py`에 aiohttp 웹 서버 추가 (커밋 `064a074`)
- `PORT` 환경변수로 포트 바인딩
- Health check 엔드포인트: `/`, `/health`

```python
from aiohttp import web

app = web.Application()
app.router.add_get('/', health_check)
port = int(os.environ.get('PORT', 10000))
```

### 2.4 CNN Fear & Greed 동의 팝업 (2026-01-28)

**문제**: CNN 페이지에 "Legal Terms and Privacy" 동의 팝업이 스크린샷을 가림

**시도한 방법들**:

1. **Playwright 버튼 클릭** (실패)
   ```python
   agree_button = page.locator('button:has-text("Agree")')
   if await agree_button.is_visible(timeout=3000):
       await agree_button.click()
   ```
   - 버튼을 찾지 못함

2. **다양한 selector 시도** (실패)
   ```python
   selectors = [
       'button:has-text("Agree")',
       'button:text-is("Agree")',
       '[data-testid="agree-button"]',
       '.cnn-consent button',
   ]
   ```

3. **JavaScript 직접 클릭** (실패)
   ```javascript
   const buttons = document.querySelectorAll('button');
   for (const btn of buttons) {
       if (btn.textContent.trim() === 'Agree') {
           btn.click();
       }
   }
   ```

4. **동의 팝업 코드 제거** (최종 해결 - 2026-01-28)
   - 실제로 팝업이 표시되지 않음을 확인
   - 불필요한 팝업 처리 코드 전체 삭제
   - width: 1020으로 복원 (전체 영역 캡처)

**최종 캡처 좌표**: `clip={'x': 20, 'y': 480, 'width': 1020, 'height': 620}`

**파일**: `python/fear_greed_tracker.py`

**커밋**: `0406586` - fix: 스크린샷 캡처 좌표 최적화 및 알림 30분 간격 추가

### 2.5 네이버 증시 캡처 좌표 최적화 (2026-01-28)

**문제**: 광고/레이아웃 변경으로 캡처 영역이 맞지 않음

**해결**: 좌표 기반 캡처로 변경

**미국 증시 (다우/나스닥/S&P)**:
```python
clip={'x': 128, 'y': 245, 'width': 920, 'height': 240}
```

**한국 증시 (코스피/코스닥)**:
```python
clip={'x': 128, 'y': 245, 'width': 850, 'height': 240}
```

**viewport**: `{'width': 1400, 'height': 1200}`

**파일**: `python/fear_greed_tracker.py`

### 3.5 주가 알림 최소 30분 간격 (2026-01-28)

**문제**: 연속 알림 발송으로 채널 스팸화

**해결**: 알림 발송 후 30분간 추가 발송 차단

```python
MIN_ALERT_INTERVAL_SECONDS = 30 * 60

# check_stock_alerts 내부
if self.last_alert_time:
    elapsed = (now - self.last_alert_time).total_seconds()
    if elapsed < MIN_ALERT_INTERVAL_SECONDS:
        return  # 30분 미경과 시 발송 안함
```

**파일**: `python/scheduler.py`

### 3.3 시작 시 테스트 브리핑 중복 발송 (2026-01-28)

**문제**: Render 재시작마다 Fear & Greed + 세계 증시 스크린샷 발송

**원인**: `main.py`에 시작 시 테스트 브리핑 코드
```python
# 테스트 브리핑 발송 (시작 시 1회)
await send_test_briefing()
```

**해결**: 테스트 코드 주석 처리
```python
# 테스트 브리핑 비활성화 (Render 재시작마다 중복 발송 방지)
# await send_test_briefing()
```

**파일**: `main.py`

---

### 3.4 중복 알림 발송 문제 (2026-01-28)

**문제**: 같은 종목 알림이 반복 발송됨

**원인 1**: Upstash Redis 환경변수명 불일치
- Upstash 제공: `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`
- 코드에서 사용: `UPSTASH_REDIS_URL`, `UPSTASH_REDIS_TOKEN`
- Redis 연결 실패 → 인메모리 폴백 → Render 재시작 시 초기화

**해결**:
```python
# config.py
UPSTASH_REDIS_URL = os.getenv('UPSTASH_REDIS_REST_URL') or os.getenv('UPSTASH_REDIS_URL')
UPSTASH_REDIS_TOKEN = os.getenv('UPSTASH_REDIS_REST_TOKEN') or os.getenv('UPSTASH_REDIS_TOKEN')
```

**원인 2**: 파일 저장 타이밍
- 알림 기록이 마지막에 한 번만 파일에 저장됨
- 중간에 오류 발생 시 기록 손실

**해결**: 매 알림마다 즉시 파일 저장
```python
def _save_alert_record(self, symbol: str, level: int):
    # ... 기존 코드 ...
    # 즉시 파일에 저장 (Redis 미사용 시)
    if not redis_client:
        self._save_alert_history()
```

**파일**: `python/config.py`, `python/scheduler.py`

---

## 5. 주가 모니터링 관련

### 5.1 가격 변동률 계산 오류 (2026-01-28)

**문제**: 5% 이상 변동 종목이 있는데 알림이 오지 않음

**원인**: Yahoo Finance API의 closes 배열 해석 오류

**상세 분석**:
- `range=5d` 쿼리 시 closes 배열에 5일치 데이터 반환
- **장중**: `closes[-1]`은 오늘 종가(실시간 업데이트중)
- **프리/애프터**: `closes[-1]`은 어제 종가
- 기존 코드: 모든 상황에서 `closes[-1]`을 전일 종가로 사용
- 결과: 장중에 현재가와 전일종가가 같아서 변동률 0%

**Yahoo Finance API 데이터 예시**:
```python
# range=5d 요청 시 (장중)
closes = [
    247.64,   # 01-21
    248.35,   # 01-22
    248.04,   # 01-23
    255.41,   # 01-26 (어제)
    259.65    # 01-28 (오늘 - 실시간)
]
# closes[-1] = 오늘 가격 (현재가와 동일)
# closes[-2] = 어제 종가 (실제 전일종가)
```

**해결**: `marketState` 기반 시간대별 분기 처리

```python
market_state = meta.get("marketState")  # REGULAR, PRE, POST, CLOSED

if market_state == "REGULAR":
    # 장중: 현재가=regularMarketPrice, 전일종가=closes[-2]
    current_price = regular_price
    previous_close = valid_closes[-2]

elif market_state == "PRE":
    # 프리마켓: 현재가=preMarketPrice, 전일종가=closes[-1]
    current_price = pre_market_price or regular_price
    previous_close = valid_closes[-1]

elif market_state == "POST":
    # 애프터마켓: 현재가=postMarketPrice, 전일종가=closes[-1]
    current_price = post_market_price or regular_price
    previous_close = valid_closes[-1]

else:  # CLOSED/UNKNOWN
    # closes[-1]이 오늘 종가일 수 있으므로 closes[-2] 사용
    current_price = regular_price
    previous_close = valid_closes[-2]
```

**파일**: `python/stock_monitor.py` (get_price_data 메서드)

**커밋**: `fix: 시간대별 가격 변동률 계산 로직 수정`

---

## 변경 이력

| 날짜 | 섹션 | 변경 내용 |
|------|------|----------|
| 2026-01-28 | 2.4 | CNN Fear & Greed 팝업 코드 제거, width 1020 복원 |
| 2026-01-28 | 2.5 | 네이버 증시 캡처 좌표 최적화 추가 |
| 2026-01-28 | 3.5 | 주가 알림 최소 30분 간격 추가 |
| 2026-01-28 | 3.3 | 시작 시 테스트 브리핑 중복 발송 추가 |
| 2026-01-28 | 3.4 | 중복 알림 문제 (Redis 변수명, 파일저장) 추가 |
| 2026-01-28 | 5.1 | 가격 변동률 계산 오류 (시간대별 분기) 추가 |
| 2026-01-27 | 4.6 | Port Scan Timeout 오류 추가 |
| 2026-01-27 | 4.3 | main.py 누락 오류 추가 |
| 2026-01-27 | 4.4 | 배포 타임아웃 오류 추가 |
| 2026-01-27 | 4.5 | Service Type 불일치 추가 |
| 2026-01-26 | 전체 | 초기 문서 생성 |

---

> **규칙**: 새 에러 해결 시 이 문서에 추가 → 커밋 → Push
