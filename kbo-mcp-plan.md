# KBO MCP Server — 구현 플랜

## 개요

KBO 공식 사이트 데이터를 MCP 툴로 제공하는 Python 서버.
Claude(또는 MCP Inspector)에서 팀 순위와 월별 경기 일정을 조회할 수 있다.

### 데이터 소스

| 기능 | 방식 | 엔드포인트 |
|---|---|---|
| 일정 | 내부 API (`/ws/`) | `https://www.koreabaseball.com/ws/Schedule.asmx/GetMonthSchedule` |
| 순위 | HTML 파싱 (BeautifulSoup) | `https://www.koreabaseball.com/Record/TeamRank/TeamRankDaily.aspx` |

> **참고**: 일정 HTML 페이지(`/Schedule/Schedule.aspx`)는 JS 동적 로딩 방식이라 파싱 불가.
> `/ws/` 경로는 `robots.txt` Disallow 대상이나, 개인/비상업적 용도로만 사용하며 README에 명시.

### 기술 스택

- **Python 3.11+**
- `mcp[cli]` — FastMCP SDK (Anthropic 공식)
- `httpx` — 비동기 HTTP 클라이언트
- `beautifulsoup4` + `lxml` — HTML 파싱
- `pydantic v2` — 데이터 모델
- 패키지 매니저: `uv`

---

## 프로젝트 구조

```
kbo-mcp/
├── kbo-mcp-plan.md
├── pyproject.toml
├── .gitignore
└── src/kbo_mcp/
    ├── __init__.py
    ├── server.py            # FastMCP 진입점, @mcp.tool() 등록
    ├── models.py            # Pydantic 데이터 모델
    ├── client.py            # httpx 공유 비동기 클라이언트
    ├── parsers/
    │   ├── __init__.py
    │   ├── schedule.py      # 일정 HTML 페이지 파싱
    │   └── standings.py     # 순위 HTML 테이블 파싱
    └── tools/
        ├── __init__.py
        ├── schedule.py      # get_kbo_schedule 툴 로직
        └── standings.py     # get_kbo_standings 툴 로직
```

---

## 구현 체크리스트

### Step 1 — 프로젝트 부트스트랩

- [x] `pyproject.toml` 작성
- [x] `uv` 로 의존성 설치 (`mcp[cli]`, `httpx`, `beautifulsoup4`, `lxml`, `pydantic`)
- [x] `.gitignore` 작성 (`.venv/`, `__pycache__/`, `*.pyc`, `dist/`)
- [x] 디렉토리 골격 생성 (`src/kbo_mcp/parsers/`, `src/kbo_mcp/tools/`, `__init__.py` 파일들)
- [x] `git init` + 첫 커밋 + GitHub 레포 생성 (public)

### Step 2 — 데이터 모델 (`models.py`)

- [x] `TeamStanding` 모델 (rank, team, games, wins, losses, draws, win_pct, games_behind)
- [x] `StandingsResult` 모델 (updated_at, standings)
- [x] `GameSchedule` 모델 (date, home_team, away_team, venue, status)
- [x] `ScheduleResult` 모델 (year, month, games)

### Step 3 — HTTP 클라이언트 (`client.py`)

- [x] `httpx.AsyncClient` context manager 팩토리 구현
- [x] User-Agent, Referer 헤더 설정
- [x] 동작 확인: 순위 페이지 200 응답, 일정 API 200 응답

### Step 4 — 순위 파서 (`parsers/standings.py`)

- [x] BeautifulSoup으로 `<table class="tData">` 파싱
- [x] `<tbody>` 행을 `TeamStanding` 리스트로 변환
- [x] 빈 결과(비시즌) 방어 처리
- [x] 라이브 HTML로 파싱 결과 직접 확인 (10팀 정상 파싱)

### Step 5 — 일정 파서 (`parsers/schedule.py`)

- [x] `/ws/Schedule.asmx/GetMonthSchedule` API 호출 (HTML 페이지는 JS 동적 로딩으로 파싱 불가)
- [x] JSON 응답 내 HTML에서 날짜 및 경기 정보 추출
- [x] `"AWAY : HOME [구장]"` 패턴 정규식으로 경기 추출
- [x] 팀 약어 → 전체 팀명 매핑 (`TEAM_MAP`)
- [x] 경기취소/우천취소 `status` 처리
- [x] 라이브 API 응답으로 파싱 결과 직접 확인 (15경기 정상 파싱)

### Step 6 — 툴 레이어 (`tools/`)

- [x] `tools/standings.py` — `fetch_standings()` 구현
- [x] `tools/schedule.py` — `fetch_schedule(year, month, series)` 구현
- [x] 연도/월 유효성 검증 (2008 이상, 1~12)
- [x] `series` 파라미터 추가 (preseason / regular / postseason)

