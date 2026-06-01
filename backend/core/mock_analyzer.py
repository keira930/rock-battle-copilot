"""
Mock analyzer — returns deterministic plausible responses based on battle state.
Drop-in replacement for the real LLM analyzer; swap by changing battle/analyze route.
"""

from .models import BattleState, ActionRecommendation, AnalyzeResponse


def _hp_pct(pet) -> float:
    return pet.hp / pet.hp_max if pet.hp_max > 0 else 0.0


def _active_skills(pet) -> list[str]:
    return [s for s in pet.skills if s.strip()]


def analyze(state: BattleState) -> AnalyzeResponse:
    player = state.player_pets[state.player_active_idx]
    opponent = state.opponent_pets[state.opponent_active_idx]

    player_hp = _hp_pct(player)
    opp_hp = _hp_pct(opponent)
    player_skills = _active_skills(player)
    opp_skills = _active_skills(opponent)
    turn = state.turn
    history = state.turn_history

    # ── Opponent prediction ──────────────────────────────────────────────────
    # Simple heuristic: look at last turn's action, low HP → switch tendency
    last_opp_action = history[-1].opponent_action if history else ""
    repeated = (
        len(history) >= 2
        and history[-1].opponent_action == history[-2].opponent_action
        if len(history) >= 2 else False
    )

    if opp_hp < 0.3:
        opp_prediction = (
            f"对手 {opponent.name} 血量仅剩 {int(opp_hp*100)}%，"
            "大概率会在本回合换上备用精灵以保存战力。"
        )
    elif repeated and last_opp_action:
        opp_prediction = (
            f"对手连续两回合使用了「{last_opp_action.replace('使用 ', '')}」，"
            "可能在积蓄 MP 或等待时机，本回合有一定概率改变策略。"
        )
    elif opp_skills:
        top_skill = opp_skills[0]
        opp_prediction = (
            f"根据已知技能库，对手 {opponent.name} 最常依赖「{top_skill}」作为主攻手段，"
            f"本回合仍大概率使用此技能（置信度约 65%）。"
        )
    else:
        opp_prediction = (
            f"对手 {opponent.name} 的技能信息尚不完整，"
            "无法给出高置信度预测，建议保守应对。"
        )

    # ── Recommendations ──────────────────────────────────────────────────────
    recs: list[ActionRecommendation] = []

    # Rec 1: best skill to use
    if player_skills:
        best_skill = player_skills[0]
        recs.append(ActionRecommendation(
            action=f"使用 {best_skill}",
            action_type="skill",
            confidence=0.72 if player_hp > 0.5 else 0.55,
            reasoning=(
                f"当前我方 {player.name} 血量 {int(player_hp*100)}%，"
                f"「{best_skill}」是已知技能中最优先选择，可对对手造成有效伤害。"
            ),
        ))

    # Rec 2: switch if low HP
    bench = [
        p for i, p in enumerate(state.player_pets)
        if i != state.player_active_idx and p.name and _hp_pct(p) > 0.5
    ]
    if player_hp < 0.4 and bench:
        recs.append(ActionRecommendation(
            action=f"换上 {bench[0].name}",
            action_type="switch",
            confidence=0.68,
            reasoning=(
                f"我方 {player.name} 血量偏低（{int(player_hp*100)}%），"
                f"换上血量充足的 {bench[0].name} 可减少损耗并重新掌控节奏。"
            ),
        ))

    # Rec 3: second skill option
    if len(player_skills) >= 2:
        recs.append(ActionRecommendation(
            action=f"使用 {player_skills[1]}",
            action_type="skill",
            confidence=0.45,
            reasoning=(
                f"若对手本回合换精灵，「{player_skills[1]}」作为备选技能"
                "可能更适合新出场的目标。"
            ),
        ))

    if not recs:
        recs.append(ActionRecommendation(
            action="等待观察",
            action_type="skill",
            confidence=0.3,
            reasoning="当前信息不足，建议先保守行动，下回合根据对手操作再调整。",
        ))

    # ── Battle summary ───────────────────────────────────────────────────────
    advantage = "优势" if player_hp > opp_hp + 0.2 else ("劣势" if opp_hp > player_hp + 0.2 else "均势")
    summary = (
        f"第 {turn} 回合，场地效果：{state.field_effect}。"
        f"我方出战 {player.name}（HP {int(player_hp*100)}%，MP {player.mp}/{player.mp_max}），"
        f"对手出战 {opponent.name}（HP {int(opp_hp*100)}%）。"
        f"当前局面我方处于{advantage}。"
    )
    if history:
        summary += f" 共经过 {len(history)} 回合记录。"

    return AnalyzeResponse(
        recommendations=recs,
        opponent_prediction=opp_prediction,
        battle_summary=summary,
    )
