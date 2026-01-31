# TeleBot 발송 메시지 정리 (3X ETF 전용)

> 최종 업데이트: 2026-01-31
> 지수 발송 제거 완료 - 3X ETF만 발송

---

## 📋 발송 메시지 구조

### 1. 오전 브리핑 (미국 장 마감 후 10분, 평일)

**메인 채널만 발송** (배당채널: Fear & Greed + 미국 증시만)

#### 1-1. Fear & Greed Index (텍스트)
- **출처**: CNN Fear & Greed API
- **형식**: 텍스트 메시지
- **내용**: 현재 Fear & Greed 지수값 및 설명
- **예시**:
  ```
  😱 Fear & Greed Index
  Current: 35 (Fear)
  Previous: 38 (Fear)
  ```

#### 1-2. 미국 증시 정보 (텍스트)
- **출처**: Naver Finance Tracker (웹 스크래핑)
- **형식**: 텍스트 메시지
- **내용**: 나스닥, S&P500, 비트코인 등 주요 지수 현황
- **예시**:
  ```
  🌍 미국 증시
  나스닥: 19,521.41 (+0.23%)
  S&P500: 5,930.10 (+0.15%)
  ```

#### 1-3. 3X ETF 리스트 (텍스트) ✅ 핵심 - **메인채널만**
- **출처**: ETFTracker (`etf_tracker.py`)
- **형식**: 텍스트 메시지 (monospace 포맷)
- **내용**: 3배 레버리지 ETF 가격 정보
- **발송대상**: 메인 채널만 (배당채널 제외)
- **표시 항목**:
  | 항목 | 설명 |
  |------|------|
  | ETF | 심볼 (TQQQ, UPRO, SOXL 등) |
  | Daily | 일일 변동률 (%) |
  | Price | 현재 가격 ($) |
  | YTD | 연초 이후 수익률 (%) |
  | MTD | 월초 이후 수익률 (%) |
  | 52W High | 52주 최고가 ($) |
  | vs Low | 52주 저가 대비 수익률 (%) |

- **예시**:
  ```
  3X ETF List - 2026-01-31 14:30:00
  ETF      Daily      Price     YTD      MTD   52W High    vs Low
  TQQQ     +1.25%  $ 28.45     +15.30%  +2.10%  $ 32.10    +5.20%
  UPRO     +0.85%  $ 42.15     +12.80%  +1.50%  $ 48.50    +3.80%
  SOXL     +1.50%  $ 35.60     +18.90%  +3.20%  $ 40.20    +7.10%
  ...
  ```

---

### 2. 오후 브리핑 (한국 장 마감 후 10분, 15:40 KST)

**메인 채널 + 배당채널 동시 발송**

#### 2-1. 한국 증시 정보 (텍스트)
- **출처**: Naver Finance Tracker (웹 스크래핑)
- **형식**: 텍스트 메시지
- **내용**: 코스피, 코스닥 등 한국 증시 현황
- **예시**:
  ```
  🇰🇷 한국 증시
  코스피: 2,650.45 (-0.15%)
  코스닥: 825.30 (+0.25%)
  ```

---

### 3. 주가 변동 알림 (5분마다, 상시)

**메인 채널만 발송**

#### 3-1. 3X ETF 가격 변동 알림
- **출처**: ETFTracker (`etf_tracker.py`)
- **형식**: 텍스트 메시지
- **조건**: 전일 종가 대비 5% 이상 변동
- **임계값**:
  - 첫 알림: 5% 이상
  - 2차 알림: 10% 이상
  - 3차 알림: 15% 이상 (누적)
- **중복 방지**: 
  - 같은 종목/레벨 조합 24시간 쿨다운
  - 30분 최소 간격 (연속 알림 방지)
- **예시**:
  ```
  📈 Alert: TQQQ +5.25%
  Current: $28.45 | Change: +$1.40 from yesterday
  
  ⚠️ Multiple alerts today - watch momentum!
  ```

---

### 4. 배당 브리핑 (09:00 KST, 평일) - 배당채널 전용

**배당채널만 발송**

#### 4-1. 배당주 리포트
- **출처**: DividendMonitor (`dividend_monitor.py`)
- **형식**: 텍스트 메시지
- **내용**: 배당 ETF 현황 및 예정 배당 정보

---

### 5. 배당 ETF 가격 변동 알림 (5분마다, 상시) - 배당채널 전용

**배당채널만 발송**

#### 5-1. 배당 ETF 가격 변동
- **출처**: StockMonitor (`stock_monitor.py`)
- **형식**: 텍스트 메시지
- **모니터링 종목**: SCHD, VYM, HDV, JEPI, JEPQ, DIVO, O
- **조건**: 전일 종가 대비 5% 이상 변동

---

## 📊 발송 채널 구분

| 채널 | 용도 | 발송 내용 |
|------|------|----------|
| **메인 채널** | 일반 투자자 | • 3X ETF 리스트 (미국 장 마감 후 10분)<br>• 3X ETF 가격 변동 알림 (상시)<br>• Fear & Greed (미국 장 마감 후 10분)<br>• 미국/한국 증시 (미국 장 마감 후 10분 / 15:40) |
| **배당채널** | 배당 투자자 | • Fear & Greed (미국 장 마감 후 10분)<br>• 미국 증시 (미국 장 마감 후 10분)<br>• 한국 증시 (15:40)<br>• 배당 브리핑 (09:00)<br>• 배당 ETF 가격 변동 알림 (상시)<br>• ~~3X ETF 리스트~~ (제거됨) |

---

## 🗂️ 발송 메시지 생성 함수

### advanced_etf_table_generator.py

