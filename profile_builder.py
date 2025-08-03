# profile_builder.py (Final Version with all PoC Metrics)

import pandas as pd
from wyscout_loader import WyscoutDataLoader
import unicodedata
import os
from formation_calculator import FormationCalculator

TEAM_NAME_MAPPING = {
    "Dinamo Bucureşti": "Dinamo Bucuresti", "FCS Bucureşti": "FCS Bucuresti",
    "Rapid Bucureşti": "Rapid Bucuresti", "Politehnica Iaşi": "Poli Iasi",
    "Oţelul": "Otelul", "Botoșani": "Botosani", "Poli Iași": "Poli Iasi",
    "AS FC Buzău": "AS FC Buzau", "Farul Constanța": "Farul Constanta"
}

def normalize_text(text: str) -> str:
    if not isinstance(text, str): return text
    return "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

class ClubProfileBuilder:
    def __init__(self, loader: WyscoutDataLoader):
        if loader.teams_df is None or loader.players_df is None:
            raise ValueError("The provided DataLoader has not loaded the data yet.")
        
        self.loader = loader
        self.formation_calc = FormationCalculator(data_folder_path=loader.base_path)
        self._prepare_player_data()
        self.club_profiles = []
        print("ClubProfileBuilder initialized and player data prepared.")

    def _prepare_player_data(self):
        """Pre-processes player data and determines their status."""
        raw_players_path = os.path.join(self.loader.base_path, 'raw', 'Romania_Superliga_Players_24_25_adv_stats.csv')
        try:
            raw_df = pd.read_csv(raw_players_path, na_values=[''])
        except FileNotFoundError:
            self.loader.players_df['player_status'] = 'Contracted'
            return

        raw_df['player_status'] = raw_df['teams.name'].apply(lambda x: 'Departed' if pd.isna(x) else 'Contracted')
        self.loader.players_df = pd.merge(self.loader.players_df, raw_df[['playerId', 'player_status']], on='playerId', how='left')
        self.loader.players_df['birthDate'] = pd.to_datetime(self.loader.players_df['birthDate'], errors='coerce')

    def _get_mapped_team_name(self, original_name: str) -> str:
        return TEAM_NAME_MAPPING.get(original_name, original_name)

    def _calculate_squad_metrics(self, team_name: str) -> dict:
        # This function is complete and working
        mapped_name = self._get_mapped_team_name(team_name)
        team_players_df = self.loader.players_df[
            (self.loader.players_df['teams.name'] == mapped_name) &
            (self.loader.players_df['player_status'] == 'Contracted')
        ].copy()
        if team_players_df.empty: return {}
        today = pd.to_datetime('today')
        team_players_df['age'] = (today - team_players_df['birthDate']).dt.days / 365.25
        position_agg = team_players_df.groupby('positions.position.name').agg(
            depth=('playerId', 'count'),
            avg_age=('age', 'mean'),
            incumbent_minutes_played=('total.minutesOnField', 'max')
        ).reset_index()
        squad_metrics = {}
        for index, row in position_agg.iterrows():
            squad_metrics[row['positions.position.name']] = {
                "depth": int(row['depth']), "avg_age": round(row['avg_age'], 1),
                "incumbent_minutes_played": int(row['incumbent_minutes_played'])
            }
        return squad_metrics

    def _calculate_squad_disruption(self, team_name: str) -> dict:
        # This function is complete and working
        mapped_name = self._get_mapped_team_name(team_name)
        departed_players_df = self.loader.players_df[
            (self.loader.players_df['teams.name'] == mapped_name) &
            (self.loader.players_df['player_status'] == 'Departed')
        ]
        if departed_players_df.empty:
            return {"squad_disruption_score": 0.0, "details": "No departures identified."}
        departed_count = len(departed_players_df)
        production_lost = departed_players_df['total.goals'].sum() + departed_players_df['total.assists'].sum()
        disruption_score = min(round((departed_count / 5.0) * 10, 1), 10.0)
        return {
            "squad_disruption_score": disruption_score,
            "departed_player_count": int(departed_count),
            "production_lost_goals_assists": int(production_lost)
        }

    def _calculate_tactical_metrics(self, team_name: str, team_id: int) -> dict: # <-- THE FIX IS HERE
        """
        Calculates the tactical profile for a single team.
        """
        team_stats = self.loader.teams_df[self.loader.teams_df['team.name'] == team_name]
        
        possession, pass_length, ppda = None, None, None
        
        if not team_stats.empty:
            stats_row = team_stats.iloc[0]
            possession = round(stats_row.get('average.possessionPercent', 0), 1)
            pass_length = round(stats_row.get('average.passLength', 0), 1)
            ppda = round(stats_row.get('total.ppda', 0), 1)

        # We will use the 'team_id' here in the future to find the event file
        formation = self.formation_calc.get_primary_formation(team_name, team_id)
        if formation is None:
            formation = "Data Not Available"
            
        return {
            "avg_possession_percentage": possession,
            "avg_pass_length": pass_length,
            "ppda": ppda,
            "primary_formation": formation
        }

    def build_all_profiles(self):
        """
        Main method to build a complete profile for each team by iterating through the teams DataFrame.
        """
        # Ensure the list is clear before we start building
        self.club_profiles = []
        
        print("Starting to build full club profiles...")
        
        # We iterate through the teams DataFrame to get both name and ID for each team
        for index, row in self.loader.teams_df.iterrows():
            team_name = row['team.name']
            team_id = row['teamId']
            
            # Create the final JSON structure for the current team
            profile = {
                "club_name": normalize_text(team_name),
                "league_name": "Romanian Superliga",
                "season": "2024-2025",
                "poc_metrics": {
                    "tactical_analysis": self._calculate_tactical_metrics(team_name, team_id),
                    "current_squad_analysis": self._calculate_squad_metrics(team_name),
                    "squad_disruption_analysis": self._calculate_squad_disruption(team_name)
                }
            }
            # Add the completed profile to our list
            self.club_profiles.append(profile)
        
        print(f"Successfully built complete profiles for {len(self.club_profiles)} teams.")
        return self.club_profiles