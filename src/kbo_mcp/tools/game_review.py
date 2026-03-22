import asyncio

from kbo_mcp.client import get_http_client
from kbo_mcp.models import DailyGamesResult, FullGameReview
from kbo_mcp.parsers.game_review import (
    parse_batting_lineup,
    parse_highlights,
    parse_inning_scores,
    parse_key_players,
)
from kbo_mcp.parsers.lineup import resolve_team
from kbo_mcp.tools.lineup import fetch_lineup

COMMON_PARAMS = {"groupSc": "GAME_WPA_RT", "sort": "DESC", "leId": "1"}
SR_IDS = ["0", "1", "3"]  # 정규, 시범, 포스트시즌


async def _fetch_key_players(client, method: str, game_id: str, sr_id: str) -> list:
    r = await client.post(
        f"/ws/Schedule.asmx/{method}",
        data={**COMMON_PARAMS, "srId": sr_id, "gameId": game_id},
    )
    r.raise_for_status()
    data = r.json()
    if data.get("code") != "100":
        return []
    return parse_key_players(data.get("record", []))


def _first_non_empty(results) -> list:
    for r in results:
        if isinstance(r, list) and r:
            return r
    return []


async def _fetch_key_players_for_game(client, game_id: str) -> tuple[list, list]:
    """투수·타자 키플레이어를 srId 자동 탐색으로 조회."""
    all_results = await asyncio.gather(
        *[_fetch_key_players(client, "GetKeyPlayerPitcher", game_id, sr_id) for sr_id in SR_IDS],
        *[_fetch_key_players(client, "GetKeyPlayerHitter", game_id, sr_id) for sr_id in SR_IDS],
        return_exceptions=True,
    )
    pitchers = _first_non_empty(all_results[:len(SR_IDS)])
    hitters = _first_non_empty(all_results[len(SR_IDS):])
    return pitchers, hitters


async def _fetch_box_score(client, game_id: str, sr_id: str) -> dict:
    r = await client.post(
        "/ws/Schedule.asmx/GetBoxScoreScroll",
        data={"leId": "1", "srId": sr_id, "seasonId": game_id[:4], "gameId": game_id},
    )
    r.raise_for_status()
    return r.json()


async def _fetch_scoreboard(client, game_id: str, sr_id: str) -> dict:
    r = await client.post(
        "/ws/Schedule.asmx/GetScoreBoardScroll",
        data={"leId": "1", "srId": sr_id, "seasonId": game_id[:4], "gameId": game_id},
    )
    r.raise_for_status()
    return r.json()


async def _fetch_finished_data(client, game_id: str) -> tuple[dict, dict]:
    """srId 자동 탐색으로 BoxScore + ScoreBoard 병렬 조회."""
    box_tasks = [_fetch_box_score(client, game_id, sr_id) for sr_id in SR_IDS]
    board_tasks = [_fetch_scoreboard(client, game_id, sr_id) for sr_id in SR_IDS]
    results = await asyncio.gather(*box_tasks, *board_tasks, return_exceptions=True)

    box_results = results[:len(SR_IDS)]
    board_results = results[len(SR_IDS):]

    # arrHitter가 있는 응답 선택
    box = next(
        (r for r in box_results if isinstance(r, dict) and r.get("arrHitter")),
        {},
    )
    # table2가 있는 응답 선택
    board = next(
        (r for r in board_results if isinstance(r, dict) and r.get("table2")),
        {},
    )
    return box, board


async def fetch_game(date: str, away_team: str = "", home_team: str = "") -> DailyGamesResult:
    """날짜별 KBO 경기 정보를 반환합니다.

    - 팀명 생략: 해당일 전체 경기 목록 (선발투수·점수·상태)
    - 팀명 지정: 특정 경기 상세 정보
      - 항상: WPA 키플레이어 (투수·타자)
      - 종료 후 추가: 이닝별 점수판, 타순, 하이라이트, 경기 메타
    """
    lineup_result = await fetch_lineup(date)

    if not away_team and not home_team:
        games = [
            FullGameReview(
                game_id=g.game_id,
                date=g.date,
                away_team=g.away_team,
                home_team=g.home_team,
                away_starter=g.away_starter,
                home_starter=g.home_starter,
                lineup_confirmed=g.lineup_confirmed,
                game_finished=g.game_finished,
                away_score=g.away_score,
                home_score=g.home_score,
            )
            for g in lineup_result.games
        ]
        return DailyGamesResult(date=date, games=games)

    # 특정 경기 조회
    away_full = resolve_team(away_team) if away_team else ""
    home_full = resolve_team(home_team) if home_team else ""

    def _matches(g) -> bool:
        if away_full and home_full:
            return g.away_team == away_full and g.home_team == home_full
        if away_full:
            return g.away_team == away_full or g.home_team == away_full
        if home_full:
            return g.away_team == home_full or g.home_team == home_full
        return False

    matched = next((g for g in lineup_result.games if _matches(g)), None)
    if not matched:
        team_hint = away_full or home_full
        raise ValueError(f"{date} {team_hint} 경기를 찾을 수 없습니다.")

    game_id = matched.game_id

    async with get_http_client() as client:
        pitchers, hitters = await _fetch_key_players_for_game(client, game_id)

        review = FullGameReview(
            game_id=game_id,
            date=matched.date,
            away_team=matched.away_team,
            home_team=matched.home_team,
            away_starter=matched.away_starter,
            home_starter=matched.home_starter,
            lineup_confirmed=matched.lineup_confirmed,
            game_finished=matched.game_finished,
            away_score=matched.away_score,
            home_score=matched.home_score,
            pitcher_key_players=pitchers,
            hitter_key_players=hitters,
        )

        if matched.game_finished:
            box, board = await _fetch_finished_data(client, game_id)

            if board:
                away_inn, home_inn, total = parse_inning_scores(board)
                review.venue = board.get("S_NM", "")
                review.crowd = board.get("CROWD_CN", "")
                review.start_time = board.get("START_TM", "")
                review.end_time = board.get("END_TM", "")
                review.duration = board.get("USE_TM", "")
                review.away_inning_scores = away_inn
                review.home_inning_scores = home_inn
                review.total_innings = total

            if box:
                arr_hitter = box.get("arrHitter", [])
                away_lineup, home_lineup = parse_batting_lineup(arr_hitter)
                review.away_lineup = away_lineup
                review.home_lineup = home_lineup
                table_etc = box.get("tableEtc", "")
                if table_etc:
                    review.highlights = parse_highlights(table_etc)

    return DailyGamesResult(date=date, games=[review])