```python
class AdvancedETFTableGenerator:
    
    @staticmethod
    def create_etf_message(etf_data: List[Dict]) -> str:
        """
        3X ETF 메시지 생성 (오전 브리핑용)
        Returns: 포맷된 ETF 리스트 메시지
        """
    
    @staticmethod
    def create_price_change_message(etf_data: List[Dict]) -> str:
        """
        ETF 가격 변동 메시지 생성 (가격 변동 알림용)
        Returns: 상승/하락 ETF 랭킹 메시지
        """
```

### etf_tracker.py

```python
class ETFTracker:
    
    def get_all_etf_data(self) -> List[Dict]:
        """3X ETF 데이터 수집 (Yahoo Finance)"""
    
    def format_etf_report(self, etf_data: List[Dict]) -> str:
        """ETF 리포트 포맷팅"""
```

### scheduler.py

```python
class NewsScheduler:
    
    async def send_morning_briefing(self, force: bool = False):
        """
        오전 브리핑 (미국 장 마감 후 10분, 화~토 = 미국 월~금)
        메인채널: Fear & Greed + 미국 증시 + 3X ETF
        배당채널: Fear & Greed + 미국 증시 (3X ETF 제외)
        """
    
    async def send_afternoon_briefing(self, force: bool = False):
        """
        오후 브리핑 (한국 장 마감 후 10분, 15:40 KST, 월~금)
        메인채널 + 배당채널: 한국 증시
        """
    
    async def send_dividend_briefing(self, force: bool = False):
        """
        배당 브리핑 (09:00 KST)
        1. 배당 리포트 텍스트
        → 배당채널만 발송
        """
    
    async def _check_dividend_stocks(self):
        """
        배당 ETF 가격 변동 체크 (5분마다)
        → 배당채널만 발송
        """
```

---

## 🔄 모니터링 종목

### 3X 레버리지 ETF (메인 + 배당채널)
```
TQQQ   - Invesco QQQ Trust 3x
UPRO   - ProShares UltraPro S&P 500
SOXL   - Direxion Daily Semiconductor 3x
LABU   - Direxion Daily Biotechnology 3x
TNA    - Direxion Daily Small Cap 3x
FAS    - Direxion Daily Financial 3x
TECL   - Direxion Daily Technology 3x
FNGU   - Direxion Daily FAANG 3x
```

### 배당 ETF (배당채널 전용)
```
SCHD   - Schwab US Dividend Equity
VYM    - Vanguard High Dividend Yield
HDV    - iShares Core High Dividend
JEPI   - JPMorgan Equity Premium Income
JEPQ   - JPMorgan Nasdaq Equity Premium
DIVO   - Amplify CWP Enhanced Dividend
O      - Realty Income (월배당)
```

---

## 📝 변경 사항 (2026-01-31)

### 배당채널
- ✅ 3X ETF 리스트 제거 (배당채널에서만)
- ✅ Fear & Greed + 미국 증시만 발송

### 발송 시간
- ✅ 미국 장 마감 후 10분으로 변경 (이전: 08:00)
  - 서머타임: 05:10 KST
  - 일반: 06:10 KST
- ✅ 한국 장 마감 후 10분 명시 (15:40 KST)

---

## 📝 이전 변경 사항 (2026-01-30)

### 제거됨
- ~~지수 데이터 (나스닥, S&P500, 코스피, 코스닥, SOXX, 비트코인)~~ → Fear & Greed로 대체
- ~~`MarketIndexTracker` 클래스 사용~~ 
- ~~`create_combined_etf_style_message()` 함수~~ (지수 포함 메시지)

### 유지됨
- ✅ 3X ETF 리스트 (메인채널만)
- ✅ 3X ETF 가격 변동 알림 (상시)
- ✅ Fear & Greed Index
- ✅ 미국/한국 증시 정보
- ✅ 배당 브리핑 시스템

### 수정됨
- `send_charts.py`: 지수 제거, 3X ETF만 발송
- `advanced_etf_table_generator.py`: 불필요한 함수 제거, 주석 추가

---

## 🎯 발송 일정

| 시간 | 내용 | 채널 | 요일 |
|------|------|------|------|
| **미국 장 마감 후 10분** | Fear & Greed + 미국 증시 + 3X ETF | 메인 + 배당 (3X ETF는 메인만) | 화~토 = 미국 월~금 |
| **15:40** | 한국 증시 | 메인 + 배당 | 월~금 |
| **상시** | 3X ETF 가격 변동 알림 (5% 이상) | 메인 | 모든 시간 |
| **상시** | 배당 ETF 가격 변동 알림 (5% 이상) | 배당채널 | 모든 시간 |

---

## 🛠️ 사용 명령어

### 수동 트리거
```bash
# 오전 브리핑 즉시 발송
curl http://localhost:10000/trigger/morning

# 오후 브리핑 즉시 발송
curl http://localhost:10000/trigger/afternoon

# 배당 브리핑 즉시 발송
curl http://localhost:10000/trigger/dividend

# Fear & Greed만 발송
curl http://localhost:10000/trigger/fg
```

### 차트 이미지 발송
```bash
# send_charts.py 실행 (3X ETF 차트 + 리스트)
python send_charts.py
```

---

## ✅ 체크리스트

- [x] 지수 발송 제거 (`send_charts.py`)
- [x] `advanced_etf_table_generator` 정리
- [x] `create_combined_etf_style_message` 함수 제거
- [x] ETF 관련 함수만 유지
- [x] 3X ETF 리스트 메시지 확인
- [x] 배당 ETF 모니터링 유지
- [x] 메시지 구조 문서화

