"""단위 테스트: 파서 함수를 네트워크 없이 검증합니다."""

import json

from kbo_mcp.parsers.game_review import (
    parse_batting_lineup,
    parse_highlights,
    parse_inning_scores,
    parse_key_players,
)
from kbo_mcp.parsers.lineup import parse_game_list, resolve_team
from kbo_mcp.parsers.schedule import parse_schedule_response
from kbo_mcp.parsers.standings import parse_standings_html


# ── 일정 파서 ────────────────────────────────────────────────

SAMPLE_SCHEDULE_RESPONSE = {
    "rows": [
        {
            "row": [
                {
                    "Text": """
                        <ul>
                            <li class="dayNum">22</li>
                            <li>한화 : 롯데 [사직]</li>
                            <li>LG : KT [잠실]</li>
                        </ul>
                    """
                },
                {
                    "Text": """
                        <ul>
                            <li class="dayNum">23</li>
                            <li>NC : 한화 [대전] 우천취소</li>
                        </ul>
                    """
                },
                {"Text": ""},  # 빈 셀 (월 경계 등)
            ]
        }
    ]
}


def test_parse_schedule_returns_correct_count():
    games = parse_schedule_response(SAMPLE_SCHEDULE_RESPONSE, 2026, 3)
    assert len(games) == 3


def test_parse_schedule_maps_team_names():
    games = parse_schedule_response(SAMPLE_SCHEDULE_RESPONSE, 2026, 3)
    # 약어 → 전체 팀명 매핑 확인
    assert games[0].away_team == "한화 이글스"
    assert games[0].home_team == "롯데 자이언츠"


def test_parse_schedule_date_format():
    games = parse_schedule_response(SAMPLE_SCHEDULE_RESPONSE, 2026, 3)
    assert games[0].date == "2026-03-22"
    assert games[2].date == "2026-03-23"


def test_parse_schedule_status():
    games = parse_schedule_response(SAMPLE_SCHEDULE_RESPONSE, 2026, 3)
    assert games[1].status == ""          # 정상 경기
    assert games[2].status == "우천취소"


def test_parse_schedule_skips_empty_cells():
    # 빈 Text가 있어도 예외 없이 처리
    games = parse_schedule_response(SAMPLE_SCHEDULE_RESPONSE, 2026, 3)
    assert all(g.date for g in games)


def test_parse_schedule_empty_response():
    games = parse_schedule_response({"rows": []}, 2026, 3)
    assert games == []


# ── 순위 파서 ────────────────────────────────────────────────

SAMPLE_STANDINGS_HTML = """
<html><body>
<table class="tData">
  <tbody>
    <tr>
      <td>1</td><td>KIA</td><td>1</td><td>1</td><td>0</td><td>0</td><td>1.000</td><td>-</td>
    </tr>
    <tr>
      <td>2</td><td>LG</td><td>1</td><td>0</td><td>1</td><td>0</td><td>0.000</td><td>1</td>
    </tr>
  </tbody>
</table>
</body></html>
"""


def test_parse_standings_count():
    standings = parse_standings_html(SAMPLE_STANDINGS_HTML)
    assert len(standings) == 2


def test_parse_standings_rank_and_team():
    standings = parse_standings_html(SAMPLE_STANDINGS_HTML)
    assert standings[0].rank == 1
    assert standings[0].team == "KIA"


def test_parse_standings_numeric_fields():
    standings = parse_standings_html(SAMPLE_STANDINGS_HTML)
    s = standings[0]
    assert s.wins == 1
    assert s.losses == 0
    assert s.win_pct == "1.000"
    assert s.games_behind == "-"


def test_parse_standings_empty_table():
    html = '<html><body><table class="tData"><tbody></tbody></table></body></html>'
    standings = parse_standings_html(html)
    assert standings == []


# ── 라인업 파서 ───────────────────────────────────────────────

SAMPLE_GAME_LIST = [
    {
        "G_ID": "20260322HTOB0",
        "AWAY_NM": "KIA",
        "HOME_NM": "두산",
        "T_PIT_P_NM": "양현종",
        "B_PIT_P_NM": "곽빈",
        "LINEUP_CK": "1",
        "GAME_RESULT_CK": "1",
        "T_SCORE_CN": "5",
        "B_SCORE_CN": "3",
    },
    {
        "G_ID": "20260322HHLT0",
        "AWAY_NM": "한화",
        "HOME_NM": "롯데",
        "T_PIT_P_NM": None,
        "B_PIT_P_NM": None,
        "LINEUP_CK": "0",
        "GAME_RESULT_CK": "0",
        "T_SCORE_CN": None,
        "B_SCORE_CN": None,
    },
]


