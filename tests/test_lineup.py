"""통합 테스트: 실제 KBO API를 호출해 fetch_lineup 전체 흐름을 검증합니다.

실행:
    uv run pytest tests/test_lineup.py -v -m integration
"""

import pytest

from kbo_mcp.models import DailyLineupResult, GameLineup
from kbo_mcp.tools.lineup import fetch_lineup

pytestmark = pytest.mark.integration

TODAY = "2026-03-22"  # 오늘 날짜 (시범경기 + 정규시즌 혼재)
PRESEASON_DATE = "2026-03-15"  # 시범경기만 있는 날짜


# ── 정상 케이스 ───────────────────────────────────────────────

async def test_returns_daily_lineup_result():
    result = await fetch_lineup(TODAY)
    assert isinstance(result, DailyLineupResult)


async def test_date_field_matches_input():
    result = await fetch_lineup(TODAY)
    assert result.date == TODAY


async def test_games_are_game_lineup_instances():
    result = await fetch_lineup(TODAY)
    assert all(isinstance(g, GameLineup) for g in result.games)


async def test_games_have_non_empty_team_names():
    result = await fetch_lineup(TODAY)
    for game in result.games:
        assert game.away_team, f"away_team 비어있음: {game.game_id}"
        assert game.home_team, f"home_team 비어있음: {game.game_id}"


async def test_games_have_non_empty_game_id():
    result = await fetch_lineup(TODAY)
    for game in result.games:
        assert game.game_id, "game_id 비어있음"


async def test_no_duplicate_game_ids():
    """정규/시범 병렬 조회 후 중복 제거 로직 검증."""
    result = await fetch_lineup(TODAY)
    ids = [g.game_id for g in result.games]
    assert len(ids) == len(set(ids)), "중복 game_id 발견"


async def test_preseason_date_returns_games():
    result = await fetch_lineup(PRESEASON_DATE)
    assert isinstance(result, DailyLineupResult)
    assert len(result.games) > 0


async def test_finished_games_have_scores():
    result = await fetch_lineup(TODAY)
    finished = [g for g in result.games if g.game_finished]
    for game in finished:
        assert game.away_score != "" or game.home_score != "", (
            f"종료 경기인데 점수 없음: {game.game_id}"
        )


# ── 유효성 검증 ───────────────────────────────────────────────

async def test_invalid_date_format_raises_value_error():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        await fetch_lineup("20260322")


async def test_invalid_date_string_raises_value_error():
    with pytest.raises(ValueError):
        await fetch_lineup("2026-13-01")
