from mcp.server.fastmcp import FastMCP

from kbo_mcp.models import ScheduleResult, StandingsResult
from kbo_mcp.tools.schedule import SeriesType, fetch_schedule
from kbo_mcp.tools.standings import fetch_standings

mcp = FastMCP(
    name="kbo-mcp",
    instructions="KBO 프로야구 팀 순위와 월별 경기 일정을 조회합니다.",
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


def main():
    mcp.run()


if __name__ == "__main__":
    main()
