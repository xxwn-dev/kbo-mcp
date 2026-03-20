# KBO MCP Server — 구현 플랜

## 개요

KBO 공식 사이트 데이터를 MCP 툴로 제공하는 Python 서버.
Claude(또는 MCP Inspector)에서 팀 순위와 월별 경기 일정을 조회할 수 있다.

### 데이터 소스

| 기능 | 방식 | 엔드포인트 |
|---|---|---|
| 일정 | HTML 파싱 (BeautifulSoup) | `https://www.koreabaseball.com/Schedule/Schedule.aspx` |
| 순위 | HTML 파싱 (BeautifulSoup) | `https://www.koreabaseball.com/Record/TeamRank/TeamRankDaily.aspx` |

> **참고**: `/ws/` 경로는 `robots.txt`에서 `Disallow` 명시 → HTML 페이지 파싱 방식으로 대체

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

- [ ] `pyproject.toml` 작성
- [ ] `uv` 로 의존성 설치 (`mcp[cli]`, `httpx`, `beautifulsoup4`, `lxml`, `pydantic`)
- [ ] `.gitignore` 작성 (`.venv/`, `__pycache__/`, `*.pyc`, `dist/`)
- [ ] 디렉토리 골격 생성 (`src/kbo_mcp/parsers/`, `src/kbo_mcp/tools/`, `__init__.py` 파일들)
- [ ] `git init` + 첫 커밋

### Step 2 — 데이터 모델 (`models.py`)

- [ ] `TeamStanding` 모델 (rank, team, games, wins, losses, draws, win_pct, games_behind)
- [ ] `StandingsResult` 모델 (updated_at, standings)
- [ ] `GameSchedule` 모델 (date, home_team, away_team, venue, status)
- [ ] `ScheduleResult` 모델 (year, month, games)

### Step 3 — HTTP 클라이언트 (`client.py`)

- [ ] `httpx.AsyncClient` context manager 팩토리 구현
- [ ] User-Agent, Referer 헤더 설정
- [ ] 동작 확인: 순위 페이지 200 응답, 일정 페이지 200 응답

### Step 4 — 순위 파서 (`parsers/standings.py`)

- [ ] BeautifulSoup으로 `<table class="tData">` 파싱
- [ ] `<tbody>` 행을 `TeamStanding` 리스트로 변환
- [ ] 빈 결과(비시즌) 방어 처리
- [ ] 라이브 HTML로 파싱 결과 직접 확인

### Step 5 — 일정 파서 (`parsers/schedule.py`)

- [ ] BeautifulSoup으로 `/Schedule/Schedule.aspx` HTML 파싱
- [ ] 날짜 및 경기 정보 추출
- [ ] `"AWAY : HOME [구장]"` 패턴 정규식으로 경기 추출
- [ ] 팀 약어 → 전체 팀명 매핑 (`TEAM_MAP`)
- [ ] 경기취소/우천취소 `status` 처리
- [ ] 라이브 HTML로 파싱 결과 직접 확인

### Step 6 — 툴 레이어 (`tools/`)

- [ ] `tools/standings.py` — `fetch_standings()` 구현
- [ ] `tools/schedule.py` — `fetch_schedule(year, month)` 구현
- [ ] 연도/월 유효성 검증 (2008 이상, 1~12)

### Step 7 — MCP 서버 (`server.py`)

- [ ] `FastMCP` 인스턴스 생성 (name, instructions)
- [ ] `@mcp.tool()` 로 `get_kbo_standings` 등록
- [ ] `@mcp.tool()` 로 `get_kbo_schedule` 등록 (year, month 파라미터)
- [ ] `main()` 함수 및 `mcp.run()` 추가
- [ ] `pyproject.toml` 의 `[project.scripts]` 에 `kbo-mcp` 엔트리포인트 등록

### Step 8 — MCP Inspector 테스트

- [ ] `mcp dev src/kbo_mcp/server.py` 실행
- [ ] 브라우저 Inspector에서 `get_kbo_standings` 툴 호출 → 결과 확인
- [ ] 브라우저 Inspector에서 `get_kbo_schedule` 툴 호출 → 결과 확인

### Step 9 — (선택) Claude Desktop 연동

- [ ] `which uv` 또는 `which python` 으로 절대 경로 확인
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

### 일정 HTML 파싱 포인트

```
GET https://www.koreabaseball.com/Schedule/Schedule.aspx
```

- `robots.txt` Disallow 대상인 `/ws/` 엔드포인트 대신 HTML 페이지 파싱
- 연도/월 파라미터는 쿼리스트링 또는 폼 POST로 전달 (페이지 구조 확인 필요)
- BeautifulSoup으로 경기 일정 테이블 추출

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
