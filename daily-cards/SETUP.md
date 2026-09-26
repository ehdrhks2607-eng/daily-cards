# 무료 자동 발행 세팅 가이드 (한 번만)

전체 흐름: **Claude가 매일 글·카드 생성 → GitHub 저장소에 올림 → GitHub Actions가 정해진 시간에 인스타·스레드에 게시**

---

## 1. GitHub (10분)

1. github.com 가입 (아이디는 신상과 무관하게)
2. 오른쪽 위 프로필 → **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**
   - Token name: `daily-cards`
   - Expiration: 1년
   - Repository access: **All repositories** (저장소를 Claude가 만들기 때문. 만든 뒤 이 저장소만으로 좁혀도 됨)
   - Permissions → Repository permissions:
     - **Administration**: Read and write (저장소 생성용)
     - **Contents**: Read and write
     - **Secrets**: Read and write
     - **Workflows**: Read and write
   - Generate → `github_pat_...` 복사
3. 이 토큰을 Claude에게 전달 → Claude가 공개 저장소 생성·코드 업로드·예약 실행 세팅

## 2. 인스타 계정 준비 (계정당 2분)

- 인스타 앱 → 설정 → 계정 유형 및 도구 → **프로페셔널 계정으로 전환 → 크리에이터**
- 페이스북 페이지 연결은 **필요 없음**

## 3. Meta 개발자 앱 (20~30분, 한 번만)

1. developers.facebook.com → 로그인 → **내 앱 → 앱 만들기**
2. 사용 사례에서 **"Threads API 액세스"** 선택 → 앱 이름 아무거나 → 생성
3. 앱 대시보드 → **사용 사례 추가 → "Instagram에서 메시지 및 콘텐츠 관리"(Instagram API) 추가**

### 3-1. 스레드 토큰 (계정 2개 각각)
1. 사용 사례 → Threads API → **권한**: `threads_basic`, `threads_content_publish`, `threads_manage_replies` 추가
2. **앱 역할 → 역할 → Threads 테스터 추가** → 작심삼일·서울적응기 스레드 아이디 입력
3. 각 계정 스레드 앱 → 설정 → 계정 → **웹사이트 권한 → 초대 → 수락**
4. 사용 사례 → Threads API → 설정 → **사용자 토큰 생성기**에서 계정별로 토큰 생성 (단기 토큰)
5. 장기 토큰(60일)으로 교환: 브라우저 주소창에 붙여넣기
   ```
   https://graph.threads.net/access_token?grant_type=th_exchange_token&client_secret=앱시크릿코드&access_token=단기토큰
   ```
   (앱 시크릿 코드: 앱 설정 → 기본 설정 → Threads 앱 시크릿 코드)
   → 나온 `access_token` 값이 최종 토큰

### 3-2. 인스타 토큰 (계정 2개 각각)
1. 사용 사례 → Instagram API → **Instagram 로그인을 통한 API 설정**
2. **앱 역할 → Instagram 테스터 추가** → 두 인스타 계정 추가
3. 각 인스타 앱 → 설정 → **웹사이트 권한 → 앱 및 웹사이트 → 테스터 초대 → 수락**
4. 다시 "API 설정" 화면 → **계정 추가 → 토큰 생성** (이 토큰은 처음부터 60일짜리)

> 앱은 **개발 모드 그대로** 두면 됨. 본인 계정만 쓰는 거라 앱 검수 불필요.

## 4. 토큰을 GitHub에 저장 (직접 입력 권장)

저장소 → **Settings → Secrets and variables → Actions → New repository secret** 으로 아래 5개 등록

| 이름 | 값 |
|---|---|
| `JAK_THREADS_TOKEN` | 작심삼일 스레드 장기 토큰 |
| `JAK_IG_TOKEN` | 작심삼일 인스타 토큰 |
| `SEOUL_THREADS_TOKEN` | 서울적응기 스레드 장기 토큰 |
| `SEOUL_IG_TOKEN` | 서울적응기 인스타 토큰 |
| `GH_PAT` | 1번에서 만든 GitHub 토큰 (자동 갱신용) |

토큰은 매주 월요일 03시에 자동 갱신됨 (refresh-tokens 워크플로).

---

## 매일 운영
- 게시 시간(KST): 서울적응기 평일 07:30·주말 09:00 / 작심삼일 평일 12:30·주말 13:30 (config.json)
- 처음 2주는 `require_approval: true` → Claude 채팅에서 **"승인"** 하면 게시됨
- 쿠팡 링크는 채팅으로 주면 Claude가 `[쿠팡링크: ...]` 자리에 넣음. 링크가 비어 있으면 본문·카드는 먼저 게시되고, 링크 댓글은 채워지는 대로 달림
