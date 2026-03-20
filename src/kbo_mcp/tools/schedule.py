from datetime import datetime
from typing import Literal

from kbo_mcp.client import get_http_client
from kbo_mcp.models import ScheduleResult
from kbo_mcp.parsers.schedule import parse_schedule_response

SCHEDULE_API = "/ws/Schedule.asmx/GetMonthSchedule"

SERIES_MAP = {
    "preseason": "1",
    "regular": "0,9,6",
    "postseason": "3,4,5,7",
}

SeriesType = Literal["preseason", "regular", "postseason"]


async def fetch_schedule(
    year: int,
    month: int,
    series: SeriesType = "regular",
) -> ScheduleResult:
    if not (2008 <= year <= datetime.now().year + 1):
        raise ValueError(f"유효하지 않은 연도입니다: {year}")
    if not (1 <= month <= 12):
        raise ValueError(f"유효하지 않은 월입니다: {month}")

    async with get_http_client() as client:
        r = await client.post(
            SCHEDULE_API,
            data={
                "leId": "1",
                "srIdList": SERIES_MAP[series],
                "seasonId": str(year),
                "gameMonth": f"{month:02d}",
                "teamId": "0",
            },
        )
        r.raise_for_status()

    games = parse_schedule_response(r.json(), year, month)
    return ScheduleResult(year=year, month=month, games=games)
