# 주간 안전보건 동향 리포트 자동화 (테스트 설정 가이드)

GitHub Actions가 매주 월요일 07:00(한국시간)에 Claude를 실행해 동향 리포트 HTML을 만들고,
GitHub Pages 사이트에 자동으로 게시합니다. 서버 비용 0원, Claude는 내 구독 계정으로 실행됩니다.

## 파일 구성
| 파일 | 역할 |
|---|---|
| `.github/workflows/weekly-report.yml` | 자동 실행 일정·순서 |
| `prompt.md` | Claude에게 주는 조사·작성 지시문 (내용 수정은 여기서) |
| `scripts/publish.py` | 리포트 게시, 목록 갱신, 보안 정책 삽입 |
| `docs/index.html` | 리포트 사이트 첫 화면 (발행 이력 + 최신 리포트) |
| `platform-link.html` | 회사 AI 플랫폼에 한 번만 올리는 연결용 파일 |

## 설정 순서 (PC에서 약 15분)

### 1) 저장소 만들기
1. github.com 로그인 → 오른쪽 위 `+` → **New repository**
2. 이름 예: `safety-weekly` / **Public** 선택 (무료 Pages는 공개 저장소만 가능) → Create
3. **uploading an existing file** 클릭 → 압축 푼 폴더 안의 내용을 **전부** 끌어다 놓기
   (`.github` 폴더가 숨김이라 안 보이면 탐색기 `보기 → 숨긴 항목` 체크)
4. **Commit changes**

### 2) Claude 구독 토큰 발급
1. PC에 Node.js(LTS) 설치 → 명령 프롬프트에서:
   ```
   npx @anthropic-ai/claude-code setup-token
   ```
2. 브라우저에서 Claude 로그인·승인 → 화면에 나온 `sk-ant-oat...` 토큰 복사
   (이 토큰은 비밀번호와 같습니다. 메신저·문서에 붙여넣지 마세요.)

### 3) 토큰 등록
저장소 → **Settings → Secrets and variables → Actions → New repository secret**
- Name: `CLAUDE_CODE_OAUTH_TOKEN`
- Secret: 복사한 토큰

### 4) Pages 켜기
저장소 → **Settings → Pages → Source: GitHub Actions** 선택

### 5) 첫 테스트 실행
저장소 → **Actions** 탭 → (처음이면 활성화 버튼 클릭) → `주간 안전보건 동향 리포트` → **Run workflow**
- 10~30분 소요. 초록 체크가 뜨면 `https://아이디.github.io/safety-weekly/` 접속
- 리포트 맨 아래 **수집 현황 표**에서 노동부·공단 사이트 직접 접속 성공 여부 확인
  (해외 서버라 "검색"으로만 수집됐다면 → 국내 회사 서버 필요성의 근거로 활용)

### 6) 회사 AI 플랫폼 연결
`platform-link.html` 안의 `https://아이디.github.io/저장소이름/` 2곳을 실제 주소로 바꿔 한 번 업로드.

## 실패했을 때
Actions 실행 화면 → 실패한 단계 로그 확인, 또는 하단 **Artifacts → claude-log** 다운로드.
- `시크릿이 등록되지 않았습니다` → 3) 다시 확인
- `report.html 이 생성되지 않았습니다` → claude-log에서 원인 확인 (토큰 만료, 사용량 한도 등)
- Pages 배포 단계 실패 → 4)에서 Source가 **GitHub Actions** 인지 확인

## 회사 서버로 옮길 때
- 개인 토큰 대신 회사 Claude API 키 사용: 워크플로의 `CLAUDE_CODE_OAUTH_TOKEN` → `ANTHROPIC_API_KEY`
- 사내 서버라면 같은 명령(`claude -p ...` + `publish.py`)을 cron으로 실행하고 `docs/`를 사내 웹서버에 게시
