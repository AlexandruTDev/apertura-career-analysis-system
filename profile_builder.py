# profile_builder.py (Final Version with all PoC Metrics)

import pandas as pd
from wyscout_loader import WyscoutDataLoader
import unicodedata
import os
from formation_calculator import FormationCalculator
from deal_attractiveness_calculator import DealAttractivenessCalculator

TEAM_NAME_MAPPING = {
    # Original Mappings from Wyscout
    "Dinamo Bucureşti": "Dinamo Bucuresti", "FCS Bucureşti": "FCS Bucuresti",
    "Rapid Bucureşti": "Rapid Bucuresti", "Politehnica Iaşi": "Poli Iasi",
    "Oţelul": "Otelul", "Botoșani": "Botosani", "Poli Iași": "Poli Iasi",
    "AS FC Buzău": "AS FC Buzau", "Farul Constanța": "Farul Constanta",

    # --- NEW MAPPINGS FROM TRANSFERMARKT ---
    "FCSB": "FCS Bucuresti",
    "CFR Cluj": "CFR Cluj",
    "CS Universitatea Craiova": "Universitatea Craiova",
    "FC Rapid 1923": "Rapid Bucuresti",
    "FC Dinamo 1948": "Dinamo Bucuresti",
    "FC Hermannstadt": "Hermannstadt",
    "SC Otelul Galati": "Otelul",
    "FCV Farul Constanta": "Farul Constanta",
    "Petrolul Ploiesti": "Petrolul 52",
    "UTA Arad": "UTA Arad",
    "Sepsi OSK Sf. Gheorghe": "Sepsi",  # Relegated, will be filtered out
    "FC Botosani": "Botosani",
    "FC Universitatea Cluj": "Universitatea Cluj",
    "ACSM Politehnica Iasi": "Poli Iasi",  # Relegated, will be filtered out
    "AFC Unirea 04 Slobozia": "Unirea Slobozia"  # Relegated, will be filtered out
}

def normalize_text(text: str) -> str:
    if not isinstance(text, str): return text
    return "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

