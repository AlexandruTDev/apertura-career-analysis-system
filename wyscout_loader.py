# wyscout_loader.py

import pandas as pd
import os

class WyscoutDataLoader:
    def __init__(self, data_folder_path: str):
        if not os.path.isdir(data_folder_path):
            raise FileNotFoundError(f"The specified data folder does not exist: {data_folder_path}")
        
        self.base_path = data_folder_path
        self.teams_df = None
        self.players_df = None
        self.formations_df = None  # This will now hold both formation and status
        self.transfer_balance_df = None
        
        print("WyscoutDataLoader initialized.")

    def load_romanian_superliga_data(self) -> bool:
        """
        Loads all necessary CSV files for the Romanian Superliga analysis.
        """
        files_to_load = {
            "teams": "raw/Superliga_Teams_24_25_adv_stats.csv",
            "players": "processed/players_manually_enriched.csv",
            "formations": "raw/superliga_formations_24_25.csv",
            "transfer_balance": "processed/superliga_transfer_balances.csv"
        }

        try:
            teams_path = os.path.join(self.base_path, files_to_load['teams'])
            self.teams_df = pd.read_csv(teams_path)

            players_path = os.path.join(self.base_path, files_to_load['players'])
            self.players_df = pd.read_csv(players_path)
            
            formations_path = os.path.join(self.base_path, files_to_load['formations'])
            self.formations_df = pd.read_csv(formations_path)

            balance_path = os.path.join(self.base_path, files_to_load['transfer_balance'])
            self.transfer_balance_df = pd.read_csv(balance_path)
            
            print("✅ All Superliga data (teams, players, formations with status) loaded successfully.")
            return True
        except FileNotFoundError as e:
            print(f"❌ ERROR: A data file was not found. Details: {e}")
            return False