import pandas as pd
from wyscout_loader import WyscoutDataLoader
import unicodedata # Import the library for normalization

# This dictionary solves our name mismatch problem.
TEAM_NAME_MAPPING = {
    "Dinamo Bucureşti": "Dinamo Bucuresti",
    "FCS Bucureşti": "FCS Bucuresti",
    "Rapid Bucureşti": "Rapid Bucuresti",
    "Politehnica Iaşi": "Poli Iasi",
    "Oţelul": "Otelul"
}

def normalize_text(text: str) -> str:
    """Removes diacritics (special characters) from a string."""
    # Decomposes characters like 'ș' into 's' and a combining accent, 
    # then filters out the accent mark.
    return "".join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn')

class ClubProfileBuilder:
    # ... (the __init__ method and other helper methods remain the same) ...
    def __init__(self, loader: WyscoutDataLoader):
        if loader.teams_df is None or loader.players_df is None:
            raise ValueError("The provided DataLoader has not loaded the data yet.")
        
        self.loader = loader
        self.loader.players_df['birthDate'] = pd.to_datetime(self.loader.players_df['birthDate'])
        self.club_profiles = []
        print("ClubProfileBuilder initialized.")

    def _get_mapped_team_name(self, original_name: str) -> str:
        return TEAM_NAME_MAPPING.get(original_name, original_name)

    def _calculate_squad_metrics(self, team_name: str) -> dict:
        mapped_name = self._get_mapped_team_name(team_name)
        team_players_df = self.loader.players_df[self.loader.players_df['teams.name'] == mapped_name].copy()
        if team_players_df.empty:
            print(f"⚠️ Warning: No players found for team '{team_name}' (mapped to '{mapped_name}').")
            return {}
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
                "depth": int(row['depth']),
                "avg_age": round(row['avg_age'], 1),
                "incumbent_minutes_played": int(row['incumbent_minutes_played'])
            }
        return squad_metrics

    def build_all_profiles(self):
        """Main method to loop through all teams and build a profile for each."""
        unique_teams = self.loader.teams_df['team.name'].unique()

        for team_name in unique_teams:
            profile = {
                # We apply our new normalization function right here
                "club_name": normalize_text(team_name),
                "league_name": "Romanian Superliga",
                "season": "2024-2025",
                "poc_metrics": {
                    "tactical": {},
                    "squad_by_position": self._calculate_squad_metrics(team_name)
                }
            }
            self.club_profiles.append(profile)
        
        print(f"Successfully built profiles for {len(self.club_profiles)} teams.")
        return self.club_profiles