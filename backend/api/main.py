from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ..core.models import BattleState, AnalyzeResponse
from ..core.mock_analyzer import analyze as mock_analyze

app = FastAPI(title="洛克王国对战助手 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/battle/analyze", response_model=AnalyzeResponse)
def analyze(state: BattleState) -> AnalyzeResponse:
    """
    Analyze the current battle state and return:
    - opponent_prediction: what the opponent is likely to do next
    - recommendations: ordered list of recommended player actions
    - battle_summary: plain-language description of the current situation

    Currently uses mock_analyzer. Replace mock_analyze with llm_analyze
    once the AI model is integrated.
    """
    try:
        return mock_analyze(state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
