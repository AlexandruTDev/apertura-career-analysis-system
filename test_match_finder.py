# test_match_finder.py
from player_analyzer import PlayerAnalyzer, PLAYERS_STATS_FILE, PLAYERS_PHYSICAL_FILE
from match_finder import MatchFinder
import pandas as pd

def print_head_to_head_comparison(match_finder, player_pos, club1_name, club2_name):
    """
    Prints a detailed, side-by-side comparison of two clubs for a specific position.
    """
    print("\n--- [DEBUG] Head-to-Head Analysis ---")
    
    avg_depth = match_finder.league_averages['depth'].get(player_pos, 'N/A')
    avg_age = match_finder.league_averages['age'].get(player_pos, 'N/A')
    avg_spend = match_finder.league_averages['net_spend']
    
    print(f"\nLeague Averages for Position: '{player_pos}'")
    print(f"  - Avg. Depth: {avg_depth:.1f}")
    print(f"  - Avg. Age: {avg_age:.1f}")
    print(f"  - Avg. Net Spend (All Clubs): €{avg_spend/1_000_000:.2f}m")
    
    club1_data = next((club for club in match_finder.club_profiles if club['club_name'] == club1_name), None)
    club2_data = next((club for club in match_finder.club_profiles if club['club_name'] == club2_name), None)

    if not club1_data or not club2_data:
        print("\n[DEBUG] Could not find data for one of the clubs.")
        return

    c1_pos_data = club1_data['poc_metrics']['current_squad_analysis'].get(player_pos, {})
    c2_pos_data = club2_data['poc_metrics']['current_squad_analysis'].get(player_pos, {})
    c1_finance = club1_data['poc_metrics']['financial_analysis']['two_year_net_spend']
    c2_finance = club2_data['poc_metrics']['financial_analysis']['two_year_net_spend']
    c1_formation = club1_data['poc_metrics']['tactical_analysis']['primary_formation']
    c2_formation = club2_data['poc_metrics']['tactical_analysis']['primary_formation']

    data = {
        "Metric": ["Depth", "Avg. Age", "Net Spend", "Formation"],
        club1_name: [c1_pos_data.get('depth', 'N/A'), c1_pos_data.get('avg_age', 'N/A'), c1_finance, c1_formation],
        club2_name: [c2_pos_data.get('depth', 'N/A'), c2_pos_data.get('avg_age', 'N/A'), c2_finance, c2_formation]
    }
    df = pd.DataFrame(data)
    print("\n--- Comparison ---")
    print(df.to_string(index=False))

def run_test():
    """
    Runs a test of the MatchFinder with a hardcoded player.
    """
    # --- NEW TEST PLAYER ---
    first_name = "Adama"
    last_name = "Diakhaby"
    
    print(f"--- [TEST] Starting match-finding test for: {first_name} {last_name} ---")

    analyzer = PlayerAnalyzer(stats_path=PLAYERS_STATS_FILE, physical_path=PLAYERS_PHYSICAL_FILE)
    player_profile = analyzer.get_player_analysis(first_name, last_name)

    if not player_profile:
        print(f"--- [TEST FAILED] Could not generate a profile for {first_name} {last_name}. ---")
        return

    print(f"\n[TEST] Player profile generated. Position: {player_profile.get('position_name')}")

    match_finder = MatchFinder(club_profiles_path='./data/processed/club_profiles_final.json')
    best_matches = match_finder.find_best_matches(player_profile)
    
    print("\n--- [RESULTS] Top 3 Club Matches ---")
    if not best_matches:
        print("No suitable matches found.")
    else:
        for i, match in enumerate(best_matches):
            print(f"{i+1}. {match['club_name']} (Match Score: {match['match_score']})")
            print(f"   - Key Drivers: {match['reason']}")
            
    if best_matches and len(best_matches) > 1:
        print_head_to_head_comparison(
            match_finder=match_finder,
            player_pos=player_profile['position_name'],
            club1_name=best_matches[0]['club_name'],
            club2_name=best_matches[1]['club_name']
        )

if __name__ == "__main__":
    run_test()