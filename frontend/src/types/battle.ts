export interface PetState {
  name: string;
  hp: number;
  hp_max: number;
  mp: number;
  mp_max: number;
  skills: [string, string, string, string];
  type: string;
}

export interface TurnRecord {
  turn: number;
  player_action: string;
  opponent_action: string;
  weather_change?: string; // new weather if a skill changed it this turn
  notes?: string;
}

export interface BattleState {
  player_pets: PetState[];
  opponent_pets: PetState[];
  turn: number;
  player_active_idx: number;
  opponent_active_idx: number;
  turn_history: TurnRecord[];
  field_effect: string; // defaults to "晴天"
}

export interface ActionRecommendation {
  action: string;
  action_type: "skill" | "switch" | "item";
  confidence: number;
  reasoning: string;
}

export interface RecommendResponse {
  recommendations: ActionRecommendation[];
  opponent_prediction: string;
  battle_summary: string;
}
