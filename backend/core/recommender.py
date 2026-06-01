"""
recommendPlayerActions — generate 2–3 ranked action recommendations.
"""
from .models import (
    NormalizedBattleState,
    RetrievedContext,
    ActionRecommendation,
)


def recommend_player_actions(
    state: NormalizedBattleState,
    context: RetrievedContext,
    opponent_prediction: str,
) -> list[ActionRecommendation]:
    """
    Returns 2–3 ranked ActionRecommendation objects.

    Logic: heuristic scoring. Replace or augment with LLM for richer reasoning.
    """
    recommendations: list[ActionRecommendation] = []
    player = state.player_active
    opponent = state.opponent_active
    player_hp = state.player_hp_ratio
    opp_hp = state.opponent_hp_ratio

    # --- 从论坛克制数据提取额外上下文 ---
    counter_context = ""
    for doc in context.counter_info:
        text = doc.get("text", "")
        if text and (opponent.name in text or opponent.type in text or player.type in text):
            counter_context += text + " "

    status_context = ""
    for doc in context.status_info:
        text = doc.get("text", "")
        if text:
            status_context += text + " "

    # --- Option 1: Best offensive skill ---
    skill_info_map = {s.get("name"): s for s in context.skill_info}

    best_skill = None
    best_skill_power = 0
    for skill_name in player.skills:
        info = skill_info_map.get(skill_name, {})
        power = info.get("power", 50)
        # Check type advantage
        type_bonus = 1.0
        for pet_doc in context.pet_info:
            if pet_doc.get("name") == opponent.name:
                weaknesses = pet_doc.get("weak_to", [])
                skill_type = info.get("type", "")
                if skill_type in weaknesses:
                    type_bonus = 1.5
        effective_power = power * type_bonus
        if effective_power > best_skill_power:
            best_skill_power = effective_power
            best_skill = skill_name

    if best_skill:
        confidence = min(0.95, 0.6 + (best_skill_power - 50) / 200)
        type_note = "（克制属性！）" if best_skill_power > 75 else ""
        # 如果论坛克制数据中有相关描述，追加到推理
        forum_note = ""
        if counter_context and (player.type in counter_context or best_skill in counter_context):
            forum_note = "（论坛数据支持此判断）"
        recommendations.append(ActionRecommendation(
            action=f"使用技能：{best_skill}{type_note}",
            action_type="skill",
            confidence=round(confidence, 2),
            reasoning=(
                f"【{best_skill}】预计威力最高{type_note}{forum_note}，"
                f"对方【{opponent.name}】当前血量 {opp_hp:.0%}，"
                "可能一击或两击击倒。"
            ),
        ))

    # --- Option 2: Switch if low HP ---
    if player_hp < 0.4 and state.player_bench:
        best_bench = state.player_bench[0]
        # Prefer bench pet that counters opponent type
        for bench_pet in state.player_bench:
            for pet_doc in context.pet_info:
                if pet_doc.get("name") == opponent.name:
                    weaknesses = pet_doc.get("weak_to", [])
                    if bench_pet.type in weaknesses:
                        best_bench = bench_pet
                        break

        recommendations.append(ActionRecommendation(
            action=f"换上精灵：{best_bench.name}",
            action_type="switch",
            confidence=0.75,
            reasoning=(
                f"当前【{player.name}】血量仅剩 {player_hp:.0%}，"
                f"换上【{best_bench.name}】可以保存战力并改变局势。"
            ),
        ))

    # --- Option 3: Second skill or defensive skill ---
    if len(player.skills) >= 2:
        second_skill = player.skills[1] if player.skills[0] == best_skill else player.skills[0]
        recommendations.append(ActionRecommendation(
            action=f"使用技能：{second_skill}（备选）",
            action_type="skill",
            confidence=0.5,
            reasoning=(
                f"若对手使用防御或有特殊抗性，"
                f"【{second_skill}】可作为备选手段打乱对手节奏。"
            ),
        ))

    # Sort by confidence descending, keep top 3
    recommendations.sort(key=lambda r: r.confidence, reverse=True)
    return recommendations[:3]
