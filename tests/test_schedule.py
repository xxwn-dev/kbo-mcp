"""통합 테스트: 실제 KBO API를 호출해 fetch_schedule 전체 흐름을 검증합니다.

실행:
    uv run pytest tests/test_schedule.py -v -m integration
"""

import pytest

from kbo_mcp.models import GameSchedule, ScheduleResult
from kbo_mcp.tools.schedule import fetch_schedule

pytestmark = pytest.mark.integration


# ── 정상 케이스 ───────────────────────────────────────────────

async def test_regular_returns_schedule_result():
    result = await fetch_schedule(2026, 3, series="regular")
    assert isinstance(result, ScheduleResult)
    assert result.year == 2026
    assert result.month == 3


async def test_regular_games_are_game_schedule_instances():
    result = await fetch_schedule(2026, 3, series="regular")
    assert all(isinstance(g, GameSchedule) for g in result.games)


async def test_all_series_includes_more_games_than_regular():
    regular = await fetch_schedule(2026, 3, series="regular")
    all_ = await fetch_schedule(2026, 3, series="all")
    # 3월에는 시범경기 + 정규시즌이 모두 존재
    assert len(all_.games) >= len(regular.games)


async def test_all_series_games_sorted_by_date():
    result = await fetch_schedule(2026, 3, series="all")
    dates = [g.date for g in result.games]
    assert dates == sorted(dates)


async def test_preseason_returns_results():
    result = await fetch_schedule(2026, 3, series="preseason")
    assert isinstance(result, ScheduleResult)
    assert len(result.games) > 0


async def test_game_fields_are_non_empty():
    result = await fetch_schedule(2026, 3, series="regular")
    for game in result.games:
        assert game.date, "date가 비어있음"
        assert game.away_team, "away_team이 비어있음"
        assert game.home_team, "home_team이 비어있음"
        assert game.venue, "venue가 비어있음"


# ── 유효성 검증 ───────────────────────────────────────────────

async def test_invalid_year_raises_value_error():
    with pytest.raises(ValueError, match="연도"):
        await fetch_schedule(2000, 3)


async def test_invalid_month_raises_value_error():
    with pytest.raises(ValueError, match="월"):
        await fetch_schedule(2026, 13)


async def test_invalid_month_zero_raises_value_error():
    with pytest.raises(ValueError):
        await fetch_schedule(2026, 0)
