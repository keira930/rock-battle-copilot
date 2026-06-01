from pydantic import BaseModel
from typing import Optional


class PetState(BaseModel):
    name: str
    hp: int
    hp_max: int
    mp: int
    mp_max: int
    skills: list[str]  # up to 4 slots, may be empty strings
    type: str = ""


class TurnRecord(BaseModel):
    turn: int
    player_action: str
    opponent_action: str
    weather_change: Optional[str] = None
    notes: Optional[str] = None


class BattleState(BaseModel):
    player_pets: list[PetState]
    opponent_pets: list[PetState]
    turn: int = 1
    player_active_idx: int = 0
    opponent_active_idx: int = 0
    turn_history: list[TurnRecord] = []
    field_effect: str = "晴天"


class ActionRecommendation(BaseModel):
    action: str
    action_type: str          # "skill" | "switch"
    confidence: float         # 0.0 – 1.0
    reasoning: str


class AnalyzeResponse(BaseModel):
    recommendations: list[ActionRecommendation]
    opponent_prediction: str
    battle_summary: str
