"""통합 테스트: 실제 KBO API를 호출해 fetch_game 전체 흐름을 검증합니다.

실행:
    uv run pytest tests/test_game_review.py -v -m integration
"""

import pytest

from kbo_mcp.models import DailyGamesResult, FullGameReview
from kbo_mcp.tools.game_review import fetch_game

pytestmark = pytest.mark.integration

TODAY = "2026-03-22"       # 시범경기 + 정규시즌 혼재 날짜
FINISHED_DATE = "2026-03-21"   # KBO 플랜 API 노트에서 확인된 종료 경기 날짜
FINISHED_AWAY = "KIA"          # 20260321HTOB0 — KIA(HT) vs 두산(OB)
FINISHED_HOME = "두산"


# ── 팀명 없이 날짜만 → 전체 경기 목록 반환 ───────────────────────

async def test_date_only_returns_daily_games_result():
    result = await fetch_game(TODAY)
    assert isinstance(result, DailyGamesResult)


async def test_date_only_date_field_matches_input():
    result = await fetch_game(TODAY)
    assert result.date == TODAY


async def test_date_only_returns_non_empty_games_list():
    result = await fetch_game(TODAY)
    assert len(result.games) > 0


async def test_date_only_games_are_full_game_review_instances():
    result = await fetch_game(TODAY)
    assert all(isinstance(g, FullGameReview) for g in result.games)


async def test_date_only_games_have_team_names():
    result = await fetch_game(TODAY)
    for game in result.games:
        assert game.away_team, f"away_team 비어있음: {game.game_id}"
        assert game.home_team, f"home_team 비어있음: {game.game_id}"


async def test_date_only_games_have_non_empty_game_id():
    result = await fetch_game(TODAY)
    for game in result.games:
        assert game.game_id, "game_id 비어있음"


async def test_date_only_key_players_are_not_fetched():
    """팀명 없이 조회하면 키플레이어를 별도 호출하지 않으므로 빈 리스트."""
    result = await fetch_game(TODAY)
    for game in result.games:
        assert game.pitcher_key_players == []
        assert game.hitter_key_players == []


# ── 팀명 한 쪽만 입력 → 원정·홈 무관 경기 매칭 ─────────────────

async def test_away_team_only_finds_game():
    """away_team만 지정해도 해당 팀이 홈이어도 매칭."""
    result = await fetch_game(FINISHED_DATE, away_team=FINISHED_AWAY)
    assert len(result.games) == 1
    game = result.games[0]
    assert game.away_team == "KIA 타이거즈" or game.home_team == "KIA 타이거즈"


async def test_home_team_only_finds_game():
    """home_team만 지정해도 해당 팀이 원정이어도 매칭."""
    result = await fetch_game(FINISHED_DATE, home_team=FINISHED_HOME)
    assert len(result.games) == 1
    game = result.games[0]
    assert game.away_team == "두산 베어스" or game.home_team == "두산 베어스"


async def test_single_team_returns_one_game():
    """한 팀 지정 시 정확히 1경기만 반환."""
    result = await fetch_game(FINISHED_DATE, away_team=FINISHED_AWAY)
    assert len(result.games) == 1


async def test_single_team_has_key_player_fields():
    """팀명 지정 시 키플레이어 필드 존재."""
    result = await fetch_game(FINISHED_DATE, away_team=FINISHED_AWAY)
    game = result.games[0]
    assert isinstance(game.pitcher_key_players, list)
    assert isinstance(game.hitter_key_players, list)


# ── 진행 중 경기 → 기본 정보 + 키플레이어 구조 검증 ──────────────
# 경기 시간에 따라 today 경기가 진행 중일 수도 있음.
# 팀명 지정 시 fetch_game이 키플레이어를 조회하는 코드 경로를 검증한다.

async def test_game_with_teams_returns_single_full_game_review():
    result = await fetch_game(FINISHED_DATE, away_team=FINISHED_AWAY, home_team=FINISHED_HOME)
    assert len(result.games) == 1
    assert isinstance(result.games[0], FullGameReview)


async def test_game_with_teams_has_correct_team_names():
    result = await fetch_game(FINISHED_DATE, away_team=FINISHED_AWAY, home_team=FINISHED_HOME)
    game = result.games[0]
    assert game.away_team == "KIA 타이거즈"
    assert game.home_team == "두산 베어스"


