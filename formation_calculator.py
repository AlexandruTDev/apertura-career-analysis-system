# formation_calculator.py

import pandas as pd
import os
import unicodedata

# We need our normalization function here as well
def normalize_text(text: str) -> str:
    if not isinstance(text, str): return text
    return "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

class FormationCalculator:
    def __init__(self, data_folder_path: str):
        self.base_path = data_folder_path

    def get_primary_formation(self, team_name: str, team_id: int) -> str | None:
        """
        Calculates the most frequent formation for a team from their event file.
        """
        # --- THE FIX IS HERE ---
        # We now use our robust normalize_text function
        team_name_normalized = normalize_text(team_name)
        team_name_slug = team_name_normalized.replace(" ", "_")
        event_file = f"{team_name_slug}_2024_2025_events.csv"
        file_path = os.path.join(self.base_path, 'raw', event_file)

        print(f"[LOG] Searching for event file: {file_path}")
        if not os.path.exists(file_path):
            print(f"[LOG] Event file not found for {team_name}. Cannot calculate formation.")
            return None
        
        try:
            events_df = pd.read_csv(file_path)
            team_events_df = events_df[events_df['team.id'] == team_id]
            
            if team_events_df.empty or 'team.formation' not in team_events_df.columns:
                return None

            primary_formation = team_events_df['team.formation'].mode()[0]
            print(f"[LOG] Calculated primary formation for {team_name}: {primary_formation}")
            return primary_formation

        except Exception as e:
            print(f"❌ Error processing event file for {team_name}: {e}")
            return None