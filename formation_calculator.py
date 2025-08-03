# formation_calculator.py

import pandas as pd
import os

class FormationCalculator:
    def __init__(self, data_folder_path: str):
        self.base_path = data_folder_path

    def get_primary_formation(self, team_name: str, team_id: int) -> str | None:
        """
        Calculates the most frequent formation for a team from their event file.
        """
        # Normalize the team name to create a likely filename
        team_name_slug = team_name.replace(" ", "_").replace("ş", "s").replace("ţ", "t").replace("ă", "a")
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

            # Get the most frequent formation (the mode) from the column
            primary_formation = team_events_df['team.formation'].mode()[0]
            print(f"[LOG] Calculated primary formation for {team_name}: {primary_formation}")
            return primary_formation

        except Exception as e:
            print(f"❌ Error processing event file for {team_name}: {e}")
            return None