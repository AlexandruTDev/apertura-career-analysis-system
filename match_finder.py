# match_finder.py (Final Corrected Version)
import json
import pandas as pd
from collections import defaultdict
from player_analyzer import PlayerAnalyzer, KPI_FORMATED_NAMES, PLAYERS_STATS_FILE, PLAYERS_PHYSICAL_FILE

# --- FINAL, INTELLIGENT FORMATION FIT MATRIX ---
FORMATION_FIT_MATRIX = {
    "Striker":              {"4-2-3-1": 100, "4-4-2": 100, "3-5-2": 90, "4-3-3": 80, "3-4-3": 80},
    "Winger":               {"4-3-3": 100, "3-4-3": 100, "4-2-3-1": 85, "4-4-2": 60, "3-5-2": 20},
    "Wing Forward":         {"4-3-3": 100, "3-4-3": 100, "4-2-3-1": 85, "4-4-2": 60, "3-5-2": 20},
    "Attacking Midfielder":   {"4-2-3-1": 100, "4-3-1-2": 100, "4-3-3": 75, "4-4-2": 30, "3-5-2": 50},
    "Central Midfielder":     {"4-3-3": 100, "4-4-2": 100, "3-5-2": 90, "4-2-3-1": 80},
    "Defensive Midfielder":   {"4-3-3": 100, "4-1-4-1": 100, "4-2-3-1": 90, "3-5-2": 70, "4-4-2": 50},
    "Centre Back":            {"3-5-2": 100, "5-3-2": 100, "3-4-3": 100, "4-2-3-1": 90, "4-4-2": 90, "4-3-3": 90},
    "Full Back":              {"4-4-2": 100, "4-3-3": 100, "4-2-3-1": 100, "3-5-2": 20, "3-4-3": 20},
    "Wing-Back":              {"3-5-2": 100, "3-4-3": 100, "5-3-2": 100, "4-4-2": 30, "4-3-3": 20}
}