### Step 7 — MCP 서버 (`server.py`)

- [x] `FastMCP` 인스턴스 생성 (name, instructions)
- [x] `@mcp.tool()` 로 `get_kbo_standings` 등록
- [x] `@mcp.tool()` 로 `get_kbo_schedule` 등록 (year, month, series 파라미터)
- [x] `main()` 함수 및 `mcp.run()` 추가
- [x] `pyproject.toml` 의 `[project.scripts]` 에 `kbo-mcp` 엔트리포인트 등록

### Step 8 — MCP Inspector 테스트

- [x] `mcp dev src/kbo_mcp/server.py` 실행
- [x] 브라우저 Inspector에서 `get_kbo_standings` 툴 호출 → 결과 확인
- [x] 브라우저 Inspector에서 `get_kbo_schedule` 툴 호출 → 결과 확인

### Step 8-1 — Claude CLI 연동 테스트

- [x] `claude --mcp-config` 로 로컬 MCP 서버 연결
- [x] "KBO 현재 순위 알려줘" 실제 동작 확인

### Step 9 — (선택) Claude Desktop 연동

- [ ] `which uv` 로 절대 경로 확인 (`/Users/xxwon/.local/bin/uv`)
- [ ] `~/Library/Application Support/Claude/claude_desktop_config.json` 편집

```json
{
  "mcpServers": {
    "kbo": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/Users/xxwon/30.dev/kbo-mcp",
        "kbo-mcp"
      ]
    }
  }
}
```

- [ ] Claude Desktop 완전 종료 후 재시작 (Cmd+Q)
- [ ] "KBO 현재 순위 알려줘" 로 동작 확인

---

## Phase 2 — 추가 기능

### 추가할 MCP 툴

| 툴 | 설명 | 데이터 소스 |
|---|---|---|
| `get_kbo_lineup` | 날짜별 경기 라인업 조회 | `/ws/Main.asmx/GetKboGameList` + 게임센터 라인업 API |
| `get_kbo_game_review` | 경기 리뷰 및 키플레이어 | KBO 게임센터 경기 결과 페이지 |
| `get_kbo_player_stats` | 선수 전통 스탯 조회 | KBO 기록실 페이지 |
| `get_kbo_sabermetrics` | wOBA / FIP 계산 | KBO 기록실 기본 스탯 기반 자체 계산 |

### 데이터 소스 추가

| 기능 | 방식 | 엔드포인트 |
|---|---|---|
| 날짜별 게임 목록 | 내부 API | `/ws/Main.asmx/GetKboGameList` |
| 라인업 상세 | 내부 API | 게임 ID 기반 게임센터 API (탐색 필요) |
| 경기 리뷰/키플레이어 | HTML 파싱 또는 내부 API | KBO 게임센터 결과 페이지 |
| 선수 스탯 | HTML 파싱 | KBO 기록실 |

### GetKboGameList API 확인 사항

```
POST /ws/Main.asmx/GetKboGameList
date=20260315&leId=1&srId=1

응답 주요 필드:
- G_ID        → 게임 ID (라인업/결과 조회에 사용)
- LINEUP_CK   → 라인업 공개 여부 (0: 미공개)
- T_PIT_P_NM  → 원정 선발 투수
- B_PIT_P_NM  → 홈 선발 투수
- GAME_RESULT_CK → 경기 종료 여부
- T_SCORE_CN / B_SCORE_CN → 점수
```

### 세이버메트릭스 계산 방식

KBO 공식 기록(기본 스탯)을 가져와서 직접 계산. 외부 사이트 크롤링 불필요.

**wOBA (가중 출루율)**
```
wOBA = (0.69×볼넷 + 0.72×사구 + 0.89×1루타 + 1.27×2루타
        + 1.62×3루타 + 2.10×홈런) / 타석
```

**FIP (수비 무관 방어율)**
```
FIP = (13×피홈런 + 3×(볼넷+사구) - 2×탈삼진) / 이닝 + 3.2(상수)
```

> **제외 항목**: wRC+(파크팩터 필요), WAR(수비 데이터 필요) → 구현 복잡도 대비 효용 낮음

### 프로젝트 구조 추가 파일

```
src/kbo_mcp/
├── parsers/
│   ├── lineup.py        # 날짜별 라인업 파싱
│   ├── game_review.py   # 경기 리뷰/키플레이어 파싱
│   └── player_stats.py  # 선수 스탯 파싱
├── tools/
│   ├── lineup.py        # get_kbo_lineup 툴 로직
│   ├── game_review.py   # get_kbo_game_review 툴 로직
│   └── player_stats.py  # get_kbo_player_stats / get_kbo_sabermetrics 툴 로직
└── calculators/
    └── sabermetrics.py  # wOBA, FIP 계산 함수
```

