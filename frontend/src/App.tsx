import { useState } from "react";
import type { BattleState, PetState, TurnRecord } from "./types/battle";
import { PetForm } from "./components/PetForm";
import { TurnLogger } from "./components/TurnLogger";
import { RecommendationCard } from "./components/RecommendationCard";
import "./App.css";

const emptyPet = (): PetState => ({
  name: "",
  hp: 100,
  hp_max: 100,
  mp: 10,
  mp_max: 10,
  skills: ["", "", "", ""],
  type: "",
});

const makePet = (name: string, type: string, skills: PetState["skills"]): PetState => ({
  name, type, hp: 100, hp_max: 100, mp: 10, mp_max: 10, skills,
});

const INITIAL_STATE: BattleState = {
  player_pets: [
    makePet("冰雪女王", "冰", ["冰霜箭", "冰封之地", "", ""]),
    makePet("火炎龙", "火", ["火球术", "龙炎冲击", "", ""]),
  ],
  opponent_pets: [
    makePet("水之精灵", "水", ["水弹", "波涛汹涌", "", ""]),
  ],
  turn: 1,
  player_active_idx: 0,
  opponent_active_idx: 0,
  turn_history: [],
  field_effect: "晴天",
};

export default function App() {
  const [battle, setBattle] = useState<BattleState>(INITIAL_STATE);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<null | {
    opponent_prediction: string;
    battle_summary: string;
    recommendations: any[];
  }>(null);
  const [error, setError] = useState<string | null>(null);

  const update = (partial: Partial<BattleState>) =>
    setBattle((b) => ({ ...b, ...partial }));

  const updatePlayerPet = (i: number, pet: PetState) => {
    const pets = [...battle.player_pets];
    pets[i] = pet;
    update({ player_pets: pets });
  };

  const updateOpponentPet = (i: number, pet: PetState) => {
    const pets = [...battle.opponent_pets];
    pets[i] = pet;
    update({ opponent_pets: pets });
  };

  const addPet = (side: "player" | "opponent") => {
    if (side === "player" && battle.player_pets.length < 6)
      update({ player_pets: [...battle.player_pets, emptyPet()] });
    if (side === "opponent" && battle.opponent_pets.length < 6)
      update({ opponent_pets: [...battle.opponent_pets, emptyPet()] });
  };

  const removePet = (side: "player" | "opponent", i: number) => {
    if (side === "player") {
      const pets = battle.player_pets.filter((_, idx) => idx !== i);
      update({ player_pets: pets, player_active_idx: Math.min(battle.player_active_idx, pets.length - 1) });
    } else {
      const pets = battle.opponent_pets.filter((_, idx) => idx !== i);
      update({ opponent_pets: pets, opponent_active_idx: Math.min(battle.opponent_active_idx, pets.length - 1) });
    }
  };

  const commitTurn = (record: TurnRecord) => {
    update({
      turn_history: [...battle.turn_history, record],
      turn: battle.turn + 1,
      field_effect: record.weather_change ?? battle.field_effect,
    });
  };

  const analyze = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("http://localhost:8000/battle/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(battle),
      });
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      setResult(await res.json());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const activePet = battle.player_pets[battle.player_active_idx];
  const activeOpponent = battle.opponent_pets[battle.opponent_active_idx];

  return (
    <div className="app">
      <header className="app-header">
        <h1>洛克王国 · 对战助手</h1>
        <p>记录对战局面，AI 预判对手操作并给出应对建议</p>
      </header>

      <main className="app-main">
        {/* ── Teams ── */}
        <section className="battle-input">
          {/* Player side */}
          <div className="input-panel input-panel--player">
            <div className="panel-header">
              <h2>我方</h2>
              <select
                className="active-select"
                value={battle.player_active_idx}
                onChange={(e) => update({ player_active_idx: Number(e.target.value) })}
              >
                {battle.player_pets.map((p, i) => (
                  <option key={i} value={i}>{p.name || `精灵 ${i + 1}`}</option>
                ))}
              </select>
            </div>
            <div className="pets-list">
              {battle.player_pets.map((pet, i) => (
                <PetForm
                  key={i}
                  pet={pet}
                  isActive={i === battle.player_active_idx}
                  side="player"
                  onChange={(p) => updatePlayerPet(i, p)}
                  onRemove={battle.player_pets.length > 1 ? () => removePet("player", i) : undefined}
                />
              ))}
            </div>
            {battle.player_pets.length < 6 && (
              <button className="btn-add-pet" onClick={() => addPet("player")}>+ 添加精灵</button>
            )}
          </div>

          <div className="vs-divider">VS</div>

          {/* Opponent side */}
          <div className="input-panel input-panel--opponent">
            <div className="panel-header">
              <h2>对手</h2>
              <select
                className="active-select"
                value={battle.opponent_active_idx}
                onChange={(e) => update({ opponent_active_idx: Number(e.target.value) })}
              >
                {battle.opponent_pets.map((p, i) => (
                  <option key={i} value={i}>{p.name || `精灵 ${i + 1}`}</option>
                ))}
              </select>
            </div>
            <div className="pets-list">
              {battle.opponent_pets.map((pet, i) => (
                <PetForm
                  key={i}
                  pet={pet}
                  isActive={i === battle.opponent_active_idx}
                  side="opponent"
                  onChange={(p) => updateOpponentPet(i, p)}
                  onRemove={battle.opponent_pets.length > 1 ? () => removePet("opponent", i) : undefined}
                />
              ))}
            </div>
            {battle.opponent_pets.length < 6 && (
              <button className="btn-add-pet btn-add-pet--opponent" onClick={() => addPet("opponent")}>+ 添加精灵</button>
            )}
          </div>
        </section>

        {/* ── Turn Logger ── */}
        <TurnLogger
          turn={battle.turn}
          currentWeather={battle.field_effect}
          history={battle.turn_history}
          playerSkills={activePet?.skills ?? []}
          opponentSkills={activeOpponent?.skills ?? []}
          playerPets={battle.player_pets.map((p) => p.name).filter(Boolean)}
          opponentPets={battle.opponent_pets.map((p) => p.name).filter(Boolean)}
          onCommit={commitTurn}
        />

        {/* ── Analyze Button ── */}
        <button className="btn-recommend" onClick={analyze} disabled={loading}>
          {loading ? "分析中…" : "获取 AI 建议"}
        </button>

        {error && <div className="error-box">{error}</div>}

        {/* ── Results ── */}
        {result && (
          <section className="results">
            <div className="result-row">
              <div className="prediction-box">
                <h3>对手下一步预测</h3>
                <p>{result.opponent_prediction}</p>
              </div>
              <div className="summary-box">
                <h3>局面总结</h3>
                <p>{result.battle_summary}</p>
              </div>
            </div>
            <h3 className="rec-title">推荐操作</h3>
            <div className="rec-list">
              {result.recommendations.map((rec, i) => (
                <RecommendationCard key={i} rec={rec} rank={i + 1} />
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
