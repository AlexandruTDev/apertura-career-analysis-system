# main.py

import json
from wyscout_loader import WyscoutDataLoader
from profile_builder import ClubProfileBuilder
# We are no longer importing the API enricher for now
# from enrich_with_api import enrich_player_data 

# --- Configuration ---
DATA_FOLDER = "./data"

# --- Main Pipeline ---
if __name__ == "__main__":
    # --- The API Enrichment step is now 'muted' ---
    # print("--- Stage 1: Running API Enrichment (Currently Muted) ---")
    # enrich_player_data() # We are not running this for the PoC
    
    # --- We proceed directly to building profiles from the available data ---
    print("\n--- Stage 2: Loading Base Data and Building Club Profiles ---")
    
    # Step 1: Load the data
    loader = WyscoutDataLoader(data_folder_path=DATA_FOLDER)
    load_success = loader.load_romanian_superliga_data()

    if load_success:
        # Step 2: Build the profiles if data loaded successfully
        builder = ClubProfileBuilder(loader=loader)
        profiles = builder.build_all_profiles()

        # Step 3: Print a sample of the output to verify
        if profiles:
            print("\n--- Sample of first club profile ---")
            print(json.dumps(profiles[0], indent=2, ensure_ascii=False))