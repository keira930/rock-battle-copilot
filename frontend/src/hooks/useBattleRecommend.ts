import { useState } from "react";
import type { BattleState, RecommendResponse } from "../types/battle";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export function useBattleRecommend() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RecommendResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function recommend(battle: BattleState) {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(battle),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail ?? `HTTP ${res.status}`);
      }
      setResult(await res.json());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return { recommend, loading, result, error };
}
