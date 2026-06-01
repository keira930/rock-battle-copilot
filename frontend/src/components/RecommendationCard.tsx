import type { ActionRecommendation } from "../types/battle";

const ACTION_ICONS: Record<string, string> = {
  skill: "⚔️",
  switch: "🔄",
  item: "🎒",
};

const CONFIDENCE_LABEL = (c: number) =>
  c >= 0.8 ? "强烈推荐" : c >= 0.6 ? "推荐" : "备选";

interface Props {
  rec: ActionRecommendation;
  rank: number;
}

export function RecommendationCard({ rec, rank }: Props) {
  const icon = ACTION_ICONS[rec.action_type] ?? "❓";
  const confidencePct = Math.round(rec.confidence * 100);

  return (
    <div className={`rec-card rec-card--${rank === 1 ? "primary" : "secondary"}`}>
      <div className="rec-card__header">
        <span className="rec-card__rank">#{rank}</span>
        <span className="rec-card__icon">{icon}</span>
        <span className="rec-card__action">{rec.action}</span>
        <span className="rec-card__badge">{CONFIDENCE_LABEL(rec.confidence)}</span>
      </div>
      <div className="rec-card__confidence-bar">
        <div className="rec-card__confidence-fill" style={{ width: `${confidencePct}%` }} />
        <span className="rec-card__confidence-label">{confidencePct}%</span>
      </div>
      <p className="rec-card__reasoning">{rec.reasoning}</p>
    </div>
  );
}
