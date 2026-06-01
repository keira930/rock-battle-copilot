# 洛克王国 · 对战助手 (RoCo Battle Copilot)

AI 辅助的洛克王国对战推荐系统。输入当前局面，获取 2–3 个推荐操作和对手行为预测。

## 架构

```
用户输入
  ↓ normalizeBattleState()
  ↓ RAG 检索（精灵/技能/阵容/历史/规则）
  ↓ predictOpponentAction()
  ↓ recommendPlayerActions()
  ↓ LLM 生成自然语言解释
  ↓ 前端展示推荐操作
```

## 快速启动

在项目根目录（`roco-battle-copilot/`）下分别开两个终端：

### 终端 1 — 后端

```bash
pip install -r backend/requirements.txt
python3 -m uvicorn backend.api.main:app --port 8000 --reload
```

API 运行在 http://localhost:8000  
交互文档：http://localhost:8000/docs

### 终端 2 — 前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在 http://localhost:5173

## 目录结构

```
roco-battle-copilot/
├── backend/
│   ├── core/
│   │   ├── models.py        # Pydantic 数据模型
│   │   ├── normalizer.py    # normalizeBattleState
│   │   ├── rag.py           # RAG 检索层
│   │   ├── predictor.py     # predictOpponentAction
│   │   ├── recommender.py   # recommendPlayerActions
│   │   └── llm.py           # LLM 自然语言生成
│   ├── api/
│   │   └── main.py          # FastAPI 入口
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── types/           # TypeScript 类型
│   │   ├── hooks/           # useBattleRecommend
│   │   ├── components/      # PetForm, RecommendationCard
│   │   └── App.tsx          # 主界面
│   └── package.json
├── data/
│   ├── pets/                # 精灵数据 JSON
│   ├── skills/              # 技能数据 JSON
│   ├── teams/               # 阵容模板
│   ├── history/             # 历史对局（待填充）
│   └── rules/               # 规则说明
└── .env.example
```

## 扩展指南

- **替换 RAG**：将 `backend/core/rag.py` 中的关键词匹配换成 ChromaDB/FAISS 向量检索
- **增强预测**：在 `predictor.py` 中调用 LLM 进行更智能的对手行为预测
- **添加数据**：在 `data/` 目录下添加更多精灵/技能 JSON 文件，RAG 会自动加载
- **历史对局**：在 `data/history/` 中记录比赛数据，提升推荐质量