---

## Phase 2 체크리스트

### Step 10 — 라인업 기능

- [ ] `/ws/Main.asmx/GetKboGameList` API로 날짜별 게임 목록 조회 확인
- [ ] 게임 ID 기반 라인업 상세 API 탐색 (게임센터 Network 탭 분석)
- [ ] `LineupPlayer` 모델 (이름, 포지션, 타순, 팀)
- [ ] `GameLineup` 모델 (game_id, date, home_team, away_team, home_lineup, away_lineup)
- [ ] `parsers/lineup.py` 구현
- [ ] `tools/lineup.py` — `fetch_lineup(date)` 구현
- [ ] `server.py` 에 `get_kbo_lineup` 툴 등록
- [ ] 테스트: 시범경기 날짜로 라인업 조회 확인

### Step 11 — 경기 리뷰 / 키플레이어

- [ ] 게임센터 경기 결과 페이지 구조 탐색
- [ ] 리뷰 텍스트 및 키플레이어 데이터 추출 방식 확인
- [ ] `GameReview` 모델 (game_id, date, summary, key_players)
- [ ] `parsers/game_review.py` 구현
- [ ] `tools/game_review.py` — `fetch_game_review(game_id)` 구현
- [ ] `server.py` 에 `get_kbo_game_review` 툴 등록
- [ ] 테스트: 종료된 경기 리뷰 조회 확인

### Step 12 — 선수 스탯

- [ ] KBO 기록실 타자/투수 스탯 페이지 구조 탐색
- [ ] `BatterStats` 모델 (타율, 홈런, 타점, 출루율, 장타율 등)
- [ ] `PitcherStats` 모델 (방어율, 탈삼진, WHIP, 승/패 등)
- [ ] `parsers/player_stats.py` 구현
- [ ] `tools/player_stats.py` — `fetch_player_stats(name, year)` 구현
- [ ] `server.py` 에 `get_kbo_player_stats` 툴 등록
- [ ] 테스트: 선수 이름으로 스탯 조회 확인

### Step 13 — 세이버메트릭스 계산

- [ ] `calculators/sabermetrics.py` — `calc_woba(stats)` 구현
- [ ] `calculators/sabermetrics.py` — `calc_fip(stats)` 구현
- [ ] `tools/player_stats.py` 에 세이버메트릭스 계산 연동
- [ ] `server.py` 에 `get_kbo_sabermetrics` 툴 등록
- [ ] 테스트: 특정 선수 wOBA/FIP 계산 결과 확인

---

## 핵심 구현 포인트

### FastMCP 툴 등록 패턴

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="kbo-mcp")

@mcp.tool()
async def get_kbo_standings() -> StandingsResult:
    """현재 KBO 팀 순위를 반환합니다."""
    return await fetch_standings()

@mcp.tool()
async def get_kbo_schedule(year: int, month: int) -> ScheduleResult:
    """KBO 월별 경기 일정을 반환합니다."""
    return await fetch_schedule(year, month)

def main():
    mcp.run()  # stdio transport (Claude Desktop 호환)
```

- 함수 타입힌트 → FastMCP가 JSON Schema 자동 생성
- Pydantic 모델 리턴 → FastMCP가 자동 직렬화
- `async def` 필수 (I/O 작업)

### 일정 API 호출 형식

```
POST https://www.koreabaseball.com/ws/Schedule.asmx/GetMonthSchedule
Content-Type: application/x-www-form-urlencoded

leId=1&srIdList=0,9,6&seasonId=2026&gameMonth=03&teamId=0
```

- `srIdList` 값: 시범경기 `"1"`, 정규시즌 `"0,9,6"`, 포스트시즌 `"3,4,5,7"`
- `gameMonth` 은 두 자리 zero-pad (`"03"`, not `"3"`)
- `httpx`에서는 `data=` 파라미터 사용 (`json=` 아님)

### 순위 HTML 파싱 포인트

```python
table = soup.find("table", class_="tData")
for row in table.find("tbody").find_all("tr"):
    cells = [td.text.strip() for td in row.find_all("td")]
    # cells: [순위, 팀명, 경기, 승, 패, 무, 승률, 게임차, ...]
```

---

## 주요 리스크

| 리스크 | 대응 |
|---|---|
| 비시즌에 순위 페이지 비어있음 | 빈 리스트 반환, 예외 아님 |
| KBO 사이트 HTML 구조 변경 | selector 유지 모니터링 |
| `uv`가 Claude Desktop PATH에 없음 | 절대 경로 사용 |
