"""
FastAPI entry point for RoCo Battle Copilot.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ..core import (
    BattleState,
    RecommendResponse,
    normalize_battle_state,
    retrieve_context,
    predict_opponent_action,
    recommend_player_actions,
    generate_battle_summary,
)

app = FastAPI(title="RoCo Battle Copilot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/recommend", response_model=RecommendResponse)
def recommend(battle: BattleState) -> RecommendResponse:
    """
    Main pipeline:
      1. normalizeBattleState
      2. RAG retrieval
      3. predictOpponentAction
      4. recommendPlayerActions
      5. LLM summary
    """
    try:
        state = normalize_battle_state(battle)
        context = retrieve_context(state)
        opponent_prediction = predict_opponent_action(state, context)
        recommendations = recommend_player_actions(state, context, opponent_prediction)
        battle_summary = generate_battle_summary(
            state, context, opponent_prediction, recommendations
        )
        return RecommendResponse(
            recommendations=recommendations,
            opponent_prediction=opponent_prediction,
            battle_summary=battle_summary,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
