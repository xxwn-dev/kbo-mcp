from bs4 import BeautifulSoup

from kbo_mcp.models import TeamStanding


def parse_standings_html(html: str) -> list[TeamStanding]:
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", class_="tData")

    if not table:
        return []

    standings = []
    for row in table.find("tbody").find_all("tr"):
        cells = [td.text.strip() for td in row.find_all("td")]
        if len(cells) < 8:
            continue
        standings.append(TeamStanding(
            rank=int(cells[0]),
            team=cells[1],
            games=int(cells[2]),
            wins=int(cells[3]),
            losses=int(cells[4]),
            draws=int(cells[5]),
            win_pct=cells[6],
            games_behind=cells[7],
        ))

    return standings