class MatchFinder:
    def __init__(self, club_profiles_path: str,player_analyzer: PlayerAnalyzer):
        """
        Initializes the MatchFinder with a path to club profiles and a PlayerAnalyzer instance.
        """
        print("--- [MatchFinder LOG] Initializing MatchFinder... ---")
        self.player_analyzer = player_analyzer
        try:
            with open(club_profiles_path, 'r', encoding='utf-8') as f:
                profiles_data = json.load(f)
                self.club_profiles = {club['club_name']: club for club in profiles_data}
                print(f"[INFO] Successfully loaded {len(self.club_profiles)} club profiles.")
            self._calculate_league_averages()
            print("✅ MatchFinder initialized and league averages calculated.")
        except FileNotFoundError:
            self.club_profiles = []
            print(f"❌ ERROR: Club profiles file not found at {club_profiles_path}")

    def _calculate_league_averages(self):
        # ... (This method is correct and remains the same)
        self.league_averages = {"depth": {}, "age": {}, "net_spend": 0}
        all_positions = defaultdict(lambda: {'depths': [], 'ages': []})
        all_spends = []
        for club in self.club_profiles.values():
            poc_metrics = club.get('poc_metrics', {})
            if not poc_metrics: continue

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
        # This function is now rewritten to correctly use the new matrix.
        if not club_formation or not isinstance(club_formation, str):
            return 50

        best_match_key = next((key for key in FORMATION_FIT_MATRIX if key in player_position), None)
        return FORMATION_FIT_MATRIX[best_match_key].get(club_formation, 70) if best_match_key else 70
        # Find the best matching key from our matrix (e.g., "Right Winger" matches "Winger")
        #best_match_key = None
        #for key in FORMATION_FIT_MATRIX.keys():
        #    if key in player_position:
        #        best_match_key = key
        #        break
        
        #if best_match_key:
        #    return FORMATION_FIT_MATRIX[best_match_key].get(club_formation, 50) # Use the specific scores for that role

        #return 70 # Return a default score if no specific role is found

    def _calculate_match_score(self, player_profile: dict, club_profile: dict) -> dict:
        """
        Calculates the final match score and generates the reasons for a single player-club pair.
        """
        player_pos = player_profile['position_name']
        poc_metrics = club_profile.get('poc_metrics', {})
        
        # Fail-safe for promoted teams with no data
        if not poc_metrics:
            return None

        attractiveness_index = poc_metrics.get('deal_attractiveness_index', {})
        if player_pos not in attractiveness_index:
            return None

        deal_score = attractiveness_index[player_pos]
        club_formation = poc_metrics.get('tactical_analysis', {}).get('primary_formation')
        tactical_score = self._get_tactical_fit_score(player_pos, club_formation)
        final_score = (deal_score * 0.70) + (tactical_score * 0.30)
        
        # Generate dynamic reasons
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
        
        return {
            "club_name": club_profile['club_name'],
            "match_score": round(final_score, 1),
            "reason": reason_str,
            "deal_score": deal_score,
            "tactical_score": tactical_score
        }

    def find_best_matches(self, player_profile: dict) -> list:
        """
        Analyzes all clubs to find the best matches for a given player profile,
        including a key differentiator for the top recommendation.
        """
        if not player_profile or 'position_name' not in player_profile:
            print("❌ ERROR: Invalid player profile provided.")
            return []

        # Loop through all clubs and call the central scoring function
        all_matches = []
        for club_profile in self.club_profiles.values():
            match_scores = self._calculate_match_score(player_profile, club_profile)
            if match_scores:
                all_matches.append(match_scores)
        
        # Sort all matches first
        sorted_matches = sorted(all_matches, key=lambda x: x['match_score'], reverse=True)
        
        # --- Your existing differentiator logic is preserved here ---
        if len(sorted_matches) > 1:
            top_match = sorted_matches[0]
            second_match = sorted_matches[1]
            
            # Condition 1: Check if scores are close (<= 5% difference)
            # Add a check to prevent division by zero if the second match score is 0
            if second_match['match_score'] > 0:
                score_diff_percent = ((top_match['match_score'] - second_match['match_score']) / second_match['match_score']) * 100
                if score_diff_percent <= 5.0:
                    deal_diff = top_match['deal_score'] - second_match['deal_score']
                    tactical_diff = top_match['tactical_score'] - second_match['tactical_score']
                    
                    # Identify which factor was more decisive
                    if deal_diff > tactical_diff:
                        top_match['highlight_driver'] = "Low Depth"
                    else:
                        top_match['highlight_driver'] = "Ideal Formation"

            # Condition 2: Check if the key driver lists are identical
            if top_match.get('reason') == second_match.get('reason'):
                deal_diff = top_match['deal_score'] - second_match['deal_score']
                if deal_diff > 5:
                    top_match['differentiator_text'] = "Higher underlying need & financial score."
                else:
                    top_match['differentiator_text'] = "Slightly better overall fit."

        return sorted_matches

    def find_best_players_for_club(self, target_club_name: str, target_position_group: str) -> list:
        """
        Finds the best-fitting players for a specific club and position, ensuring each player is analyzed only once.
        """
        print(f"\n--- [Club Needs LOG] Starting new search for a '{target_position_group}' for '{target_club_name}' ---")
        
        target_club_profile = self.club_profiles.get(target_club_name)
        if not target_club_profile:
            print(f"  [ERROR] Could not find profile for club: {target_club_name}")
            return []

        all_players = self.player_analyzer.players_df

        # --- De-duplicate the player list ---
        # 1. Sort players by minutes played to ensure their primary position/entry is first.
        sorted_players_by_minutes = all_players.sort_values(by='total.minutesOnField', ascending=False)
        
        # 2. Drop duplicates based on the player's full name, keeping only their most-played role.
        unique_players_df = sorted_players_by_minutes.drop_duplicates(subset='full_name', keep='first')
        
        # 3. Now, filter these unique players by the desired position group.
        relevant_players = unique_players_df[unique_players_df['position_group'] == target_position_group]
        print(f"  [LOG] Found {len(relevant_players)} unique players in the '{target_position_group}' position group.")

        all_player_matches = []
        for _, player_row in relevant_players.iterrows():
            player_profile = self.player_analyzer.get_player_analysis(player_row['firstName'], player_row['lastName'])
            
            if player_profile:
                # This print statement will now only appear once per unique player
                print(f"    -> Analyzing match for player: {player_row['full_name']}")
                match_scores = self._calculate_match_score(player_profile, target_club_profile)
                
                if match_scores:
                    # 1. Get the player's top 3 skills with their percentile data
                    top_skills_data = sorted(player_profile['analysis'].items(), key=lambda item: item[1]['percentile'], reverse=True)[:3]
                    
                    # 2. Format the strengths to include the percentile, separated by a special character
                    strengths_with_scores = []
                    for skill, data in top_skills_data:
                        pretty_name = KPI_FORMATED_NAMES.get(skill, skill)
                        percentile = data['percentile']
                        strength_str = f"{pretty_name} (Top {100-percentile:.0f}%)"
                        strengths_with_scores.append(strength_str)
                    
                    all_player_matches.append({
                        "Player Name": player_row['full_name'],
                        "Age": int((pd.to_datetime('today') - pd.to_datetime(player_row['birthDate'])).days / 365.25),
                        "Current Club": player_row['teams.name'],
                        "Match Score": match_scores['match_score'],
                        # 3. Join with a unique separator for easy splitting in the UI
                        "Key Strengths": " | ".join(strengths_with_scores) 
                    })

        sorted_players = sorted(all_player_matches, key=lambda x: x['Match Score'], reverse=True)
        print(f"--- [Club Needs LOG] Search complete. Returning {len(sorted_players)} players. ---")
        return sorted_players

# --- Main execution block for testing ---
if __name__ == "__main__":
    analyzer = PlayerAnalyzer(stats_path=PLAYERS_STATS_FILE, physical_path=PLAYERS_PHYSICAL_FILE)
    finder = MatchFinder(
        club_profiles_path='./data/processed/club_profiles_final.json',
        player_analyzer=analyzer
    )

    # --- Run the ORIGINAL test ---
    print("\n--- [TEST] Running original player-to-club match test... ---")
    
    # Get the profile for a specific player
    player_to_test = analyzer.get_player_analysis(first_name="Albion", last_name="Rrahmani")
    
    if player_to_test:
        # Find the best clubs for that player
        best_clubs = finder.find_best_matches(player_to_test)
        
        # Print the top 3 results
        print("\n--- TEST RESULTS: Top 3 Club Matches for Albion Rrahmani ---")
        for club in best_clubs[:3]:
            print(club)
    else:
        print("Could not find test player 'Albion Rrahmani'.")
