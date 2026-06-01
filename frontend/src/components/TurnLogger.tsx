import { useState } from "react";
import type { TurnRecord } from "../types/battle";

const WEATHER_OPTIONS = ["晴天", "下雨", "沙尘暴", "冰雹", "强风"];

interface Props {
  turn: number;
  currentWeather: string;
  history: TurnRecord[];
  playerSkills: string[];
  opponentSkills: string[];
  playerPets: string[];
  opponentPets: string[];
  onCommit: (record: TurnRecord) => void;
}

export function TurnLogger({
  turn, currentWeather, history,
  playerSkills, opponentSkills, playerPets, opponentPets,
  onCommit,
}: Props) {
  const [playerAction, setPlayerAction] = useState("");
  const [opponentAction, setOpponentAction] = useState("");
  const [weatherChange, setWeatherChange] = useState("");
  const [notes, setNotes] = useState("");

  const playerOptions = [
    ...playerSkills.filter(Boolean).map((s) => `使用 ${s}`),
    ...playerPets.map((p) => `换上 ${p}`),
  ];
  const opponentOptions = [
    ...opponentSkills.filter(Boolean).map((s) => `使用 ${s}`),
    ...opponentPets.map((p) => `换上 ${p}`),
  ];

  const commit = () => {
    if (!playerAction && !opponentAction) return;
    onCommit({
      turn,
      player_action: playerAction,
      opponent_action: opponentAction,
      weather_change: weatherChange || undefined,
      notes: notes || undefined,
    });
    setPlayerAction("");
    setOpponentAction("");
    setWeatherChange("");
    setNotes("");
  };

  return (
    <div className="turn-logger">
      <div className="turn-logger__titlebar">
        <h3 className="turn-logger__title">第 {turn} 回合记录</h3>
        <div className="weather-badge">
          <span className="weather-icon">☀️</span>
          <span>{currentWeather}</span>
        </div>
      </div>

      <div className="turn-logger__inputs">
        <div className="turn-action-col turn-action-col--player">
          <label>我方操作</label>
          <select value={playerAction} onChange={(e) => setPlayerAction(e.target.value)}>
            <option value="">选择操作…</option>
            {playerOptions.map((o) => <option key={o} value={o}>{o}</option>)}
            <option value="__custom__">手动输入</option>
          </select>
          {playerAction === "__custom__" && (
            <input placeholder="描述操作" autoFocus onChange={(e) => setPlayerAction(e.target.value)} />
          )}
        </div>

        <div className="turn-action-col turn-action-col--opponent">
          <label>对手操作（观察到的）</label>
          <select value={opponentAction} onChange={(e) => setOpponentAction(e.target.value)}>
            <option value="">选择操作…</option>
            {opponentOptions.map((o) => <option key={o} value={o}>{o}</option>)}
            <option value="__custom__">手动输入</option>
          </select>
          {opponentAction === "__custom__" && (
            <input placeholder="描述操作" autoFocus onChange={(e) => setOpponentAction(e.target.value)} />
          )}
        </div>
      </div>

      <div className="turn-logger__meta">
        <select
          className="weather-select"
          value={weatherChange}
          onChange={(e) => setWeatherChange(e.target.value)}
        >
          <option value="">天气未变化</option>
          {WEATHER_OPTIONS.filter((w) => w !== currentWeather).map((w) => (
            <option key={w} value={w}>天气变为：{w}</option>
          ))}
        </select>
        <input
          className="notes-input"
          value={notes}
          placeholder="备注（状态变化、特效触发…）"
          onChange={(e) => setNotes(e.target.value)}
        />
        <button className="btn-commit" onClick={commit}>确认记录</button>
      </div>

      {history.length > 0 && (
        <div className="turn-history">
          <div className="turn-history__header">历史记录</div>
          {[...history].reverse().map((r) => (
            <div key={r.turn} className="turn-row">
              <span className="turn-row__num">T{r.turn}</span>
              <span className="turn-row__player">{r.player_action || "—"}</span>
              <span className="turn-row__vs">vs</span>
              <span className="turn-row__opponent">{r.opponent_action || "—"}</span>
              {r.weather_change && (
                <span className="turn-row__weather">☀️→ {r.weather_change}</span>
              )}
              {r.notes && <span className="turn-row__notes">{r.notes}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
