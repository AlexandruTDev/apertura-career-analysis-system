# wyscout_loader.py (Updated for Raw/Processed Pipeline)

import pandas as pd
import os

class WyscoutDataLoader:
    """
    A class dedicated to loading the Wyscout CSV files provided by the Federation.
    It reads the data into pandas DataFrames for easy manipulation.
    """
    def __init__(self, data_folder_path: str):
        if not os.path.isdir(data_folder_path):
            raise FileNotFoundError(f"The specified data folder does not exist: {data_folder_path}")
        
        self.base_path = data_folder_path
        
        # These will hold the data as pandas DataFrames
        self.teams_df = None
        self.players_df = None
        
        print("WyscoutDataLoader initialized for CSV files.")

    def load_romanian_superliga_data(self) -> bool:
        """
        Loads the specific CSV summary files for the Romanian Superliga.
        """
        # --- File Mapping (Updated with correct subfolder paths) ---
        files_to_load = {
            "teams": "raw/Superliga_Teams_24_25_adv_stats.csv",
            "players": "processed/players_manually_enriched.csv" # <-- This is the main change
        }

        try:
            teams_path = os.path.join(self.base_path, files_to_load['teams'])
            print(f"Loading {files_to_load['teams']}...")
            self.teams_df = pd.read_csv(teams_path)

            players_path = os.path.join(self.base_path, files_to_load['players'])
            print(f"Loading {files_to_load['players']}...")
            self.players_df = pd.read_csv(players_path)
            
            print("✅ Romanian Superliga summary data loaded successfully into pandas DataFrames.")
            return True
        except FileNotFoundError as e:
            print(f"❌ ERROR: A data file was not found. Please check your file paths and names. Details: {e}")
            return False

# --- The test block below should also be updated if you want to run it directly ---
if __name__ == "__main__":
    DATA_FOLDER = "./data" 
    
    loader = WyscoutDataLoader(data_folder_path=DATA_FOLDER)
    success = loader.load_romanian_superliga_data()

    if success:
        print("\n--- DataFrames Loaded ---")
        print(f"Teams DataFrame Shape: {loader.teams_df.shape}")
        print(f"Players DataFrame Shape: {loader.players_df.shape}")
        
        print("\n--- First 3 Teams ---")
        print(loader.teams_df.head(3))
        
        print("\n--- First 3 Players (from enriched file) ---")
        print(loader.players_df[['shortName', 'teams.name', 'total.minutesOnField']].head(3))