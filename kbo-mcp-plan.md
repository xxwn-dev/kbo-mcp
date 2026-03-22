# KBO MCP Server — 구현 플랜

## 개요

KBO 공식 사이트 데이터를 MCP 툴로 제공하는 Python 서버.
Claude(또는 MCP Inspector)에서 팀 순위, 월별 경기 일정, 날짜별 경기 정보, 경기 리뷰를 조회할 수 있다.

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

| 툴 | 설명 | 데이터 소스 | 상태 |
|---|---|---|---|
| ~~`get_kbo_lineup`~~ | ~~날짜별 경기 정보 및 선발 투수 조회~~ | ~~`/ws/Main.asmx/GetKboGameList`~~ | ✅ `get_kbo_game`으로 통합 |
| ~~`get_kbo_game_review`~~ | ~~종료 경기: 타순·하이라이트·키플레이어 / 진행 중: 키플레이어만~~ | ~~`GetBoxScoreScroll` + `GetScoreBoardScroll` + `GetKeyPlayerPitcher/Hitter`~~ | ✅ `get_kbo_game`으로 통합 |
| `get_kbo_game` | 날짜별 경기 정보 통합 툴 — 팀명 생략 시 전체 목록, 팀명 지정 시 키플레이어·이닝점수·타순·하이라이트 | `GetKboGameList` + `GetBoxScoreScroll` + `GetScoreBoardScroll` + `GetKeyPlayer*` | ✅ **구현 완료** |
| `get_kbo_player_stats` | 선수 전통 스탯 조회 | KBO 기록실 페이지 | ⬜ 미구현 |
| `get_kbo_sabermetrics` | wOBA / FIP 계산 | KBO 기록실 기본 스탯 기반 자체 계산 | ⬜ 미구현 |
| `get_kbo_matchup` | 투수-타자 역대 상성 조회 | KBO 기록실 투수 vs 타자 페이지 | ⬜ 미구현 |
| `get_kbo_prediction` | 경기 승부 예측 데이터 조회 | 최근 전적 + 선발 투수 스탯 + 팀 홈/원정 성적 조합 | ⬜ 미구현 |

### 데이터 소스 추가

| 기능 | 방식 | 엔드포인트 |
|---|---|---|
| 날짜별 게임 목록 + 선발 투수 | 내부 API | `/ws/Main.asmx/GetKboGameList` |
| 진행 전/중 타자 타순 | ❌ 미제공 | KBO 로그인 필요, 네이버 스포츠도 CSR 구조로 접근 불가 |
| 종료 경기 타자 타순 + 투수 기록 + 하이라이트 | 내부 API | `/ws/Schedule.asmx/GetBoxScoreScroll` |
| 종료 경기 메타 (구장·관중·소요시간) | 내부 API | `/ws/Schedule.asmx/GetScoreBoardScroll` |
| WPA 키플레이어 (투수/타자) | 내부 API | `/ws/Schedule.asmx/GetKeyPlayerPitcher`, `/ws/Schedule.asmx/GetKeyPlayerHitter` |
| 선수 스탯 | HTML 파싱 | KBO 기록실 |
| 투수-타자 상성 | HTML 파싱 | `https://www.koreabaseball.com/Record/Pitcher/PitcherVsBatter/BasicOld.aspx` |
| 팀 최근 전적 | HTML 파싱 | KBO 기록실 팀 결과 페이지 |

### GetKboGameList API 확인 사항

```
POST /ws/Main.asmx/GetKboGameList
date=20260315&leId=1&srId=0   # srId: 0=정규시즌, 1=시범경기, 3=포스트시즌

응답 주요 필드:
- G_ID            → 게임 ID (경기 리뷰 조회에 사용)
- AWAY_NM / HOME_NM  → 팀 표시명 (예: "KIA", "두산")
- AWAY_ID / HOME_ID  → 팀 내부 코드 (예: "HT", "OB")
- LINEUP_CK       → 라인업 공개 여부 (0=미공개, 양수=공개 — boolean 아님)
- T_PIT_P_NM      → 원정 선발 투수 (null 가능)
- B_PIT_P_NM      → 홈 선발 투수 (null 가능)
- GAME_RESULT_CK  → 경기 종료 여부 (0=진행중/예정, 1=종료)
- T_SCORE_CN / B_SCORE_CN → 점수
```

### GetBoxScoreScroll API 확인 사항

```
POST /ws/Schedule.asmx/GetBoxScoreScroll
leId=1&srId=1&seasonId=2026&gameId=20260321HTOB0

응답 주요 필드:
- arrHitter[팀][table1]  → 타순·포지션·선수명 (같은 타순 반복 = 교체 선수)
- arrHitter[팀][table2]  → 타격 성적
- arrPitcher[팀][table]  → 투수 기록
- tableEtc               → 결승타·홈런·3루타·도루 등 하이라이트 (JSON 문자열)

※ 종료된 경기에서만 데이터 반환
```

### GetKeyPlayerPitcher / GetKeyPlayerHitter API 확인 사항

