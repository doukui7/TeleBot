# TeleBot 텔레그램 발송 계획

> 최종 업데이트: 2026-01-28

---

## 1. 현재 상태

### 활성화된 기능
- **주가 변동 알림** - 5분마다 체크

### 비활성화된 기능 (2026-01-28)
- 오전/오후 브리핑
- Fear & Greed 스크린샷
- 네이버 증시 스크린샷
- 시장 차트 발송

---

## 2. 주가 변동 알림

### 체크 주기
- **평일**: 5분마다 (`STOCK_CHECK_INTERVAL`)
- **주말**: 5분마다 (나스닥 선물 + 비트코인만)

### 알림 임계값

| 카테고리 | 임계값 | 예시 |
|----------|--------|------|
| 지수 (index) | 1% 단위 | 1%, 2%, 3%... |
| 암호화폐 (crypto) | 1% 단위 | 1%, 2%, 3%... |
| 개별주/ETF | 5% 단위 | 5%, 10%, 15%... |

### 중복 방지

| 조건 | 설명 |
|------|------|
| 24시간 쿨다운 | 같은 종목/레벨 조합은 24시간 내 재알림 안함 |
| 30분 최소 간격 | 연속 알림 발송 방지 |

### 저장소
- **Primary**: Upstash Redis (24시간 TTL)
- **Fallback**: 로컬 JSON 파일 (`data/alert_history.json`)

---

## 3. 스크린샷 캡처 설정 (비활성화 상태)

### CNN Fear & Greed
```python
url: https://edition.cnn.com/markets/fear-and-greed
clip: {'x': 20, 'y': 480, 'width': 1020, 'height': 620}
viewport: {'width': 1400, 'height': 1200}
```

### 네이버 미국 증시
```python
url: https://stock.naver.com/market/stock/usa
clip: {'x': 128, 'y': 245, 'width': 920, 'height': 240}
viewport: {'width': 1400, 'height': 1200}
```

### 네이버 한국 증시
```python
url: https://stock.naver.com/market/stock/kr
clip: {'x': 128, 'y': 245, 'width': 850, 'height': 240}
viewport: {'width': 1400, 'height': 1200}
```

---

## 4. 모니터링 종목

### 지수 (1% 단위 알림)
- 나스닥 종합 (^IXIC)
- S&P 500 (^GSPC)
- 다우존스 (^DJI)
- 나스닥 100 (^NDX)
- 필라델피아 반도체 (^SOX)

### 암호화폐 (1% 단위 알림)
- 비트코인 (BTC-USD)

### 레버리지 ETF (5% 단위 알림)
- TQQQ (나스닥 3배)
- SQQQ (나스닥 -3배)
- SOXL (반도체 3배)
- SOXS (반도체 -3배)
- UVXY (VIX 1.5배)

### 개별 종목 (5% 단위 알림)
- NVDA (엔비디아)
- TSLA (테슬라)

---

## 5. 향후 계획

### Phase 1: 안정화 (현재)
- [x] 주가 변동 알림만 운영
- [x] 중복 알림 방지 (Redis + 30분 간격)
- [x] 스크린샷 캡처 좌표 최적화

### Phase 2: 브리핑 재활성화 (예정)
- [ ] 오전 브리핑 (08:00 KST)
  - Fear & Greed 스크린샷
  - 전일 미국 증시 요약
- [ ] 오후 브리핑 (15:30 KST)
  - 한국 증시 마감 요약
  - 미국 프리마켓 현황

### Phase 3: 고급 기능 (미정)
- [ ] 뉴스 자동 발송
- [ ] 실적 발표 알림
- [ ] 배당락일 알림

---

## 6. 환경 변수

| 변수명 | 설명 |
|--------|------|
| `TELEGRAM_BOT_TOKEN` | 텔레그램 봇 토큰 |
| `CHANNEL_ID` | 발송 대상 채널 ID |
| `STOCK_CHECK_INTERVAL` | 주가 체크 간격 (초) |
| `UPSTASH_REDIS_REST_URL` | Redis URL |
| `UPSTASH_REDIS_REST_TOKEN` | Redis 토큰 |

---

## 7. 배포

- **플랫폼**: Render (Web Service)
- **포트**: 10000
- **헬스체크**: `/health`

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-01-28 | 스크린샷 캡처 좌표 최적화 |
| 2026-01-28 | 주가 알림 30분 최소 간격 추가 |
| 2026-01-28 | 모든 브리핑/스크린샷 비활성화 |
| 2026-01-27 | Render 배포 완료 |
| 2026-01-26 | 초기 구축 |