def test_parse_game_list_count():
    games = parse_game_list(SAMPLE_GAME_LIST, "2026-03-22")
    assert len(games) == 2


def test_parse_game_list_team_names():
    games = parse_game_list(SAMPLE_GAME_LIST, "2026-03-22")
    assert games[0].away_team == "KIA 타이거즈"
    assert games[0].home_team == "두산 베어스"
    assert games[1].away_team == "한화 이글스"
    assert games[1].home_team == "롯데 자이언츠"


def test_parse_game_list_starters():
    games = parse_game_list(SAMPLE_GAME_LIST, "2026-03-22")
    assert games[0].away_starter == "양현종"
    assert games[0].home_starter == "곽빈"


def test_parse_game_list_null_starters():
    """T_PIT_P_NM / B_PIT_P_NM 이 None 이면 빈 문자열로 변환."""
    games = parse_game_list(SAMPLE_GAME_LIST, "2026-03-22")
    assert games[1].away_starter == ""
    assert games[1].home_starter == ""


def test_parse_game_list_lineup_confirmed():
    games = parse_game_list(SAMPLE_GAME_LIST, "2026-03-22")
    assert games[0].lineup_confirmed is True
    assert games[1].lineup_confirmed is False


def test_parse_game_list_game_finished():
    games = parse_game_list(SAMPLE_GAME_LIST, "2026-03-22")
    assert games[0].game_finished is True
    assert games[1].game_finished is False


def test_parse_game_list_scores():
    games = parse_game_list(SAMPLE_GAME_LIST, "2026-03-22")
    assert games[0].away_score == "5"
    assert games[0].home_score == "3"
    assert games[1].away_score == ""
    assert games[1].home_score == ""


def test_parse_game_list_date():
    games = parse_game_list(SAMPLE_GAME_LIST, "2026-03-22")
    assert all(g.date == "2026-03-22" for g in games)


def test_parse_game_list_empty():
    games = parse_game_list([], "2026-03-22")
    assert games == []


def test_resolve_team_display_name():
    assert resolve_team("KIA") == "KIA 타이거즈"
    assert resolve_team("두산") == "두산 베어스"


def test_resolve_team_internal_code():
    assert resolve_team("HT") == "KIA 타이거즈"
    assert resolve_team("OB") == "두산 베어스"


def test_resolve_team_unknown_passthrough():
    """알 수 없는 값은 그대로 반환."""
    assert resolve_team("UNKNOWN") == "UNKNOWN"


# ── 키플레이어 파서 ─────────────────────────────────────────────

SAMPLE_KEY_PLAYERS = [
    {
        "RANK_NO": "1",
        "P_NM": "양현종",
        "T_ID": "HT",
        "RECORD_IF": "19.4%</br>(5이닝 1실점 3삼진)",
    },
    {
        "RANK_NO": "2",
        "P_NM": "고영우",
        "T_ID": "OB",
        "RECORD_IF": "15.2%</br>(3타수 2안타 1타점)",
    },
]


def test_parse_key_players_count():
    players = parse_key_players(SAMPLE_KEY_PLAYERS)
    assert len(players) == 2


def test_parse_key_players_name_and_rank():
    players = parse_key_players(SAMPLE_KEY_PLAYERS)
    assert players[0].rank == 1
    assert players[0].name == "양현종"


def test_parse_key_players_team_resolved():
    players = parse_key_players(SAMPLE_KEY_PLAYERS)
    assert players[0].team == "KIA 타이거즈"
    assert players[1].team == "두산 베어스"


def test_parse_key_players_wpa_pct_and_record():
    players = parse_key_players(SAMPLE_KEY_PLAYERS)
    assert players[0].wpa_pct == "19.4%"
    assert players[0].record == "5이닝 1실점 3삼진"


def test_parse_key_players_empty():
    assert parse_key_players([]) == []


# ── 이닝별 점수판 파서 ──────────────────────────────────────────

SAMPLE_SCOREBOARD = {
    "table2": json.dumps({
        "rows": [
            {"row": [{"Text": "0"}, {"Text": "0"}, {"Text": "3"}, {"Text": "0"}, {"Text": "-"}]},
            {"row": [{"Text": "1"}, {"Text": "0"}, {"Text": "0"}, {"Text": "1"}, {"Text": "-"}]},
        ]
    }),
    "S_NM": "잠실",
    "CROWD_CN": "15000",
    "START_TM": "18:30",
    "END_TM": "21:15",
    "USE_TM": "2시간 45분",
}