```
POST /ws/Schedule.asmx/GetKeyPlayerPitcher (또는 GetKeyPlayerHitter)
leId=1&srId=1&gameId=20260322HHLT0&groupSc=GAME_WPA_RT&sort=DESC

응답 주요 필드:
- RANK_NO    → 순위
- P_NM       → 선수명
- T_ID       → 팀 내부 코드 (예: "LT"=롯데, "HH"=한화)
- RECORD_IF  → "19.4%</br>(5이닝 1실점 3삼진)" 형태 — </br> 기준으로 WPA%와 기록 분리

※ 경기 진행 중·종료 후 모두 조회 가능
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
│   ├── lineup.py        # GetKboGameList 파싱 (선발 투수·경기 상태)
│   ├── game_review.py   # GetBoxScoreScroll·GetKeyPlayer 파싱
│   ├── player_stats.py  # 선수 스탯 파싱
│   └── matchup.py       # 투수-타자 상성 파싱
├── tools/
│   ├── lineup.py        # get_kbo_lineup 툴 로직
│   ├── game_review.py   # get_kbo_game_review 툴 로직 (date+팀명으로 game_id 자동 resolve)
│   ├── player_stats.py  # get_kbo_player_stats / get_kbo_sabermetrics 툴 로직
│   ├── matchup.py       # get_kbo_matchup 툴 로직
│   └── prediction.py    # get_kbo_prediction 툴 로직 (데이터 조합)
└── calculators/
    └── sabermetrics.py  # wOBA, FIP 계산 함수
```

---

## Phase 2 체크리스트

### Step 10 — 날짜별 경기 정보 (선발 투수)

> **완료 및 Step 11과 병합**: `get_kbo_lineup`은 `get_kbo_game`으로 통합.
> `tools/lineup.py`의 `fetch_lineup()`은 내부 헬퍼로 유지.

- [x] `/ws/Main.asmx/GetKboGameList` API 응답 구조 확인 (AWAY_NM/HOME_NM, LINEUP_CK 양수 체크)
- [x] 진행 전/중 타자 타순 API 탐색 → 불가 확인 (KBO 로그인 필요, 네이버 스포츠 CSR)
- [x] `GameLineup` 모델 (game_id, date, away/home_team, away/home_starter, lineup_confirmed, game_finished, score) — 내부 헬퍼용 유지
- [x] `DailyLineupResult` 모델 (date, games) — 내부 헬퍼용 유지
- [x] `parsers/lineup.py` — TEAM_MAP (표시명 + 내부코드 통합), `parse_game_list()` 구현
- [x] `tools/lineup.py` — `fetch_lineup(date)` 구현 (정규/시범 병렬 조회, 중복 제거)
- [x] ~~`server.py` 에 `get_kbo_lineup` 툴 등록~~ → `get_kbo_game`으로 통합
- [x] 테스트: 시범경기 날짜로 경기 정보 조회 확인

### Step 11 — 경기 리뷰 / 키플레이어

> **범위 확정**: 리뷰 텍스트(요약문)는 KBO API 미제공으로 제외.
> 인터페이스: `get_kbo_game_review(date, away_team, home_team)` — 내부에서 game_id 자동 resolve.

#### 실시간 가용성 정리 (API 탐색 완료)

| 데이터 | API | 진행 중 | 종료 후 |
|---|---|---|---|
| WPA 키플레이어 (투수/타자) | `GetKeyPlayerPitcher/Hitter` | ✅ | ✅ |
| 이닝별 점수판 | `GetScoreBoardScroll` (table2/3) | ❌ | ✅ |
| 경기 메타 (구장·관중·시간) | `GetScoreBoardScroll` | 구장·관중만 | ✅ 전체 |
| 타순 (arrHitter) | `GetBoxScoreScroll` | ❌ (로그인 필요) | ✅ |
| 하이라이트 (tableEtc) | `GetBoxScoreScroll` | ❌ | ✅ |

> `GetScoreBoardScroll`: 진행 중엔 구장·관중만 반환, 이닝 데이터는 종료 후 제공.
> `GetBoxScoreScroll`: arrHitter(타순)은 종료 후에만 반환. 진행 중 타순은 KBO 로그인 필요.

#### 응답 구조 (game_finished 여부로 분기)

```
진행 중: 키플레이어(투수/타자)
종료 후: 키플레이어 + 이닝별 점수판 + 타순 + 하이라이트 + 경기 메타
```

#### API 구조 확인 완료

- `GetScoreBoardScroll`: table2.rows[0/1]=이닝점수(원정/홈), table3.rows[0/1]=[R,H,E,...], 진행 중엔 이닝 데이터 미제공
- `GetBoxScoreScroll`: arrHitter[0/1].table1=타순 JSON, tableEtc=하이라이트 [카테고리, 내용] 쌍
- `GetKeyPlayer*`: 진행 중·종료 모두 실시간 제공

#### 체크리스트

