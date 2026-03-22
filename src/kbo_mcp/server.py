from mcp.server.fastmcp import FastMCP

from kbo_mcp.models import DailyGamesResult, ScheduleResult, StandingsResult
from kbo_mcp.tools.game_review import fetch_game
from kbo_mcp.tools.schedule import SeriesType, fetch_schedule
from kbo_mcp.tools.standings import fetch_standings

mcp = FastMCP(
    name="kbo-mcp",
    instructions="""KBO 프로야구 팀 순위, 경기 일정, 경기 정보를 조회합니다.

## 파라미터 처리 원칙
- 날짜(date)가 필요한 툴을 호출할 때, 사용자가 날짜를 명시하지 않았다면 반드시 어떤 날짜를 원하는지 먼저 물어보세요.
- 팀명(away_team, home_team)이 필요한데 언급되지 않았다면 어떤 팀인지 먼저 물어보세요.
- 사용자가 "오늘", "어제", "내일" 같은 상대적 표현을 쓴 경우에는 현재 날짜를 기준으로 변환해 사용하세요.
""",
)


@mcp.tool()
async def get_kbo_standings() -> StandingsResult:
    """현재 KBO 팀 순위를 반환합니다. (순위, 팀명, 경기수, 승, 패, 무, 승률, 게임차)"""
    return await fetch_standings()


@mcp.tool()
async def get_kbo_schedule(
    year: int,
    month: int,
    series: SeriesType = "regular",
) -> ScheduleResult:
    """KBO 월별 경기 일정을 반환합니다.

    Args:
        year: 조회할 연도 (예: 2026)
        month: 조회할 월 (1~12)
        series: 경기 종류 - preseason(시범경기), regular(정규시즌), postseason(포스트시즌), all(전체). 기본값은 regular
    """
    return await fetch_schedule(year, month, series)


@mcp.tool()
async def get_kbo_game(date: str, away_team: str = "", home_team: str = "") -> DailyGamesResult:
    """날짜별 KBO 경기 정보를 반환합니다.

    팀명을 생략하면 해당일 전체 경기 목록(선발투수·점수·경기상태)을 반환합니다.
    팀명을 지정하면 해당 경기의 상세 정보를 반환합니다.
    - 경기 진행 중·종료 후: WPA 키플레이어 (투수·타자)
    - 경기 종료 후 추가: 이닝별 점수판, 타순, 하이라이트, 경기 메타(구장·관중·시간)

    Args:
        date: 조회할 날짜 (YYYY-MM-DD 형식, 예: 2026-03-22)
        away_team: 원정 팀명 — 약어(KIA, LG 등) 또는 전체명·별칭(기아, 트윈스 등) 모두 허용
        home_team: 홈 팀명 — 약어(KIA, LG 등) 또는 전체명·별칭(기아, 트윈스 등) 모두 허용
    """
    return await fetch_game(date, away_team, home_team)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
