# TeleBot 텔레그램 발송 계획

> 최종 업데이트: 2026-01-28

---

## 1. 현재 상태

### 활성화된 기능
- **주가 변동 알림** - 5분마다 체크
- **오전 브리핑** - 08:00 KST (평일)
  - Fear & Greed 스크린샷
  - 미국 증시 스크린샷
- **오후 브리핑** - 15:30 KST (평일)
  - 한국 증시 스크린샷

### 비활성화된 기능
- 시장 차트 발송 (별도 요청 시 활성화)

---

## 2. 주가 변동 알림

### 체크 주기
- **평일**: 5분마다 (`STOCK_CHECK_INTERVAL`)
- **주말**: 5분마다 (나스닥 선물 + 비트코인만)

### 알림 임계값

| 카테고리 | 최소 임계값 | 알림 레벨 |
|----------|-------------|-----------|
| 지수 (index) | 2% 이상 | 2%, 3%, 4%... |
| 암호화폐 (crypto) | 2% 이상 | 2%, 3%, 4%... |
| 개별주/ETF | 5% 이상 | 5%, 10%, 15%... |

### 중복 방지

| 조건 | 설명 |
|------|------|
| 24시간 쿨다운 | 같은 종목/레벨 조합은 24시간 내 재알림 안함 |
| 30분 최소 간격 | 연속 알림 발송 방지 |

### 저장소
- **Primary**: Upstash Redis (24시간 TTL)
- **Fallback**: 로컬 JSON 파일 (`data/alert_history.json`)

---

## 3. 스크린샷 캡처 설정

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

### 지수 (2% 이상 변동 시 알림)
| 심볼 | 이름 | 비고 |
|------|------|------|
| ^KS11 | 코스피 (KOSPI) | 한국장 시간만 |
| ^KQ11 | 코스닥 (KOSDAQ) | 한국장 시간만 |
| ^IXIC | 나스닥 (NASDAQ) | 미국장 시간 |
| ^GSPC | S&P 500 | 미국장 시간 |
| NQ=F | 나스닥 선물 | 주말에도 체크 |

### 암호화폐 (2% 이상 변동 시 알림)
| 심볼 | 이름 | 비고 |
|------|------|------|
| BTC-USD | 비트코인 (Bitcoin) | 24시간 체크 |

### 환율
| 심볼 | 이름 |
|------|------|
| KRW=X | 원/달러 환율 |

### 3x 레버리지 ETF (5% 이상 변동 시 알림)
| 심볼 | 이름 |
|------|------|
| TQQQ | 나스닥 3배 |
| UPRO | S&P 3배 |
| SOXL | 반도체 3배 |
| LABU | 바이오 3배 |
| TNA | 소형주 3배 |
| FAS | 금융 3배 |
| TECL | 기술 3배 |
| FNGU | 빅테크 3배 |

> ⚠️ 인버스 ETF (SQQQ, SOXS, UVXY 등)는 모니터링 제외

### S&P 100 개별주 (5% 이상 변동 시 알림)

**Technology (16종목)**
AAPL, MSFT, GOOGL, NVDA, META, AVGO, CSCO, ADBE, CRM, ORCL, ACN, IBM, INTC, AMD, QCOM, TXN

**Consumer (16종목)**
AMZN, TSLA, HD, MCD, NKE, SBUX, LOW, TGT, COST, WMT, PG, KO, PEP, MDLZ, CL, KHC

**Communication (7종목)**
NFLX, DIS, CMCSA, CHTR, T, VZ, TMUS

**Healthcare (14종목)**
UNH, JNJ, LLY, MRK, ABBV, PFE, TMO, ABT, DHR, BMY, AMGN, GILD, MDT, CVS

**Financial (18종목)**
BRK-B, JPM, V, MA, BAC, WFC, GS, MS, C, SCHW, BLK, AXP, BK, USB, COF, MET, AIG, SPG

**Industrial (12종목)**
BA, HON, UNP, RTX, CAT, GE, LMT, GD, UPS, FDX, EMR, MMM

**Energy (3종목)**
XOM, CVX, COP

**Utilities (4종목)**
NEE, DUK, SO, EXC

**기타 (9종목)**
LIN, DOW, AMT, BKNG, GM, F, PM, MO, WBA

---

## 5. 향후 계획

### Phase 1: 안정화 (완료)
- [x] 주가 변동 알림 운영
- [x] 중복 알림 방지 (Redis + 30분 간격)
- [x] 스크린샷 캡처 좌표 최적화

### Phase 2: 브리핑 활성화 (완료)
- [x] 오전 브리핑 (08:00 KST, 평일)
  - Fear & Greed 스크린샷
  - 미국 증시 스크린샷
- [x] 오후 브리핑 (15:30 KST, 평일)
  - 한국 증시 스크린샷

### Phase 3: 고급 기능 (미정)
- [ ] 뉴스 자동 발송
- [ ] 실적 발표 알림
- [ ] 배당락일 알림

### Phase 4: 배당주 전용 채널 (계획)

별도 텔레그램 채널을 생성하여 배당 투자자를 위한 정보만 집중 발송

#### 채널 구성
| 항목 | 내용 |
|------|------|
| 채널명 | (미정) 배당주 알리미 |
| 환경변수 | `DIVIDEND_CHANNEL_ID` |

#### 발송 내용

**1. 매일 시장 브리핑 (기존과 동일)**
- 오전 08:00: Fear & Greed + 미국 증시
- 오후 15:30: 한국 증시

**2. 배당 ETF 모니터링**
| 심볼 | 이름 | 설명 |
|------|------|------|
| SCHD | Schwab US Dividend Equity | 미국 고배당 ETF |
| VYM | Vanguard High Dividend Yield | 뱅가드 고배당 |
| HDV | iShares Core High Dividend | 아이셰어즈 고배당 |
| JEPI | JPMorgan Equity Premium Income | 커버드콜 전략 |
| JEPQ | JPMorgan Nasdaq Equity Premium | 나스닥 커버드콜 |
| QYLD | Global X NASDAQ 100 Covered Call | 나스닥 커버드콜 |
| DIVO | Amplify CWP Enhanced Dividend | 배당성장 |

**3. 배당 귀족주 (Dividend Aristocrats)**
25년 이상 연속 배당 증가 종목
- JNJ, PG, KO, PEP, MCD, MMM, ABT, ABBV, XOM, CVX 등

**4. 배당 관련 알림**
- 배당락일 (Ex-Dividend Date) 알림
- 배당금 지급일 알림
- 배당 증가/감소 뉴스
- 실적 발표 (배당주 한정)

**5. 주간 배당 리포트**
- 매주 금요일: 다음 주 배당락일 종목 리스트
- 월간: 배당 수익률 상위 종목

#### 데이터 소스 (검토 필요)
- Yahoo Finance API: 배당 정보
- Seeking Alpha / Dividend.com: 배당 캘린더
- 뉴스 API: 배당 관련 뉴스 필터링

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
| 2026-01-28 | 배당주 전용 채널 계획 추가 (Phase 4) |
| 2026-01-28 | 오전/오후 브리핑 재활성화 |
| 2026-01-28 | 모니터링 종목 목록 실제 코드와 동기화 |
| 2026-01-28 | 스크린샷 캡처 좌표 최적화 |
| 2026-01-28 | 주가 알림 30분 최소 간격 추가 |
| 2026-01-27 | Render 배포 완료 |
| 2026-01-26 | 초기 구축 |
