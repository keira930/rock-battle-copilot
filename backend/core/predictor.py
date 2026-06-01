"""
predictOpponentAction — heuristic + LLM-assisted prediction of opponent's next move.
"""
from .models import NormalizedBattleState, RetrievedContext


def predict_opponent_action(
    state: NormalizedBattleState,
    context: RetrievedContext,
) -> str:
    """
    Returns a natural-language prediction of what the opponent will likely do.

    Current implementation uses heuristics; swap in an LLM call for richer predictions.
    """
    opp = state.opponent_active
    player = state.player_active
    opp_hp_ratio = state.opponent_hp_ratio

    # Heuristic tree
    if opp_hp_ratio < 0.25:
        return (
            f"对手的【{opp.name}】血量危急（剩余 {opp_hp_ratio:.0%}），"
            "很可能会换上备战精灵或使用强力技能进行最后一搏。"
        )

    if opp_hp_ratio < 0.5:
        return (
            f"对手的【{opp.name}】血量偏低（剩余 {opp_hp_ratio:.0%}），"
            "可能考虑换精灵或优先使用高伤技能。"
        )

    # Check type advantage from retrieved pet info
    for pet_doc in context.pet_info:
        if pet_doc.get("name") == opp.name:
            weaknesses = pet_doc.get("weak_to", [])
            if player.type and player.type in weaknesses:
                return (
                    f"对手的【{opp.name}】对【{player.type}】属性有弱点，"
                    "对手可能会换上克制你的精灵，或尝试先手控制技能。"
                )

    if opp.skills:
        top_skill = opp.skills[0]
        return f"对手的【{opp.name}】预计会使用【{top_skill}】，保持压制。"

    return f"对手的【{opp.name}】局面稳定，预计继续正常进攻。"
