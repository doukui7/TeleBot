# Quanters Telegram Bot

독립적으로 운영되는 텔레그램 봇 서비스입니다.
시장 브리핑, 가격 알림 등의 기능을 제공합니다.

---

## 📁 프로젝트 구조

```
telegram-bot/
├── src/
│   ├── config/
│   │   └── supabase.ts      # Supabase 클라이언트 설정
│   ├── services/
│   │   ├── telegram.ts      # 텔레그램 API 래퍼
│   │   └── briefing.ts      # 브리핑 생성 서비스
│   ├── commands/
│   │   ├── briefing.ts      # 브리핑 전송 명령
│   │   └── alert.ts         # 알림 전송 명령
│   └── index.ts             # 메인 진입점
├── package.json
├── tsconfig.json
├── .env.example
└── README.md
```

---

## 🚀 설치 및 실행

### 1. 의존성 설치

```bash
cd telegram-bot
npm install
```

### 2. 환경변수 설정

```bash
cp .env.example .env
```

`.env` 파일 편집:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### 3. 실행

```bash
# 개발 모드
npm run dev

# 빌드
npm run build

# 프로덕션 실행
npm start server
```

---

## 📬 기능 목록

### 1. 시장 브리핑 (Market Briefing)

매일 아침 시장 뉴스를 텔레그램으로 전송합니다.

**수동 실행:**
```bash
npm run briefing
```

**내용:**
- 🇺🇸 미국 증시 뉴스 (3개)
- 🇰🇷 한국 증시 뉴스 (3개)
- 🪙 비트코인 뉴스 (3개)

**RSS 소스:** Google News RSS

---

### 2. 개별 알림 (Alert)

특정 사용자에게 알림을 전송합니다.

```bash
npm run alert <userId> "<message>"
```

**예시:**
```bash
npm run alert abc123 "🚨 비트코인 급등! 현재가: $100,000"
```

---

### 3. 스케줄러 모드 (Server)

cron으로 자동 실행됩니다.

```bash
npm start server
```

**스케줄:**
| 작업 | 시간 (KST) | 설명 |
|------|-----------|------|
| Daily Briefing | 08:00 | 시장 브리핑 전송 |

---

## 🔧 API 사용법

### 프로그래매틱 사용

```typescript
import {
    sendMessage,
    sendToMultipleUsers,
    generateBriefing,
    getTelegramUsers,
    sendAlert
} from 'telegram-bot';

// 단일 메시지 전송
await sendMessage({
    chatId: '123456789',
    token: 'bot-token',
    message: '안녕하세요!',
    parseMode: 'HTML'
});

// 브리핑 생성
const briefing = await generateBriefing();

// 모든 사용자에게 전송
const users = await getTelegramUsers();
await sendToMultipleUsers(users, briefing, 'HTML');

// 특정 사용자에게 알림
await sendAlert({
    userId: 'user-uuid',
    message: '가격 알림입니다!'
});
```

---

## 📊 데이터베이스 스키마

### users 테이블 필수 컬럼

```sql
telegram_id    VARCHAR    -- 텔레그램 Chat ID
telegram_token VARCHAR    -- 사용자별 봇 토큰
```

**설정 방법:**
1. 사용자가 `/mypage`에서 텔레그램 설정
2. BotFather에서 봇 생성 후 토큰 입력
3. 봇과 대화 시작 후 Chat ID 입력

---

## 🔗 텔레그램 봇 설정 가이드

### 1. BotFather에서 봇 생성

1. 텔레그램에서 `@BotFather` 검색
2. `/newbot` 명령 실행
3. 봇 이름 입력 (예: My Trading Bot)
4. 봇 username 입력 (예: my_trading_bot)
5. **Bot Token** 복사 저장

### 2. Chat ID 확인

1. 생성한 봇과 대화 시작 (`/start`)
2. 다음 URL 접속:
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
3. `chat.id` 값 확인

### 3. 설정 저장

웹사이트 `/mypage`에서:
- Telegram ID: Chat ID 입력
- Telegram Token: Bot Token 입력

---

## 🛠 트러블슈팅

### 메시지가 전송되지 않음

1. **봇과 대화 시작 확인**
   - 사용자가 봇에게 먼저 `/start` 해야 함

2. **토큰 확인**
   - BotFather에서 새 토큰 발급 시도

3. **Chat ID 확인**
   - getUpdates로 정확한 ID 확인

### 에러: "chat not found"

- 사용자가 봇을 차단했거나 대화를 삭제함
- 해결: 사용자가 봇과 다시 대화 시작

### 에러: "Unauthorized"

- 봇 토큰이 잘못됨
- 해결: BotFather에서 토큰 재확인

---

## 📝 변경 이력

| 날짜 | 버전 | 내용 |
|------|------|------|
| 2025-01-26 | 1.0.0 | 초기 버전 (web에서 분리) |

---

## 🔒 보안 주의사항

- `.env` 파일을 Git에 커밋하지 마세요
- Service Role Key는 서버에서만 사용하세요
- 사용자별 봇 토큰은 암호화 저장 권장

---

## 📚 관련 문서

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Supabase Docs](https://supabase.com/docs)
- [node-cron](https://www.npmjs.com/package/node-cron)
