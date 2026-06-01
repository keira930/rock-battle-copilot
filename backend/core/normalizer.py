"""
normalizeBattleState — canonicalize raw user input into a structured state.
"""
from .models import BattleState, NormalizedBattleState, PetState


def normalize_battle_state(raw: BattleState) -> NormalizedBattleState:
    def find_pet(pets: list[PetState], name: str) -> PetState:
        for p in pets:
            if p.name == name:
                return p
        # fallback: return first pet
        return pets[0]

    player_active = find_pet(raw.player_pets, raw.player_active)
    opponent_active = find_pet(raw.opponent_pets, raw.opponent_active)

    player_bench = [p for p in raw.player_pets if p.name != raw.player_active]
    opponent_bench = [p for p in raw.opponent_pets if p.name != raw.opponent_active]

    player_hp_ratio = player_active.hp / max(player_active.hp_max, 1)
    opponent_hp_ratio = opponent_active.hp / max(opponent_active.hp_max, 1)

    return NormalizedBattleState(
        player_active=player_active,
        opponent_active=opponent_active,
        player_bench=player_bench,
        opponent_bench=opponent_bench,
        player_hp_ratio=player_hp_ratio,
        opponent_hp_ratio=opponent_hp_ratio,
        turn=raw.turn,
        weather=raw.weather,
        context_notes=raw.notes,
    )
