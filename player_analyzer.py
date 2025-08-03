# player_analyzer.py (v3 - Final with Name Normalization)

import pandas as pd
import os
import unicodedata

# --- Configuration ---
PLAYERS_STATS_FILE = './data/processed/players_manually_enriched.csv'
PLAYERS_PHYSICAL_FILE = './data/raw/Romania_Superliga_24_25_physical_metrics.csv'

# Updated KPI dictionary with new physical metrics
POSITION_KPIS = {
    "Defender": [
        'percent.defensiveDuelsWon', 'total.interceptions', 'percent.aerialDuelsWon',
        'Max Speed', 'Count High Acceleration'
    ],
    "Midfielder": [
        'percent.successfulPasses', 'total.passesToFinalThird', 'total.duelsWon',
        'Total Distance', 'High Intensity (HI) Distance'
    ],
    "Forward": [
        'total.goals', 'percent.goalConversion', 'total.xgShot',
        'Max Speed', 'Count Sprint'
    ]
}

def normalize_text(text: str) -> str:
    """Removes diacritics from a string."""
    if not isinstance(text, str): return text
    return "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def get_position_group(player_position: str) -> str:
    if 'Back' in player_position or 'Defender' in player_position: return 'Defender'
    if 'Midfielder' in player_position: return 'Midfielder'
    if 'Winger' in player_position or 'Striker' in player_position or 'Forward' in player_position: return 'Forward'
    return 'Other'

class PlayerAnalyzer:
    def __init__(self, stats_path: str, physical_path: str):
        """Initializes by loading, normalizing, and merging both player data sources."""
        try:
            stats_df = pd.read_csv(stats_path, na_values=[''])
            physical_df = pd.read_csv(physical_path, na_values=[''])
            
            # --- THE FIX IS HERE ---
            # Create a clean, normalized name column in both DataFrames before merging.
            stats_df['normalized_name'] = stats_df['shortName'].apply(normalize_text)
            physical_df['normalized_name'] = physical_df['player_name'].apply(normalize_text)

            # Aggregate the physical data by the normalized name
            physical_agg_df = physical_df.groupby('normalized_name').mean(numeric_only=True).reset_index()
            
            # Merge the two dataframes on the new normalized name column
            self.players_df = pd.merge(stats_df, physical_agg_df, on='normalized_name', how='left')
            print("✅ Player stats and physical data loaded, normalized, and merged successfully.")
            
        except FileNotFoundError as e:
            raise FileNotFoundError(f"ERROR: A data file was not found. Details: {e}")

    def analyze_player(self, first_name: str, last_name: str):
        """
        Performs a full analysis using the player's full name.
        """
        # We also normalize the input names to ensure a match
        normalized_full_name = normalize_text(f"{first_name} {last_name}")
        
        # We need to create a temporary normalized full name column for matching
        self.players_df['temp_full_name'] = (self.players_df['firstName'].apply(normalize_text) + ' ' + self.players_df['lastName'].apply(normalize_text))

        player_data = self.players_df[self.players_df['temp_full_name'] == normalized_full_name]
        
        if player_data.empty:
            print(f"❌ Player '{first_name} {last_name}' not found.")
            return

        # ... (The rest of the analysis logic remains the same) ...
        player_primary_position = player_data.sort_values(by='positions.percent', ascending=False).iloc[0]
        position_name = player_primary_position['positions.position.name']
        position_group = get_position_group(position_name)
        
        print(f"\n--- Analyzing {first_name} {last_name} ---")
        print(f"Primary Position: {position_name} (Group: {position_group})")

        if position_group not in POSITION_KPIS:
            print(f"No KPIs defined for position group: {position_group}")
            return
        
        kpis_to_check = POSITION_KPIS[position_group]
        peer_df = self.players_df[self.players_df['positions.position.name'].apply(get_position_group) == position_group]

        player_analysis = {}
        for kpi in kpis_to_check:
            if kpi not in player_primary_position or pd.isna(player_primary_position[kpi]):
                print(f"  - KPI '{kpi}': Data not available for this player.")
                continue

            player_value = player_primary_position[kpi]
            peer_values = peer_df[kpi].dropna()
            total_peers = len(peer_values)
            
            if total_peers == 0: percentile = 0
            else:
                worse_peers = (peer_values < player_value).sum()
                percentile = (worse_peers / total_peers) * 100
            
            player_analysis[kpi] = percentile
            print(f"  - KPI '{kpi}': {player_value:.2f} (Percentile: {percentile:.1f}%)")

        top_3_skills = sorted(player_analysis.items(), key=lambda item: item[1], reverse=True)[:3]

        print("\n--- 🌟 Top 3 Skills (vs. Superliga Peers) ---")
        for i, (skill, percentile) in enumerate(top_3_skills):
            print(f"{i+1}. {skill} (Top {100-percentile:.0f}%)")


# --- Main execution block ---
if __name__ == "__main__":
    analyzer = PlayerAnalyzer(stats_path=PLAYERS_STATS_FILE, physical_path=PLAYERS_PHYSICAL_FILE)
    
    # Analyze our test case using his full name
    analyzer.analyze_player(first_name="Kennedy Kofi", last_name="Boateng")