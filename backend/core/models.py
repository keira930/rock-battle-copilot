"""
Data models for the RoCo Battle Copilot.
"""
from pydantic import BaseModel, Field
from typing import Optional


class PetState(BaseModel):
    name: str
    level: int = 1
    hp: int
    hp_max: int
    skills: list[str] = Field(default_factory=list)
    type: str = ""
    is_active: bool = False


class BattleState(BaseModel):
    """Raw input from the user describing the current battle situation."""
    player_pets: list[PetState]
    opponent_pets: list[PetState]
    turn: int = 1
    player_active: str  # name of currently active pet
    opponent_active: str
    weather: Optional[str] = None
    notes: Optional[str] = None  # free-form notes


class NormalizedBattleState(BaseModel):
    """Canonicalized battle state after normalization."""
    player_active: PetState
    opponent_active: PetState
    player_bench: list[PetState]
    opponent_bench: list[PetState]
    player_hp_ratio: float
    opponent_hp_ratio: float
    turn: int
    weather: Optional[str]
    context_notes: Optional[str]


class RetrievedContext(BaseModel):
    """Documents retrieved from the RAG layer."""
    pet_info: list[dict]
    skill_info: list[dict]
    team_templates: list[dict]
    battle_history: list[dict]
    rules: list[dict]
    counter_info: list[dict] = Field(default_factory=list)  # 克制关系（来自论坛）
    status_info: list[dict] = Field(default_factory=list)   # 状态效果（来自论坛）


class ActionRecommendation(BaseModel):
    action: str               # e.g. "使用技能：冰霜箭", "换上精灵：火龙"
    action_type: str          # "skill" | "switch" | "item"
    confidence: float         # 0.0 – 1.0
    reasoning: str            # natural-language explanation


class RecommendResponse(BaseModel):
    recommendations: list[ActionRecommendation]
    opponent_prediction: str
    battle_summary: str
