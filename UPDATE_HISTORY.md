# TeleBot 업데이트 히스토리

> GitHub: https://github.com/doukui7/TeleBot
>
> 이 문서는 TeleBot 프로젝트의 변경 이력, 에러 수정, 기능 추가 등을 기록합니다.
> 반복되는 문제를 방지하고 빠른 디버깅을 위해 작성됩니다.

---

## 목차

1. [변경 이력](#변경-이력)
2. [에러 수정 기록](#에러-수정-기록)
3. [기능 추가 기록](#기능-추가-기록)
4. [알려진 이슈](#알려진-이슈)
5. [트러블슈팅 가이드](#트러블슈팅-가이드)
6. [외부 레퍼런스](#외부-레퍼런스)

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 | 관련 파일 |
|------|------|----------|----------|
| 2025-01-26 | 1.0.1 | GitHub 저장소 생성 (TeleBot) | - |
| 2025-01-26 | 1.0.0 | 프로젝트 초기 생성 (web에서 분리) | 전체 |
| 2025-01-26 | 1.0.0 | 시장 브리핑 기능 구현 | `src/services/briefing.ts` |
| 2025-01-26 | 1.0.0 | 개별 알림 기능 구현 | `src/commands/alert.ts` |
| 2025-01-26 | 1.0.0 | Cron 스케줄러 추가 | `src/index.ts` |

---

## 에러 수정 기록

### 1. [해결됨] RSS 피드 중복 뉴스 문제

**날짜**: 2025-01-26 (web 프로젝트에서 이관)

**증상:**
- 브리핑에 비슷한 제목의 뉴스가 중복 표시됨

**원인:**
- Google News RSS가 같은 뉴스를 여러 소스에서 제공

**해결책:**
```typescript
// Jaccard Similarity로 중복 제거
function getSimilarity(str1: string, str2: string): number {
    const clean = (s: string) => s.replace(/[^\w\s가-힣]/g, '').toLowerCase();
    const s1 = new Set(clean(str1).split(/\s+/));
    const s2 = new Set(clean(str2).split(/\s+/));
    const intersection = new Set([...s1].filter(x => s2.has(x)));
    const union = new Set([...s1, ...s2]);
    return union.size === 0 ? 0 : intersection.size / union.size;
}

// 유사도 40% 이상이면 중복으로 처리
if (sim > 0.4) isDuplicate = true;
```

**관련 파일:**
- `src/services/briefing.ts`

---

### 2. [해결됨] 텔레그램 메시지 전송 실패

**날짜**: 2025-01-26

**증상:**
- "chat not found" 에러
- 메시지가 전송되지 않음

**원인:**
- 사용자가 봇과 대화를 시작하지 않음
- Chat ID가 잘못됨

**해결책:**
1. 사용자가 봇에게 `/start` 메시지 전송 필수
2. `getUpdates` API로 정확한 Chat ID 확인:
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```

**관련 파일:**
- `src/services/telegram.ts`

---

### 3. [해결됨] Markdown 파싱 에러

**날짜**: 2025-01-26

**증상:**
- 특수문자가 포함된 뉴스 제목에서 파싱 에러

**원인:**
- Telegram Markdown은 `_`, `*`, `[`, `]` 등을 특수 처리

**해결책:**
```typescript
// HTML 모드 사용 권장 (더 안정적)
await sendMessage({
    chatId: user.telegram_id,
    token: user.telegram_token,
    message: briefing,
    parseMode: 'HTML'  // Markdown 대신 HTML 사용
});
```

**관련 파일:**
- `src/services/telegram.ts`
- `src/services/briefing.ts`

---

## 기능 추가 기록

### 1. 시장 브리핑 (v1.0.0)

**날짜**: 2025-01-26

**기능:**
- Google News RSS에서 시장 뉴스 수집
- 미국 증시, 한국 증시, 비트코인 3개 카테고리
- 카테고리당 3개 뉴스 (중복 제거 후)

**사용법:**
```bash
npm run briefing
```

**관련 파일:**
- `src/services/briefing.ts`
- `src/commands/briefing.ts`

---

### 2. 개별 알림 (v1.0.0)

**날짜**: 2025-01-26

**기능:**
- 특정 사용자에게 커스텀 메시지 전송
- User ID로 DB에서 텔레그램 정보 조회

**사용법:**
```bash
npm run alert <userId> "<message>"
```

**관련 파일:**
- `src/commands/alert.ts`

---

### 3. Cron 스케줄러 (v1.0.0)

**날짜**: 2025-01-26

**기능:**
- 매일 08:00 KST에 자동 브리핑 전송
- node-cron 라이브러리 사용

**스케줄:**
```typescript
// 08:00 KST = 23:00 UTC (전날)
cron.schedule('0 23 * * *', () => {
    sendDailyBriefing();
}, { timezone: 'UTC' });
```

**관련 파일:**
- `src/index.ts`

---

## 알려진 이슈

### 1. [미해결] Rate Limiting

**증상:**
- 대량 사용자에게 동시 전송 시 일부 실패

**원인:**
- Telegram Bot API rate limit (30 messages/second)

**임시 해결책:**
```typescript
// 딜레이 추가 (향후 구현 예정)
for (const user of users) {
    await sendMessage(...);
    await sleep(100); // 100ms 딜레이
}
```

**상태:** 사용자 수가 적어 현재는 문제없음

---

### 2. [미해결] 봇 토큰 보안

**이슈:**
- 사용자별 봇 토큰이 평문으로 저장됨

**권장 해결책:**
- 암호화 저장 또는 중앙 봇 사용 검토

**상태:** 향후 개선 예정

---

## 트러블슈팅 가이드

### 메시지 전송 안됨

```
1. 봇 토큰 확인
   - BotFather에서 /token으로 확인

2. Chat ID 확인
   - https://api.telegram.org/bot<TOKEN>/getUpdates

3. 봇 대화 시작 확인
   - 사용자가 봇에게 /start 했는지

4. 봇 차단 여부
   - 사용자가 봇을 차단하면 전송 불가
```

### RSS 피드 에러

```
1. 네트워크 확인
   - Google News RSS 접근 가능한지

2. 지역 제한 확인
   - 일부 지역에서 Google 서비스 제한

3. RSS URL 유효성
   - 브라우저에서 직접 접속해서 확인
```

### Supabase 연결 에러

```
1. 환경변수 확인
   - SUPABASE_URL
   - SUPABASE_SERVICE_ROLE_KEY

2. Service Role Key 사용 확인
   - Anon Key가 아닌 Service Role Key 필요

3. RLS 정책 확인
   - Service Role은 RLS 우회
```

---

## 외부 레퍼런스

### Telegram Bot API

- [공식 문서](https://core.telegram.org/bots/api)
- [sendMessage API](https://core.telegram.org/bots/api#sendmessage)
- [Rate Limits](https://core.telegram.org/bots/faq#my-bot-is-hitting-limits-how-do-i-avoid-this)

### Node.js 관련

- [node-cron](https://www.npmjs.com/package/node-cron)
- [cheerio (RSS 파싱)](https://cheerio.js.org/)

### Supabase

- [JavaScript Client](https://supabase.com/docs/reference/javascript)
- [Service Role Key 사용법](https://supabase.com/docs/guides/api#service-role-key)

---

## 체크리스트

### 배포 전 체크리스트

- [ ] `.env` 파일 설정 완료
- [ ] `npm install` 실행
- [ ] `npm run briefing` 테스트 성공
- [ ] Supabase users 테이블에 telegram 컬럼 존재
- [ ] 테스트 사용자에게 메시지 전송 확인

### 새 기능 추가 시 체크리스트

- [ ] 이 문서에 기능 추가 기록
- [ ] README.md 업데이트
- [ ] 테스트 완료
- [ ] 버전 번호 업데이트 (package.json)

---

> **참고:** 새로운 에러나 기능 추가 시 이 문서를 업데이트하세요.
> 마지막 업데이트: 2025-01-26