def test_parse_inning_scores_away_scores():
    away, home, total = parse_inning_scores(SAMPLE_SCOREBOARD)
    assert away == ["0", "0", "3", "0"]  # "-" 제거


def test_parse_inning_scores_home_scores():
    away, home, total = parse_inning_scores(SAMPLE_SCOREBOARD)
    assert home == ["1", "0", "0", "1"]


def test_parse_inning_scores_total_innings():
    away, home, total = parse_inning_scores(SAMPLE_SCOREBOARD)
    assert total == 4


def test_parse_inning_scores_empty_table2():
    result = parse_inning_scores({"table2": json.dumps({"rows": []})})
    assert result == ([], [], 0)


def test_parse_inning_scores_missing_key_returns_empty():
    result = parse_inning_scores({})
    assert result == ([], [], 0)


# ── 타순 파서 ─────────────────────────────────────────────────

def _make_table1(rows: list[tuple]) -> str:
    """(order, position, name) 튜플 리스트로 table1 JSON 문자열 생성."""
    return json.dumps({
        "rows": [
            {"row": [{"Text": str(o)}, {"Text": pos}, {"Text": name}]}
            for o, pos, name in rows
        ]
    })


SAMPLE_ARR_HITTER = [
    {
        "table1": _make_table1([
            (1, "CF", "이정후"),
            (2, "SS", "오지환"),
            (3, "RF", "박해민"),
            (4, "1B", "채은성"),
            (5, "LF", "김현수"),
            (6, "3B", "문보경"),
            (7, "C", "박동원"),
            (8, "2B", "신민재"),
            (9, "DH", "홍창기"),
            (4, "1B", "문성주"),  # 교체 선수 (4번 타자)
        ])
    },
    {
        "table1": _make_table1([
            (1, "CF", "정수빈"),
            (2, "LF", "김재환"),
            (3, "1B", "양석환"),
            (4, "RF", "페르난데스"),
            (5, "C", "박세혁"),
            (6, "DH", "강승호"),
            (7, "2B", "허경민"),
            (8, "SS", "박계범"),
            (9, "3B", "조수행"),
        ])
    },
]


def test_parse_batting_lineup_away_count():
    away, home = parse_batting_lineup(SAMPLE_ARR_HITTER)
    assert len(away) == 10  # 선발 9명 + 교체 1명


def test_parse_batting_lineup_home_count():
    away, home = parse_batting_lineup(SAMPLE_ARR_HITTER)
    assert len(home) == 9


def test_parse_batting_lineup_starter_flag():
    away, _ = parse_batting_lineup(SAMPLE_ARR_HITTER)
    # 첫 번째 4번 타자는 선발
    assert away[3].is_starter is True
    assert away[3].name == "채은성"
    # 교체 선수 (마지막 행, 같은 타순 4)
    assert away[9].is_starter is False
    assert away[9].name == "문성주"


def test_parse_batting_lineup_names():
    away, _ = parse_batting_lineup(SAMPLE_ARR_HITTER)
    assert away[0].name == "이정후"
    assert away[0].order == 1
    assert away[0].position == "CF"


def test_parse_batting_lineup_insufficient_data():
    away, home = parse_batting_lineup([])
    assert away == []
    assert home == []


def test_parse_batting_lineup_single_team():
    away, home = parse_batting_lineup(SAMPLE_ARR_HITTER[:1])
    assert away == []
    assert home == []


# ── 하이라이트 파서 ─────────────────────────────────────────────

SAMPLE_TABLE_ETC = json.dumps({
    "rows": [
        {"row": [{"Text": "결승타"}, {"Text": "이정후(5회 무사 1,3루서 중전 적시타)"}]},
        {"row": [{"Text": "홈런"}, {"Text": "김재환 1호(3회 2점)"}]},
        {"row": [{"Text": "도루"}, {"Text": "신민재(6회)"}]},
    ]
})


def test_parse_highlights_count():
    highlights = parse_highlights(SAMPLE_TABLE_ETC)
    assert len(highlights) == 3


def test_parse_highlights_category_and_detail():
    highlights = parse_highlights(SAMPLE_TABLE_ETC)
    assert highlights[0].category == "결승타"
    assert "이정후" in highlights[0].detail
    assert highlights[1].category == "홈런"


def test_parse_highlights_empty_rows():
    highlights = parse_highlights(json.dumps({"rows": []}))
    assert highlights == []


def test_parse_highlights_invalid_json():
    highlights = parse_highlights("not-json")
    assert highlights == []
