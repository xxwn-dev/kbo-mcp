# kbo-mcp

KBO 프로야구 데이터를 제공하는 [MCP](https://modelcontextprotocol.io) 서버.
Claude에서 팀 순위와 월별 경기 일정을 자연어로 조회할 수 있습니다.

## 제공 툴

| 툴 | 설명 | 파라미터 |
|---|---|---|
| `get_kbo_standings` | 현재 KBO 팀 순위 조회 | 없음 |
| `get_kbo_schedule` | 월별 경기 일정 조회 | `year`, `month` |

## 데이터 소스

- **순위**: `koreabaseball.com/Record/TeamRank/TeamRankDaily.aspx` (HTML 파싱)
- **일정**: `koreabaseball.com/ws/Schedule.asmx/GetMonthSchedule` (내부 API)

> **참고**: 일정 데이터는 `koreabaseball.com`의 내부 API(`/ws/`)를 사용합니다.
> 해당 경로는 `robots.txt`에 `Disallow`로 명시되어 있습니다.
> 이 프로젝트는 개인/비상업적 용도로만 사용하며, 서버에 과도한 부하를 주지 않습니다.

## 설치 및 실행

### 요구사항

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

### 설치

```bash
git clone https://github.com/xxwn-dev/kbo-mcp.git
cd kbo-mcp
uv sync
```

### MCP Inspector로 테스트

```bash
uv run mcp dev src/kbo_mcp/server.py
```

브라우저에서 Inspector UI를 열어 툴을 직접 호출해볼 수 있습니다.

### Claude Desktop 연동

`~/Library/Application Support/Claude/claude_desktop_config.json` 에 추가:

```json
{
  "mcpServers": {
    "kbo": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/절대경로/kbo-mcp",
        "kbo-mcp"
      ]
    }
  }
}
```

> `uv`의 절대 경로가 필요한 경우 `which uv` 로 확인하세요.

Claude Desktop을 완전히 종료 후 재시작하면 적용됩니다.

### 사용 예시

```
KBO 현재 순위 알려줘
2026년 4월 경기 일정 보여줘
다음 주 LG 경기 있어?
```

## 기술 스택

- [FastMCP](https://github.com/jlowin/fastmcp) — MCP 서버 프레임워크
- [httpx](https://www.python-httpx.org/) — 비동기 HTTP 클라이언트
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) — HTML 파싱
- [Pydantic v2](https://docs.pydantic.dev/) — 데이터 모델
