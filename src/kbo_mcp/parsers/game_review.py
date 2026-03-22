import json
import re

from kbo_mcp.models import BattingPlayer, GameHighlight, KeyPlayer
from kbo_mcp.parsers.lineup import resolve_team

# "19.4%</br>(5이닝 1실점 3삼진)" → wpa_pct="19.4%", record="5이닝 1실점 3삼진"
_RECORD_IF_RE = re.compile(r"([^<]+)</br>\(([^)]+)\)")


def _parse_record_if(value: str) -> tuple[str, str]:
    m = _RECORD_IF_RE.search(value)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    cleaned = re.sub(r"<[^>]+>", " ", value).strip()
    return cleaned, ""


def parse_key_players(data: list[dict]) -> list[KeyPlayer]:
    players = []
    for p in data:
        wpa_pct, record = _parse_record_if(p.get("RECORD_IF", ""))
        players.append(KeyPlayer(
            rank=int(p.get("RANK_NO", 0)),
            name=p.get("P_NM", "").strip(),
            team=resolve_team(p.get("T_ID", "")),
            wpa_pct=wpa_pct,
            record=record,
        ))
    return players


def parse_inning_scores(scoreboard: dict) -> tuple[list[str], list[str], int]:
    """GetScoreBoardScroll → (away_inning_scores, home_inning_scores, total_innings)

    table2.rows[0] = 원정 이닝점수, rows[1] = 홈 이닝점수.
    '-' 는 미사용 이닝이므로 제거.
    """
    try:
        table2 = json.loads(scoreboard["table2"])
        rows = table2.get("rows", [])
        if len(rows) < 2:
            return [], [], 0
        away_scores = [c["Text"] for c in rows[0]["row"] if c["Text"] != "-"]
        home_scores = [c["Text"] for c in rows[1]["row"] if c["Text"] != "-"]
        total = max(len(away_scores), len(home_scores))
        return away_scores, home_scores, total
    except (KeyError, json.JSONDecodeError):
        return [], [], 0


def parse_batting_lineup(arr_hitter: list) -> tuple[list[BattingPlayer], list[BattingPlayer]]:
    """arrHitter[0]=원정, arrHitter[1]=홈 → (away_lineup, home_lineup)

    같은 타순 두 번째 등장 = 교체 선수 (is_starter=False).
    """
    def _parse_one(table1_json: str) -> list[BattingPlayer]:
        data = json.loads(table1_json)
        rows = data.get("rows", [])
        seen: set[int] = set()
        players = []
        for row in rows:
            cells = [c["Text"] for c in row["row"]]
            if len(cells) < 3:
                continue
            order = int(cells[0]) if cells[0].isdigit() else 0
            position = cells[1]
            name = cells[2]
            is_starter = order not in seen
            if order > 0:
                seen.add(order)
            players.append(BattingPlayer(
                order=order, position=position, name=name, is_starter=is_starter,
            ))
        return players

    if len(arr_hitter) < 2:
        return [], []
    return (
        _parse_one(arr_hitter[0]["table1"]),
        _parse_one(arr_hitter[1]["table1"]),
    )


def parse_highlights(table_etc_json: str) -> list[GameHighlight]:
    """tableEtc → list[GameHighlight]

    각 row: [카테고리(th), 내용] 쌍.
    """
    try:
        data = json.loads(table_etc_json)
        highlights = []
        for row in data.get("rows", []):
            cells = [c["Text"] for c in row["row"]]
            if len(cells) >= 2:
                highlights.append(GameHighlight(category=cells[0], detail=cells[1]))
        return highlights
    except (json.JSONDecodeError, KeyError):
        return []
