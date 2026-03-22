import asyncio
from datetime import datetime

from kbo_mcp.client import get_http_client
from kbo_mcp.models import DailyLineupResult, GameLineup
from kbo_mcp.parsers.lineup import parse_game_list

GAME_LIST_API = "/ws/Main.asmx/GetKboGameList"

SR_IDS = ["0", "1"]  # 정규시즌, 시범경기


async def _fetch_game_list(client, date_param: str, sr_id: str) -> list[GameLineup]:
    r = await client.post(
        GAME_LIST_API,
        data={"date": date_param, "leId": "1", "srId": sr_id},
    )
    r.raise_for_status()
    data = r.json()
    game_list = data.get("game", [])
    date_str = f"{date_param[:4]}-{date_param[4:6]}-{date_param[6:]}"
    return parse_game_list(game_list, date_str)


async def fetch_lineup(date: str) -> DailyLineupResult:
    """날짜(YYYY-MM-DD)로 해당일 전체 경기 정보 및 선발 투수 조회.

    정규시즌·시범경기를 모두 조회하여 합산 반환합니다.
    타자 타순은 KBO API에서 미제공 — 선발 투수, 점수, 경기 상태를 포함합니다.
    """
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"날짜 형식이 올바르지 않습니다 (YYYY-MM-DD): {date}")

    date_param = dt.strftime("%Y%m%d")

    async with get_http_client() as client:
        results = await asyncio.gather(
            *[_fetch_game_list(client, date_param, sr_id) for sr_id in SR_IDS],
            return_exceptions=True,
        )

    games: list[GameLineup] = []
    for r in results:
        if isinstance(r, list):
            games.extend(r)

    # game_id 기준 중복 제거 후 날짜순 정렬
    seen: set[str] = set()
    unique_games = []
    for g in games:
        if g.game_id not in seen:
            seen.add(g.game_id)
            unique_games.append(g)

    return DailyLineupResult(date=date, games=unique_games)
