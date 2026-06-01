import type { PetState } from "../types/battle";

interface Props {
  pet: PetState;
  isActive: boolean;
  side: "player" | "opponent";
  onChange: (pet: PetState) => void;
  onRemove?: () => void;
}

export function PetForm({ pet, isActive, side, onChange, onRemove }: Props) {
  const update = (partial: Partial<PetState>) => onChange({ ...pet, ...partial });

  const hpPct = Math.max(0, Math.min(100, (pet.hp / (pet.hp_max || 1)) * 100));
  const mpPct = Math.max(0, Math.min(100, (pet.mp / (pet.mp_max || 1)) * 100));
  const hpColor = hpPct > 50 ? "#4caf50" : hpPct > 25 ? "#ff9800" : "#f44336";

  const setSkill = (i: number, val: string) => {
    const next = [...pet.skills] as PetState["skills"];
    next[i] = val;
    update({ skills: next });
  };

  return (
    <div className={`pet-form ${isActive ? "pet-form--active" : ""}`}>
      <div className="pet-form__header">
        <div className="field-inline">
          <input
            className="pet-name-input"
            value={pet.name}
            placeholder="精灵名称"
            onChange={(e) => update({ name: e.target.value })}
          />
          <input
            className="pet-type-input"
            value={pet.type}
            placeholder="属性"
            onChange={(e) => update({ type: e.target.value })}
          />
        </div>
        <div className="pet-form__actions">
          {isActive && <span className="badge-active">出战中</span>}
          {onRemove && (
            <button className="btn-remove" onClick={onRemove} title="移除精灵">×</button>
          )}
        </div>
      </div>

      {/* HP */}
      <div className="stat-row">
        <span className="stat-label">HP</span>
        <input type="number" className="stat-input" value={pet.hp} min={0} max={pet.hp_max}
          onChange={(e) => update({ hp: Number(e.target.value) })} />
        <span className="stat-sep">/</span>
        <input type="number" className="stat-input" value={pet.hp_max} min={1}
          onChange={(e) => update({ hp_max: Number(e.target.value) })} />
      </div>
      <div className="stat-bar">
        <div className="stat-fill" style={{ width: `${hpPct}%`, background: hpColor }} />
      </div>

      {/* MP */}
      <div className="stat-row">
        <span className="stat-label">MP</span>
        <input type="number" className="stat-input" value={pet.mp} min={0} max={pet.mp_max}
          onChange={(e) => update({ mp: Number(e.target.value) })} />
        <span className="stat-sep">/</span>
        <input type="number" className="stat-input" value={pet.mp_max} min={1}
          onChange={(e) => update({ mp_max: Number(e.target.value) })} />
      </div>
      <div className="stat-bar">
        <div className="stat-fill stat-fill--mp" style={{ width: `${mpPct}%` }} />
      </div>

      {/* Skills: 4 slots */}
      <div className="skills-grid">
        {pet.skills.map((sk, i) => (
          <input
            key={i}
            className={`skill-input skill-input--${side}`}
            value={sk}
            placeholder={`技能 ${i + 1}`}
            onChange={(e) => setSkill(i, e.target.value)}
          />
        ))}
      </div>
    </div>
  );
}
