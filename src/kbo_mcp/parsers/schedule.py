import re

from bs4 import BeautifulSoup

from kbo_mcp.models import GameSchedule

TEAM_MAP = {
    "KT": "KT 위즈",
    "LG": "LG 트윈스",
    "두산": "두산 베어스",
    "삼성": "삼성 라이온즈",
    "SSG": "SSG 랜더스",
    "롯데": "롯데 자이언츠",
    "한화": "한화 이글스",
    "키움": "키움 히어로즈",
    "NC": "NC 다이노스",
    "KIA": "KIA 타이거즈",
}

GAME_PATTERN = re.compile(r"(\S+)\s*:\s*(\S+)\s*\[(.+?)\](?:\s*(.+))?")


def parse_schedule_response(data: dict, year: int, month: int) -> list[GameSchedule]:
    games = []

    for week in data.get("rows", []):
        for day_cell in week.get("row", []):
            text = day_cell.get("Text", "")
            if not text.strip():
                continue

            soup = BeautifulSoup(text, "lxml")

            day_li = soup.find("li", class_="dayNum")
            if not day_li or not day_li.text.strip().isdigit():
                continue

            day = int(day_li.text.strip())
            date_str = f"{year}-{month:02d}-{day:02d}"

            for li in soup.find_all("li"):
                if li.get("class"):  # dayNum 등 class 있는 li 건너뜀
                    continue
                match = GAME_PATTERN.match(li.text.strip())
                if not match:
                    continue
                away, home, venue, status = match.groups()
                games.append(GameSchedule(
                    date=date_str,
                    away_team=TEAM_MAP.get(away, away),
                    home_team=TEAM_MAP.get(home, home),
                    venue=venue.strip(),
                    status=(status or "").strip(),
                ))

    return games
