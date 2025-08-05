# match_finder.py
import json
import pandas as pd
from collections import defaultdict

# --- FINAL, INTELLIGENT FORMATION FIT MATRIX ---
FORMATION_FIT_MATRIX = {
    # Attacking Roles
    "Striker":              {"4-2-3-1": 100, "4-4-2": 100, "3-5-2": 90, "4-3-3": 80, "3-4-3": 80},
    "Winger":               {"4-3-3": 100, "3-4-3": 100, "4-2-3-1": 85, "4-4-2": 60, "3-5-2": 20},
    "Attacking Midfielder":   {"4-2-3-1": 100, "4-3-1-2": 100, "4-3-3": 75, "4-4-2": 30, "3-5-2": 50},

    # Midfield Roles
    "Central Midfielder":     {"4-3-3": 100, "4-4-2": 100, "3-5-2": 90, "4-2-3-1": 80},
    "Defensive Midfielder":   {"4-3-3": 100, "4-1-4-1": 100, "4-2-3-1": 90, "3-5-2": 70, "4-4-2": 50},

    # Defensive Roles
    "Centre Back":            {"3-5-2": 100, "5-3-2": 100, "3-4-3": 100, "4-2-3-1": 90, "4-4-2": 90, "4-3-3": 90},
    "Full Back":              {"4-4-2": 100, "4-3-3": 100, "4-2-3-1": 100, "3-5-2": 20, "3-4-3": 20},
    "Wing-Back":              {"3-5-2": 100, "3-4-3": 100, "5-3-2": 100, "4-4-2": 30, "4-3-3": 20}
}

class MatchFinder:
    def __init__(self, club_profiles_path: str):
        try:
            with open(club_profiles_path, 'r', encoding='utf-8') as f:
                self.club_profiles = json.load(f)
            self._calculate_league_averages()
            print("✅ MatchFinder initialized and league averages calculated.")
        except FileNotFoundError:
            self.club_profiles = []
            print(f"❌ ERROR: Club profiles file not found at {club_profiles_path}")

    def _calculate_league_averages(self):
        self.league_averages = {"depth": {}, "age": {}, "net_spend": 0}
        all_positions = defaultdict(lambda: {'depths': [], 'ages': []})
        all_spends = []
        for club in self.club_profiles:
            net_spend_str = club['poc_metrics']['financial_analysis']['two_year_net_spend'].replace('€', '').replace('m', '')
            try:
                all_spends.append(float(net_spend_str) * 1_000_000)
            except (ValueError, TypeError):
                continue
            for pos, data in club['poc_metrics']['current_squad_analysis'].items():
                all_positions[pos]['depths'].append(data['depth'])
                all_positions[pos]['ages'].append(data['avg_age'])
        self.league_averages['net_spend'] = sum(all_spends) / len(all_spends) if all_spends else 0
        for pos, data in all_positions.items():
            self.league_averages['depth'][pos] = sum(data['depths']) / len(data['depths'])
            self.league_averages['age'][pos] = sum(data['ages']) / len(data['ages'])

    def _get_tactical_fit_score(self, player_position: str, club_formation: str) -> int:
        """
        A more robust scoring system for tactical fit based on position and formation.
        """
        if not club_formation or not isinstance(club_formation, str):
            return 50

        # --- THE FIX IS HERE ---
        # First, handle the special case for defenders
        if "Back" in player_position:
            if club_formation.startswith("4-"):
                return FORMATION_FIT_MATRIX["Back"]["4-"]
            elif club_formation.startswith("3-"):
                return FORMATION_FIT_MATRIX["Back"]["3-"]
            elif club_formation.startswith("5-"):
                return FORMATION_FIT_MATRIX["Back"]["5-"]
        
        # Then, handle all other positions as before
        for pos_key, scores in FORMATION_FIT_MATRIX.items():
            if pos_key in player_position:
                return scores.get(club_formation, 50)
        
        return 70 # Default good score if no specific rule applies

    def find_best_matches(self, player_profile: dict) -> list:
        if not player_profile or 'position_name' not in player_profile: return []
        player_pos = player_profile['position_name']
        
        all_matches = []
        print("\n--- [DEBUG] Tactical Fit Score Calculation ---") # Log header
        
        for club in self.club_profiles:
            poc_metrics = club.get('poc_metrics', {})
            attractiveness_index = poc_metrics.get('deal_attractiveness_index', {})
            
            if player_pos in attractiveness_index:
                deal_score = attractiveness_index[player_pos]
                club_formation = poc_metrics.get('tactical_analysis', {}).get('primary_formation')
                
                # --- This is the value we want to inspect ---
                tactical_score = self._get_tactical_fit_score(player_pos, club_formation)
                
                # --- THE NEW LOG IS HERE ---
                print(f"  - Club: {club['club_name']:<25} | Player Pos: {player_pos:<20} | Club Formation: {club_formation:<8} | Tactical Score: {tactical_score}")

                final_score = (deal_score * 0.70) + (tactical_score * 0.30)
                
                reasons = []
                squad_pos_data = poc_metrics.get('current_squad_analysis', {}).get(player_pos, {})
                financial_data = poc_metrics.get('financial_analysis', {})
                avg_depth = self.league_averages['depth'].get(player_pos, 5)
                avg_age = self.league_averages['age'].get(player_pos, 26)
                
                if squad_pos_data.get('depth', 5) <= avg_depth * 0.75:
                    reasons.append("Low Depth")
                if squad_pos_data.get('avg_age', 25) >= avg_age * 1.1:
                    reasons.append("Aging Squad")

                net_spend_str = financial_data.get('two_year_net_spend', '€0m').replace('€', '').replace('m', '')
                try:
                    net_spend = float(net_spend_str) * 1_000_000
                    if net_spend > 0 and net_spend >= self.league_averages['net_spend']:
                        reasons.append("Has Funds")
                except (ValueError, TypeError):
                    pass
                
                if tactical_score >= 80:
                    reasons.append("Ideal Formation")
                elif tactical_score >= 60:
                    reasons.append("Good Formation")

                reason_str = " | ".join(reasons) if reasons else "Balanced Need"
                
                all_matches.append({
                    "club_name": club['club_name'],
                    "match_score": round(final_score, 1),
                    "reason": reason_str
                })

        return sorted(all_matches, key=lambda x: x['match_score'], reverse=True)[:3]