- [x] `GetKeyPlayerPitcher` / `GetKeyPlayerHitter` API 확인
- [x] `GetBoxScoreScroll` API 확인
- [x] `GetScoreBoardScroll` API 확인
- [x] `KeyPlayer` 모델 (rank, name, team, wpa_pct, record)
- [x] ~~`GameKeyPlayers` 모델~~ → `FullGameReview`로 대체
- [x] `parsers/game_review.py` — RECORD_IF 파싱 구현
- [x] `tools/game_review.py` — `fetch_game(date, away_team, home_team)` 로 전면 재작성
  - 팀명 없음: fetch_lineup → DailyGamesResult (기본 정보만)
  - 팀명 있음: game_id resolve → 키플레이어 항상 조회 → 종료 시 BoxScore+ScoreBoard 병렬 조회
  - 팀명 한 쪽만 입력: 원정·홈 구분 없이 해당 팀 포함 경기 매칭
- [x] ~~`server.py` 에 `get_kbo_game_review` 툴 등록~~ → `get_kbo_game`으로 통합
- [x] `BattingPlayer` 모델 (order, position, name, is_starter)
- [x] `GameHighlight` 모델 (category, detail)
- [x] `FullGameReview` 모델 (game_id, date, away/home_team, away/home_starter, lineup_confirmed, game_finished, away/home_score, venue, crowd, start_time, end_time, duration, away/home_inning_scores, total_innings, away/home_lineup, highlights, pitcher_key_players, hitter_key_players)
- [x] `DailyGamesResult` 모델 (date, games: list[FullGameReview])
- [x] `parsers/game_review.py` — `parse_inning_scores()` 구현 (table2 rows → away/home 이닝점수)
- [x] `parsers/game_review.py` — `parse_batting_lineup()` 구현 (arrHitter JSON → BattingPlayer)
- [x] `parsers/game_review.py` — `parse_highlights()` 구현 (tableEtc rows → GameHighlight)
- [x] `server.py` — `get_kbo_lineup` + `get_kbo_game_review` 제거, `get_kbo_game` 등록
- [x] 테스트: 팀명 없이 날짜만 → 전체 경기 목록 반환 확인
- [x] 테스트: 팀명 한 쪽만 입력 → 원정·홈 무관 경기 매칭 확인
- [x] 테스트: 진행 중 경기 → 기본 정보 + 키플레이어 반환 확인
- [x] 테스트: 종료 경기 → 풀 리뷰 (이닝점수 + 타순 + 하이라이트) 확인

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

### Step 14 — 투수-타자 상성 조회

- [ ] KBO 기록실 `PitcherVsBatter` 페이지 구조 탐색 (투수 ID 기반 조회 방식 확인)
- [ ] `MatchupRecord` 모델 (batter_name, at_bats, hits, home_runs, strikeouts, avg)
- [ ] `PitcherMatchupResult` 모델 (pitcher_name, year, records)
- [ ] `parsers/matchup.py` 구현
- [ ] `tools/matchup.py` — `fetch_matchup(pitcher_name, year)` 구현
- [ ] `server.py` 에 `get_kbo_matchup` 툴 등록
- [ ] 테스트: 특정 투수 이름으로 상성 조회 확인

### Step 15 — 승부 예측 데이터 조회

> **설계 원칙**: 이 툴은 예측 수치를 직접 계산하지 않음. 필요한 데이터를 구조화하여 반환하고, LLM이 이를 바탕으로 분석/예측을 수행하는 구조.

- [ ] 팀 최근 N경기 결과 조회 방식 탐색 (KBO 기록실 팀 결과 페이지)
- [ ] 홈/원정별 팀 성적 파싱 방식 확인
- [ ] `RecentGameResult` 모델 (date, opponent, home_away, result, score)
- [ ] `PredictionContext` 모델 (home_team, away_team, venue, home_starter, away_starter, home_recent, away_recent, home_record, away_record)
- [ ] `tools/prediction.py` — `fetch_prediction_context(date, home_team, away_team)` 구현
  - `GetKboGameList` API로 해당 날짜 선발 투수 자동 조회
  - 두 팀 최근 5경기 결과 조회
  - 홈/원정 시즌 성적 조회
- [ ] `server.py` 에 `get_kbo_prediction` 툴 등록
- [ ] 테스트: 예정된 경기 날짜와 팀으로 데이터 조회 확인

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
| 진행 전/중 타자 타순 불가 | KBO 로그인 필요 확인 → 선발 투수만 제공으로 범위 확정 |
| `T_PIT_P_NM` 등 null 가능 필드 | `.get(key, "")` 대신 `(g.get(key) or "").strip()` 사용 |
| `LINEUP_CK`가 boolean 아닌 양수 | `== "1"` 대신 `> 0` 체크 |
| 투수 ID 탐색 필요 (이름만으로 조회 불가할 수 있음) | 선수 검색 API 또는 기록실 검색 페이지로 ID 획득 후 상성 조회 |
| 승부 예측 — 파크팩터 데이터 없음 | 파크팩터 제외, 홈/원정 시즌 성적으로 대체 |
| 승부 예측 — 예측 수치 직접 계산 시 신뢰도 문제 | 툴은 데이터만 제공, 분석은 LLM에 위임 |
