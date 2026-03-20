from pydantic import BaseModel


class TeamStanding(BaseModel):
    rank: int
    team: str
    games: int
    wins: int
    losses: int
    draws: int
    win_pct: str      # "0.833" 형태 — KBO 표기 그대로 유지
    games_behind: str  # 1위는 "-", 이하 "1.5" 형태


class StandingsResult(BaseModel):
    updated_at: str           # "YYYY-MM-DD"
    standings: list[TeamStanding]


class GameSchedule(BaseModel):
    date: str                 # "YYYY-MM-DD"
    away_team: str
    home_team: str
    venue: str                # 잠실, 문학, 대구 등
    status: str = ""          # 비어있으면 정상, "우천취소" 등


class ScheduleResult(BaseModel):
    year: int
    month: int
    games: list[GameSchedule]
