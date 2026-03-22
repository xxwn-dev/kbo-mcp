from kbo_mcp.models import GameLineup

# GetKboGameList AWAY_NM/HOME_NM 값과 GetKeyPlayer T_ID 값을 모두 커버
TEAM_MAP = {
    # AWAY_NM / HOME_NM (표시명)
    "KIA": "KIA 타이거즈",
    "기아": "KIA 타이거즈",
    "타이거즈": "KIA 타이거즈",
    "두산": "두산 베어스",
    "베어스": "두산 베어스",
    "한화": "한화 이글스",
    "이글스": "한화 이글스",
    "롯데": "롯데 자이언츠",
    "자이언츠": "롯데 자이언츠",
    "LG": "LG 트윈스",
    "엘지": "LG 트윈스",
    "트윈스": "LG 트윈스",
    "삼성": "삼성 라이온즈",
    "라이온즈": "삼성 라이온즈",
    "NC": "NC 다이노스",
    "엔씨": "NC 다이노스",
    "다이노스": "NC 다이노스",
    "KT": "KT 위즈",
    "케이티": "KT 위즈",
    "위즈": "KT 위즈",
    "키움": "키움 히어로즈",
    "히어로즈": "키움 히어로즈",
    "넥센": "키움 히어로즈",
    "SSG": "SSG 랜더스",
    "랜더스": "SSG 랜더스",
    "에스에스지": "SSG 랜더스",
    # T_ID / AWAY_ID / HOME_ID (내부 코드)
    "HT": "KIA 타이거즈",
    "OB": "두산 베어스",
    "HH": "한화 이글스",
    "LT": "롯데 자이언츠",
    "WO": "키움 히어로즈",
    "SK": "SSG 랜더스",
    "SS": "삼성 라이온즈",
    # LG, NC, KT 는 표시명과 코드가 동일
}


def resolve_team(value: str) -> str:
    return TEAM_MAP.get(value, value)


def parse_game_list(data: list[dict], date: str) -> list[GameLineup]:
    games = []
    for g in data:
        away_score = g.get("T_SCORE_CN") or ""
        home_score = g.get("B_SCORE_CN") or ""
        games.append(GameLineup(
            game_id=g.get("G_ID", ""),
            date=date,
            away_team=resolve_team(g.get("AWAY_NM", "")),
            home_team=resolve_team(g.get("HOME_NM", "")),
            away_starter=(g.get("T_PIT_P_NM") or "").strip(),
            home_starter=(g.get("B_PIT_P_NM") or "").strip(),
            lineup_confirmed=int(g.get("LINEUP_CK") or 0) > 0,
            game_finished=int(g.get("GAME_RESULT_CK") or 0) > 0,
            away_score=str(away_score),
            home_score=str(home_score),
        ))
    return games
