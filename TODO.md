# TeleBot - TODO & DONE List

> 프로젝트 작업 관리 문서

---

## 📋 TODO (예정 작업)

### 🔴 높은 우선순위

| ID | 작업 | 상태 | 담당 | 비고 |
|----|------|------|------|------|
| TB-001 | Render 배포 설정 확인 | 대기 | - | render.yaml 적용 |
| TB-002 | Playwright 스크린샷 테스트 | 대기 | - | CNN, 네이버 캡처 |
| TB-003 | 릴리즈 실패 원인 확인 | 대기 | - | GitHub Actions |

### 🟡 중간 우선순위

| ID | 작업 | 상태 | 담당 | 비고 |
|----|------|------|------|------|
| TB-010 | 7시 브리핑 실시간 스크린샷 적용 | 대기 | - | Playwright 설정 후 |
| TB-011 | TQ버스 알림 기능 테스트 | 대기 | - | 193일선 크로스오버 |
| TB-012 | ETF 리포트 포맷 개선 | 대기 | - | - |

### 🟢 낮은 우선순위

| ID | 작업 | 상태 | 담당 | 비고 |
|----|------|------|------|------|
| TB-020 | 사용자별 알림 설정 | 대기 | - | Supabase 연동 |
| TB-021 | 명령어 인터페이스 추가 | 대기 | - | /briefing, /alert |

---

## ✅ DONE (완료된 작업)

### 2025-01-26

| ID | 작업 | 완료일 | 커밋 |
|----|------|--------|------|
| TB-D001 | 독립 프로젝트로 분리 | 2025-01-26 | `017e0a8` |
| TB-D002 | 유틸리티 스크립트 추가 | 2025-01-26 | `65b2b60` |
| TB-D003 | GIT_SYNC_LOG.md 생성 | 2025-01-26 | `ba62602` |
| TB-D004 | ERROR_FIX_HISTORY.md 생성 | 2025-01-26 | `ba62602` |
| TB-D005 | Python 스케줄러 모듈 통합 | 2025-01-26 | `61f63fd` |
| TB-D006 | requirements.txt 생성 | 2025-01-26 | `61f63fd` |
| TB-D007 | render.yaml 설정 추가 | 2025-01-26 | `61f63fd` |

---

## 📊 통계

| 항목 | 수량 |
|------|------|
| TODO (높음) | 3 |
| TODO (중간) | 3 |
| TODO (낮음) | 2 |
| DONE | 7 |

---

## 스크린샷 캡처 관련

### 현재 상태
- **CNN Fear & Greed**: Playwright 캡처 시도 → 실패 시 Matplotlib 폴백
- **네이버 세계 증시**: Playwright 캡처 시도 → 실패 시 Yahoo Finance API 폴백

### 필요한 설정 (Render)
```yaml
buildCommand: pip install -r requirements.txt && playwright install chromium --with-deps
```

---

## 작업 규칙

1. 새 작업 추가 시 ID 부여 (TB-XXX)
2. 완료 시 DONE 섹션으로 이동 (TB-DXXX)
3. 커밋 후 이 문서 업데이트
4. 우선순위 변경 시 섹션 이동

---

> 마지막 업데이트: 2025-01-26 09:20
