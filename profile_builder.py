# profile_builder.py (Final PoC Version)

import pandas as pd
from wyscout_loader import WyscoutDataLoader
import unicodedata
import os
from deal_attractiveness_calculator import DealAttractivenessCalculator

TEAM_NAME_MAPPING = {
    "Dinamo Bucureşti": "Dinamo Bucuresti", "FCS Bucureşti": "FCS Bucuresti",
    "Rapid Bucureşti": "Rapid Bucuresti", "Politehnica Iaşi": "Poli Iasi",
    "Oţelul": "Otelul", "Botoșani": "Botosani", "Poli Iași": "Poli Iasi",
    "AS FC Buzău": "AS FC Buzau", "Farul Constanța": "Farul Constanta",
    "FCSB": "FCS Bucuresti", "CFR Cluj": "CFR Cluj",
    "CS Universitatea Craiova": "Universitatea Craiova",
    "FC Rapid 1923": "Rapid Bucuresti", "FC Dinamo 1948": "Dinamo Bucuresti",
    "FC Hermannstadt": "Hermannstadt", "SC Otelul Galati": "Otelul",
    "FCV Farul Constanta": "Farul Constanta", "Petrolul Ploiesti": "Petrolul 52",
    "UTA Arad": "UTA Arad", "Sepsi OSK Sf. Gheorghe": "Sepsi",
    "FC Botosani": "Botosani", "FC Universitatea Cluj": "Universitatea Cluj",
    "ACSM Politehnica Iasi": "Poli Iasi", "AFC Unirea 04 Slobozia": "Unirea Slobozia"
}

def normalize_text(text: str) -> str:
    if not isinstance(text, str): return text
    return "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

