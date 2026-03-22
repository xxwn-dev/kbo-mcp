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


class LineupPlayer(BaseModel):
    order: int        # 타순 (0: 투수 등 타순 없음)
    position: str     # 포지션 (P, C, 1B, 2B, 3B, SS, LF, CF, RF, DH)
    name: str


class GameLineup(BaseModel):
    game_id: str
    date: str                        # "YYYY-MM-DD"
    away_team: str
    home_team: str
    away_starter: str                # 원정 선발 투수
    home_starter: str                # 홈 선발 투수
    lineup_confirmed: bool           # LINEUP_CK: 라인업 공개 여부
    game_finished: bool              # GAME_RESULT_CK: 경기 종료 여부
    away_score: str = ""             # 원정 점수 (경기 전이면 빈 문자열)
    home_score: str = ""             # 홈 점수
    away_lineup: list[LineupPlayer] = []
    home_lineup: list[LineupPlayer] = []


class DailyLineupResult(BaseModel):
    date: str
    games: list[GameLineup]


class KeyPlayer(BaseModel):
    rank: int
    name: str
    team: str
    wpa_pct: str   # "19.4%"
    record: str    # "5이닝 1실점 3삼진"


class BattingPlayer(BaseModel):
    order: int       # 타순 (1~9)
    position: str    # 포지션 (유, 중, 一 등)
    name: str
    is_starter: bool  # 선발 여부 (같은 타순 반복 = 교체 선수)


class GameHighlight(BaseModel):
    category: str  # "결승타", "홈런", "도루" 등
    detail: str    # "정현창(3회 무사 1,2루서 우중월 홈런)"


class FullGameReview(BaseModel):
    game_id: str
    date: str
    away_team: str
    home_team: str
    away_starter: str = ""
    home_starter: str = ""
    lineup_confirmed: bool = False
    game_finished: bool
    away_score: str = ""
    home_score: str = ""
    # 항상 조회 가능 (GetScoreBoardScroll)
    venue: str = ""
    crowd: str = ""
    # 종료 경기에만 제공
    start_time: str = ""
    end_time: str = ""
    duration: str = ""
    away_inning_scores: list[str] = []  # ["0","0","6","0","1","0","1","0","3"]
    home_inning_scores: list[str] = []
    total_innings: int = 0
    away_lineup: list[BattingPlayer] = []
    home_lineup: list[BattingPlayer] = []
    highlights: list[GameHighlight] = []
    # 팀명 지정 시 항상 조회 (GetKeyPlayer*)
    pitcher_key_players: list[KeyPlayer] = []
    hitter_key_players: list[KeyPlayer] = []


class DailyGamesResult(BaseModel):
    date: str
    games: list[FullGameReview]
