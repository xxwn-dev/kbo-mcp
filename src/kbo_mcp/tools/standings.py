from kbo_mcp.client import get_http_client
from kbo_mcp.models import StandingsResult
from kbo_mcp.parsers.standings import parse_standings_html
from datetime import date


async def fetch_standings() -> StandingsResult:
    async with get_http_client() as client:
        r = await client.get("/Record/TeamRank/TeamRankDaily.aspx")
        r.raise_for_status()

    standings = parse_standings_html(r.text)
    return StandingsResult(
        updated_at=date.today().isoformat(),
        standings=standings,
    )