class ClubProfileBuilder:
    def __init__(self, loader: WyscoutDataLoader):
        if loader.teams_df is None or loader.players_df is None or loader.formations_df is None:
            raise ValueError("DataLoader has not loaded all required data yet.")
        
        self.loader = loader
        self.attractiveness_calc = DealAttractivenessCalculator()
        self.club_profiles = []
        
        self._normalize_all_data()
        self._prepare_player_data()
        print("ClubProfileBuilder initialized and all data has been normalized.")

    def _normalize_all_data(self):
        """Creates a consistent, normalized name column in all dataframes."""
        self.loader.teams_df['clean_name'] = self.loader.teams_df['team.name'].apply(normalize_text)
        self.loader.players_df['clean_name'] = self.loader.players_df['teams.name'].map(TEAM_NAME_MAPPING).fillna(self.loader.players_df['teams.name'])
        self.loader.players_df['clean_name'] = self.loader.players_df['clean_name'].apply(normalize_text)
        self.loader.formations_df['clean_name'] = self.loader.formations_df['team.name'].apply(normalize_text)
        self.loader.transfer_balance_df['clean_name'] = self.loader.transfer_balance_df['club_name_transfermarkt'].map(TEAM_NAME_MAPPING).fillna(self.loader.transfer_balance_df['club_name_transfermarkt'])
        self.loader.transfer_balance_df['clean_name'] = self.loader.transfer_balance_df['clean_name'].apply(normalize_text)

    def _prepare_player_data(self):
        raw_players_path = os.path.join(self.loader.base_path, 'raw', 'Romania_Superliga_Players_24_25_adv_stats.csv')
        raw_df = pd.read_csv(raw_players_path, na_values=[''])
        raw_df['player_status'] = raw_df['teams.name'].apply(lambda x: 'Departed' if pd.isna(x) else 'Contracted')
        self.loader.players_df = pd.merge(self.loader.players_df, raw_df[['playerId', 'player_status']], on='playerId', how='left')
        self.loader.players_df['birthDate'] = pd.to_datetime(self.loader.players_df['birthDate'], errors='coerce')

    def _get_mapped_team_name(self, original_name: str) -> str:
        return TEAM_NAME_MAPPING.get(original_name, original_name)

    def _calculate_squad_metrics(self, clean_team_name: str) -> dict:
        team_players_df = self.loader.players_df[(self.loader.players_df['clean_name'] == clean_team_name) & (self.loader.players_df['player_status'] == 'Contracted')].copy()
        if team_players_df.empty: return {}
        today = pd.to_datetime('today')
        team_players_df['age'] = (today - team_players_df['birthDate']).dt.days / 365.25
        position_agg = team_players_df.groupby('positions.position.name').agg(depth=('playerId', 'count'), avg_age=('age', 'mean'), incumbent_minutes_played=('total.minutesOnField', 'max')).reset_index()
        squad_metrics = {}
        for index, row in position_agg.iterrows():
            squad_metrics[row['positions.position.name']] = {"depth": int(row['depth']), "avg_age": round(row['avg_age'], 1), "incumbent_minutes_played": int(row['incumbent_minutes_played'])}
        return squad_metrics
        
    def _calculate_squad_disruption(self, clean_team_name: str) -> dict:
        all_players_df = self.loader.players_df[self.loader.players_df['clean_name'] == clean_team_name]
        departed_players_df = all_players_df[all_players_df['player_status'] == 'Departed']
        if departed_players_df.empty: return {"squad_disruption_score": 0.0, "departed_player_count": 0, "production_lost_goals": 0, "production_lost_assists": 0, "minutes_lost_percentage": 0.0}
        total_squad_minutes = all_players_df['total.minutesOnField'].sum()
        minutes_lost = departed_players_df['total.minutesOnField'].sum()
        minutes_lost_percentage = (minutes_lost / total_squad_minutes) * 100 if total_squad_minutes > 0 else 0
        departed_count = len(departed_players_df)
        goals_lost = departed_players_df['total.goals'].sum()
        assists_lost = departed_players_df['total.assists'].sum()
        total_production_lost = goals_lost + assists_lost
        count_score = min((departed_count / 15) * 100, 100)
        minutes_score = min((minutes_lost_percentage / 50) * 100, 100)
        production_score = min((total_production_lost / 40) * 100, 100)
        weights = {'minutes': 0.60, 'count': 0.25, 'production': 0.15}
        final_disruption_score = (minutes_score * weights['minutes'] + count_score * weights['count'] + production_score * weights['production'])
        return {"squad_disruption_score": round(final_disruption_score / 10, 1), "departed_player_count": int(departed_count), "production_lost_goals": int(goals_lost), "production_lost_assists": int(assists_lost), "minutes_lost_percentage": round(minutes_lost_percentage, 1)}

    def _calculate_tactical_metrics(self, clean_team_name: str) -> dict:
        team_stats = self.loader.teams_df[self.loader.teams_df['clean_name'] == clean_team_name]
        possession, pass_length, ppda = None, None, None
        if not team_stats.empty:
            stats_row = team_stats.iloc[0]
            possession = round(stats_row.get('average.possessionPercent', 0), 1)
            pass_length = round(stats_row.get('average.passLength', 0), 1)
            ppda = round(stats_row.get('total.ppda', 0), 1)
        team_formation_data = self.loader.formations_df[self.loader.formations_df['clean_name'] == clean_team_name]
        primary_formation, secondary_formation = "Data Not Available", None
        if not team_formation_data.empty:
            primary_formation = team_formation_data.iloc[0]['formation.primary']
            if 'formation.secondary' in team_formation_data.columns and pd.notna(team_formation_data.iloc[0]['formation.secondary']):
                secondary_formation = team_formation_data.iloc[0]['formation.secondary']
        return {"avg_possession_percentage": possession, "avg_pass_length": pass_length, "ppda": ppda, "primary_formation": primary_formation, "secondary_formation": secondary_formation}

    def _calculate_financial_analysis(self, clean_team_name: str) -> dict:
        financial_data = self.loader.transfer_balance_df[self.loader.transfer_balance_df['clean_name'] == clean_team_name]
        if not financial_data.empty:
            return {"two_year_net_spend": financial_data.iloc[0]['two_year_net_spend']}
        return {"two_year_net_spend": "Data Not Available"}

    def build_all_profiles(self):
        self.club_profiles = []
        established_teams_df = self.loader.formations_df[self.loader.formations_df['status'] == 'Established']
        teams_to_profile_df = self.loader.teams_df[self.loader.teams_df['clean_name'].isin(established_teams_df['clean_name'].tolist())]
        
        print(f"--- Building profiles for {len(teams_to_profile_df)} established teams ---")
        
        base_profiles = []
        for index, row in teams_to_profile_df.iterrows():
            clean_name = row['clean_name']
            profile = {
                "club_name": clean_name, "league_name": "Romanian Superliga", "season": "2024-2025",
                "poc_metrics": {
                    "financial_analysis": self._calculate_financial_analysis(clean_name),
                    "tactical_analysis": self._calculate_tactical_metrics(clean_name),
                    "current_squad_analysis": self._calculate_squad_metrics(clean_name),
                    "squad_disruption_analysis": self._calculate_squad_disruption(clean_name)
                }
            }
            base_profiles.append(profile)

        for profile in base_profiles:
            attractiveness_scores = self.attractiveness_calc.calculate_deal_attractiveness(profile, base_profiles)
            profile['poc_metrics']['deal_attractiveness_index'] = attractiveness_scores
            self.club_profiles.append(profile)
            
        print(f"Successfully built complete profiles for {len(self.club_profiles)} teams.")
        return self.club_profiles