class ClubProfileBuilder:
    def __init__(self, loader: WyscoutDataLoader):
        if loader.teams_df is None or loader.players_df is None or loader.formations_df is None:
            raise ValueError("The provided DataLoader has not loaded all required data yet.")
        
        self.loader = loader
        self._prepare_player_data()
        self.attractiveness_calc = DealAttractivenessCalculator()
        self.club_profiles = []
        print("ClubProfileBuilder initialized.")

    def _prepare_player_data(self):
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
        mapped_name = self._get_mapped_team_name(team_name)
        team_players_df = self.loader.players_df[(self.loader.players_df['teams.name'] == mapped_name) & (self.loader.players_df['player_status'] == 'Contracted')].copy()
        if team_players_df.empty: return {}
        today = pd.to_datetime('today')
        team_players_df['age'] = (today - team_players_df['birthDate']).dt.days / 365.25
        position_agg = team_players_df.groupby('positions.position.name').agg(depth=('playerId', 'count'), avg_age=('age', 'mean'), incumbent_minutes_played=('total.minutesOnField', 'max')).reset_index()
        squad_metrics = {}
        for index, row in position_agg.iterrows():
            squad_metrics[row['positions.position.name']] = {"depth": int(row['depth']), "avg_age": round(row['avg_age'], 1), "incumbent_minutes_played": int(row['incumbent_minutes_played'])}
        return squad_metrics
        
    def _calculate_squad_disruption(self, team_name: str) -> dict:
        """
        Calculates a weighted disruption score, now with separate goal and assist loss tracking.
        """
        mapped_name = self._get_mapped_team_name(team_name)
        all_players_df = self.loader.players_df[self.loader.players_df['teams.name'] == mapped_name]
        departed_players_df = all_players_df[all_players_df['player_status'] == 'Departed']

        if departed_players_df.empty:
            return {
                "squad_disruption_score": 0.0, "departed_player_count": 0,
                "production_lost_goals": 0, "production_lost_assists": 0, # <-- Updated
                "minutes_lost_percentage": 0.0
            }

        # --- Calculations ---
        total_squad_minutes = all_players_df['total.minutesOnField'].sum()
        minutes_lost = departed_players_df['total.minutesOnField'].sum()
        minutes_lost_percentage = (minutes_lost / total_squad_minutes) * 100 if total_squad_minutes > 0 else 0
    
        departed_count = len(departed_players_df)
    
        # We now calculate goals and assists separately.
        goals_lost = departed_players_df['total.goals'].sum()
        assists_lost = departed_players_df['total.assists'].sum()
        total_production_lost = goals_lost + assists_lost

        # --- Weighted Score Calculation (0-100 scale) ---
        count_score = min((departed_count / 15) * 100, 100)
        minutes_score = min((minutes_lost_percentage / 50) * 100, 100)
        production_score = min((total_production_lost / 40) * 100, 100) # The score still uses the total

        weights = {'minutes': 0.60, 'count': 0.25, 'production': 0.15}
    
        final_disruption_score = (
            minutes_score * weights['minutes'] +
            count_score * weights['count'] +
            production_score * weights['production']
        )
    
        return {
            "squad_disruption_score": round(final_disruption_score / 10, 1),
            "departed_player_count": int(departed_count),
            "production_lost_goals": int(goals_lost), # <-- Updated
            "production_lost_assists": int(assists_lost), # <-- Updated
            "minutes_lost_percentage": round(minutes_lost_percentage, 1)
        }

    def _calculate_tactical_metrics(self, team_name: str) -> dict:
        team_stats = self.loader.teams_df[self.loader.teams_df['team.name'] == team_name]
        possession, pass_length, ppda = None, None, None
        if not team_stats.empty:
            stats_row = team_stats.iloc[0]
            possession = round(stats_row.get('average.possessionPercent', 0), 1)
            pass_length = round(stats_row.get('average.passLength', 0), 1)
            ppda = round(stats_row.get('total.ppda', 0), 1)

        normalized_team_name = normalize_text(team_name)
        team_formation_data = self.loader.formations_df[self.loader.formations_df['team.name'] == normalized_team_name]
        
        primary_formation, secondary_formation = "Data Not Available", None
        if not team_formation_data.empty:
            primary_formation = team_formation_data.iloc[0]['formation.primary']
            if 'formation.secondary' in team_formation_data.columns and pd.notna(team_formation_data.iloc[0]['formation.secondary']):
                secondary_formation = team_formation_data.iloc[0]['formation.secondary']
            
        return {
            "avg_possession_percentage": possession, "avg_pass_length": pass_length,
            "ppda": ppda, "primary_formation": primary_formation, "secondary_formation": secondary_formation
        }

    def _calculate_financial_analysis(self, team_name: str) -> dict:
        """
        Looks up the pre-scraped transfer balance for a team.
        """
        mapped_name = self._get_mapped_team_name(team_name)
    
        # We need to normalize the names from the transfer data to match our mapping
        self.loader.transfer_balance_df['mapped_name'] = self.loader.transfer_balance_df['club_name_transfermarkt'].apply(self._get_mapped_team_name)
    
        financial_data = self.loader.transfer_balance_df[self.loader.transfer_balance_df['mapped_name'] == mapped_name]
    
        if not financial_data.empty:
            return {
                "two_year_net_spend": financial_data.iloc[0]['two_year_net_spend']
            }
        return {"two_year_net_spend": "Data Not Available"}

    def build_all_profiles(self):
        """
        Main method to build profiles ONLY for the established Superliga teams.
        """
        self.club_profiles = []
        
        # --- NEW LOGGING ---
        print("\n--- Filtering Teams Based on Status ---")
        established_teams_df = self.loader.formations_df[self.loader.formations_df['status'] == 'Established']
        relegated_teams_df = self.loader.formations_df[self.loader.formations_df['status'] == 'Relegated']
        
        print(f"[LOG] Found {len(established_teams_df)} 'Established' teams to process.")
        if not relegated_teams_df.empty:
            print(f"[LOG] Found {len(relegated_teams_df)} 'Relegated' teams to exclude: {relegated_teams_df['team.name'].tolist()}")

        teams_to_profile_df = pd.merge(
            self.loader.teams_df, 
            established_teams_df[['team.name']], 
            on='team.name', 
            how='inner'
        )
        
        print(f"\n--- Starting to build full club profiles for {len(teams_to_profile_df)} teams. ---")
        
        base_profiles = []
        for index, row in teams_to_profile_df.iterrows():
            team_name = row['team.name']
            profile = {
                "club_name": normalize_text(team_name),
                "league_name": "Romanian Superliga", "season": "2024-2025",
                "poc_metrics": {
                    "financial_analysis": self._calculate_financial_analysis(team_name),
                    "tactical_analysis": self._calculate_tactical_metrics(team_name),
                    "current_squad_analysis": self._calculate_squad_metrics(team_name),
                    "squad_disruption_analysis": self._calculate_squad_disruption(team_name)
                }
            }
            base_profiles.append(profile)

        for profile in base_profiles:
            attractiveness_scores = self.attractiveness_calc.calculate_deal_attractiveness(profile, base_profiles)
            profile['poc_metrics']['deal_attractiveness_index'] = attractiveness_scores
            self.club_profiles.append(profile)
        
        print(f"Successfully built complete profiles for {len(self.club_profiles)} teams.")
        return self.club_profiles
