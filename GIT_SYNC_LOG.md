# Git 동기화 로그 - TeleBot

> 여러 디바이스/환경에서 작업 시 동기화 상태를 추적하는 문서

---

## 디바이스 목록

| 디바이스 ID | 설명 | OS | 비고 |
|-------------|------|-----|------|
| `DESKTOP-MAIN` | 메인 데스크탑 | Windows 11 | basra 계정 |
| `LAPTOP-01` | 노트북 | - | - |
| `RENDER` | Render 서버 | Linux | 배포 서버 |

---

## 동기화 이력

| 날짜 | 시간 | 디바이스 | 작업 | 커밋 해시 | 주요 변경사항 |
|------|------|----------|------|-----------|---------------|
| 2025-01-26 | 04:45 | DESKTOP-MAIN | push | `65b2b60` | 유틸리티 스크립트 및 테스트 파일 추가 |
| 2025-01-26 | 02:13 | DESKTOP-MAIN | push | `017e0a8` | Initial commit: Telegram Bot 독립 프로젝트 |

---

## 원격 저장소 최신 상태

| 항목 | 값 |
|------|-----|
| 현재 브랜치 | `main` |
| 최신 커밋 | `65b2b60` |
| 마지막 Push | 2025-01-26 04:45 |
| 마지막 디바이스 | DESKTOP-MAIN |

---

## 디바이스별 동기화 상태

| 디바이스 | 마지막 Pull | 현재 커밋 | 상태 | 미푸시 변경 |
|----------|-------------|-----------|------|-------------|
| DESKTOP-MAIN | 2025-01-26 04:45 | `65b2b60` | ✅ 최신 | 없음 |
| RENDER | - | - | ❓ 설정 필요 | - |

**상태 범례:**
- ✅ 최신: 원격과 동기화됨
- ⚠️ 뒤처짐: pull 필요
- 🔄 앞섬: push 필요
- ❓ 미확인: 확인 필요

---

## 작업 전 체크리스트

### Step 1: Git 동기화
```bash
git status
git log --oneline -3
git fetch origin
git pull origin main
```

### Step 2: 히스토리 검색 (중요!)

**코드 변경 전 반드시 ERROR_FIX_HISTORY.md 검색**

| 작업 유형 | 검색 키워드 | 참고 섹션 |
|----------|------------|-----------|
| 텔레그램 API | `telegram`, `bot`, `send_message` | 섹션 1 |
| 스크린샷 캡처 | `selenium`, `playwright`, `screenshot` | 섹션 2 |
| 스케줄러 | `scheduler`, `cron`, `APScheduler` | 섹션 3 |
| Render 배포 | `Render`, `deploy`, `build` | 섹션 4 |

### Step 3: 작업 방법 선택

- [ ] **히스토리에 해결책 있음** → 문서화된 방법 사용
- [ ] **히스토리에 없음** → 새로운 접근법 시도
- [ ] **새 에러 발생 시** → ERROR_FIX_HISTORY.md에 기록 추가

### Step 4: 작업 완료 후

- [ ] 이 문서의 동기화 이력 업데이트
- [ ] 디바이스별 상태 업데이트
- [ ] 커밋 & 푸시

---

## 관련 프로젝트

| 프로젝트 | GitHub URL | 설명 |
|----------|------------|------|
| GoldenToilet | https://github.com/doukui7/GoldenToilet | 메인 트레이딩 웹앱 |
| TeleBot | https://github.com/doukui7/TeleBot | 텔레그램 봇 (현재) |

---

> **규칙**: Push 후 반드시 이 문서 업데이트 → 커밋 → Push