async def test_game_with_teams_key_players_are_lists():
    result = await fetch_game(FINISHED_DATE, away_team=FINISHED_AWAY, home_team=FINISHED_HOME)
    game = result.games[0]
    assert isinstance(game.pitcher_key_players, list)
    assert isinstance(game.hitter_key_players, list)


# ── 종료 경기 → 풀 리뷰 (이닝점수 + 타순 + 하이라이트) ──────────

async def test_finished_game_is_marked_finished():
    result = await fetch_game(FINISHED_DATE, away_team=FINISHED_AWAY, home_team=FINISHED_HOME)
    game = result.games[0]
    assert game.game_finished is True


async def test_finished_game_has_inning_scores():
    result = await fetch_game(FINISHED_DATE, away_team=FINISHED_AWAY, home_team=FINISHED_HOME)
    game = result.games[0]
    assert len(game.away_inning_scores) > 0
    assert len(game.home_inning_scores) > 0


async def test_finished_game_total_innings_matches_inning_score_length():
    result = await fetch_game(FINISHED_DATE, away_team=FINISHED_AWAY, home_team=FINISHED_HOME)
    game = result.games[0]
    assert game.total_innings == max(
        len(game.away_inning_scores), len(game.home_inning_scores)
    )


async def test_finished_game_has_batting_lineup():
    result = await fetch_game(FINISHED_DATE, away_team=FINISHED_AWAY, home_team=FINISHED_HOME)
    game = result.games[0]
    assert len(game.away_lineup) > 0
    assert len(game.home_lineup) > 0


async def test_finished_game_has_nine_starters_per_team():
    """각 팀에 선발 타자 9명이 포함되어야 함."""
    result = await fetch_game(FINISHED_DATE, away_team=FINISHED_AWAY, home_team=FINISHED_HOME)
    game = result.games[0]
    away_starters = [p for p in game.away_lineup if p.is_starter]
    home_starters = [p for p in game.home_lineup if p.is_starter]
    assert len(away_starters) == 9
    assert len(home_starters) == 9


async def test_finished_game_has_highlights():
    result = await fetch_game(FINISHED_DATE, away_team=FINISHED_AWAY, home_team=FINISHED_HOME)
    game = result.games[0]
    assert len(game.highlights) > 0


async def test_finished_game_highlights_have_category_and_detail():
    result = await fetch_game(FINISHED_DATE, away_team=FINISHED_AWAY, home_team=FINISHED_HOME)
    game = result.games[0]
    for h in game.highlights:
        assert h.category, "highlight category 비어있음"
        assert h.detail, "highlight detail 비어있음"


async def test_finished_game_has_venue():
    result = await fetch_game(FINISHED_DATE, away_team=FINISHED_AWAY, home_team=FINISHED_HOME)
    game = result.games[0]
    assert game.venue, "venue 비어있음"


async def test_finished_game_has_crowd():
    result = await fetch_game(FINISHED_DATE, away_team=FINISHED_AWAY, home_team=FINISHED_HOME)
    game = result.games[0]
    assert game.crowd, "crowd 비어있음"


async def test_finished_game_has_key_players():
    """종료 경기에는 키플레이어가 반드시 존재해야 함."""
    result = await fetch_game(FINISHED_DATE, away_team=FINISHED_AWAY, home_team=FINISHED_HOME)
    game = result.games[0]
    assert len(game.pitcher_key_players) > 0
    assert len(game.hitter_key_players) > 0


async def test_finished_game_key_player_fields():
    result = await fetch_game(FINISHED_DATE, away_team=FINISHED_AWAY, home_team=FINISHED_HOME)
    game = result.games[0]
    for kp in game.pitcher_key_players + game.hitter_key_players:
        assert kp.name, "키플레이어 name 비어있음"
        assert kp.wpa_pct, "키플레이어 wpa_pct 비어있음"


# ── 에러 케이스 ──────────────────────────────────────────────────

async def test_unknown_team_raises_value_error():
    with pytest.raises(ValueError):
        await fetch_game(TODAY, away_team="존재하지않는팀")
