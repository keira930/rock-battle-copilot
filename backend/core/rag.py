"""
RAG retrieval layer.

数据目录说明：
  data/pets/        — 精灵基础信息
  data/skills/      — 技能信息
  data/teams/       — 阵容模板
  data/history/     — 历史对局
  data/rules/       — 规则说明
  data/counters/    — 克制关系（由 data_ingestion/parse_forum.py 生成）
  data/status/      — 状态效果（由 data_ingestion/parse_forum.py 生成）

生产环境：将 _keyword_match 替换为 ChromaDB/FAISS 向量检索，接口不变。
"""
import json
from pathlib import Path
from .models import NormalizedBattleState, RetrievedContext

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def _load_json(subdir: str) -> list[dict]:
    """加载某个子目录下所有 JSON 文件，返回扁平列表。"""
    results = []
    target = DATA_DIR / subdir
    if not target.exists():
        return results
    for f in sorted(target.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            # 兼容：顶层可能是 list 或单个 dict
            if isinstance(data, list):
                results.extend(data)
            elif isinstance(data, dict):
                results.append(data)
        except Exception:
            pass
    return results


def _keyword_match(docs: list[dict], keywords: list[str], top_k: int = 3) -> list[dict]:
    """
    关键词相关度排序。
    论坛爬取的文档结构为 {"text": "...", ...}，一并纳入检索。
    生产环境替换为 embedding 余弦相似度。
    """
    def score(doc: dict) -> int:
        # 优先检索 text 字段（论坛段落），其次全文序列化
        text = doc.get("text", "") + " " + json.dumps(doc, ensure_ascii=False)
        text = text.lower()
        return sum(1 for kw in keywords if kw.lower() in text)

    # 过滤掉分数为 0 的无关文档（对论坛数据尤其重要）
    scored = [(score(d), d) for d in docs]
    ranked = sorted(scored, key=lambda x: x[0], reverse=True)
    # 只返回有相关性的文档
    return [d for s, d in ranked if s > 0][:top_k]


def retrieve_context(state: NormalizedBattleState) -> RetrievedContext:
    """根据当前局面检索所有相关文档。"""
    # 构建检索关键词：精灵名、属性、技能名
    keywords = [
        state.player_active.name,
        state.opponent_active.name,
        state.player_active.type,
        state.opponent_active.type,
        *state.player_active.skills,
        *state.opponent_active.skills,
        # 把备战精灵的属性也纳入（有助于换精灵推荐）
        *[p.type for p in state.player_bench if p.type],
    ]
    keywords = list(dict.fromkeys(k for k in keywords if k))  # 去重保序

    # 加载各类数据
    all_pets      = _load_json("pets")
    all_skills    = _load_json("skills")
    all_teams     = _load_json("teams")
    all_history   = _load_json("history")
    all_rules     = _load_json("rules")
    all_counters  = _load_json("counters")   # 论坛克制数据
    all_status    = _load_json("status")     # 论坛状态数据

    return RetrievedContext(
        pet_info        = _keyword_match(all_pets,     keywords, top_k=5),
        skill_info      = _keyword_match(all_skills,   keywords, top_k=5),
        team_templates  = _keyword_match(all_teams,    keywords, top_k=3),
        battle_history  = _keyword_match(all_history,  keywords, top_k=3),
        rules           = all_rules[:5],           # 规则始终包含
        counter_info    = _keyword_match(all_counters, keywords, top_k=5),
        status_info     = _keyword_match(all_status,   keywords, top_k=3),
    )
