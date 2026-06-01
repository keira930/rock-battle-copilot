"""
LLM explanation generator.

Calls the Anthropic API to produce a natural-language battle summary.
Falls back to a template-based summary if API key is not set.
"""
import os
from .models import (
    NormalizedBattleState,
    RetrievedContext,
    ActionRecommendation,
)

try:
    import anthropic  # type: ignore
    _HAS_ANTHROPIC = True
except ImportError:
    _HAS_ANTHROPIC = False


def _template_summary(
    state: NormalizedBattleState,
    opponent_prediction: str,
    recommendations: list[ActionRecommendation],
) -> str:
    top = recommendations[0] if recommendations else None
    lines = [
        f"当前局面：你的【{state.player_active.name}】（血量 {state.player_hp_ratio:.0%}）"
        f" vs 对手的【{state.opponent_active.name}】（血量 {state.opponent_hp_ratio:.0%}）。",
        f"对手预测：{opponent_prediction}",
    ]
    if top:
        lines.append(f"最优推荐：{top.action} —— {top.reasoning}")
    return "\n".join(lines)


def generate_battle_summary(
    state: NormalizedBattleState,
    context: RetrievedContext,
    opponent_prediction: str,
    recommendations: list[ActionRecommendation],
) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not _HAS_ANTHROPIC or not api_key:
        return _template_summary(state, opponent_prediction, recommendations)

    client = anthropic.Anthropic(api_key=api_key)

    rec_text = "\n".join(
        f"{i+1}. {r.action}（置信度 {r.confidence:.0%}）：{r.reasoning}"
        for i, r in enumerate(recommendations)
    )

    # 附上论坛克制/状态数据（最多 3 条，各取 text 字段）
    counter_snippets = "\n".join(
        f"- {d.get('text', '')[:120]}"
        for d in context.counter_info[:3]
        if d.get("text")
    )
    status_snippets = "\n".join(
        f"- {d.get('text', '')[:120]}"
        for d in context.status_info[:2]
        if d.get("text")
    )

    prompt = f"""你是洛克王国对战助手，请用简洁中文（120字以内）总结当前局面并给出核心建议。

当前局面：
- 我方出战：{state.player_active.name}，血量 {state.player_hp_ratio:.0%}，技能：{', '.join(state.player_active.skills)}
- 对方出战：{state.opponent_active.name}，血量 {state.opponent_hp_ratio:.0%}
- 回合数：{state.turn}

参考资料（来自游戏论坛）：
克制信息：
{counter_snippets or "（暂无）"}
状态信息：
{status_snippets or "（暂无）"}

对手预测：{opponent_prediction}

推荐操作：
{rec_text}

请结合参考资料输出一段简短的对战建议。"""

    message = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text
