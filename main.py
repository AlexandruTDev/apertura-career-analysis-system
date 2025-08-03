# main.py

import json
from wyscout_loader import WyscoutDataLoader
from profile_builder import ClubProfileBuilder

# --- Configuration ---
DATA_FOLDER = "./data"
# Define a path for our final output file
OUTPUT_FILE = "./data/processed/club_profiles_final.json" 

# --- Main Pipeline ---
if __name__ == "__main__":
    print("\n--- Running Main Data Pipeline ---")
    
    # Step 1: Load the data from the correct subfolders
    loader = WyscoutDataLoader(data_folder_path=DATA_FOLDER)
    load_success = loader.load_romanian_superliga_data()

    if load_success:
        # Step 2: Build the profiles if data loaded successfully
        builder = ClubProfileBuilder(loader=loader)
        profiles = builder.build_all_profiles()

        # Step 3: Save the complete output to a file
        if profiles:
            print(f"\n✅ Successfully generated {len(profiles)} club profiles.")
            
            # Use a 'with' statement to safely open and write to the file
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                # json.dump (no 's') writes directly to a file object
                json.dump(profiles, f, indent=2, ensure_ascii=False)
                
            print(f"Final JSON output saved to: {OUTPUT_FILE}")
            
            # We can still print a sample if we want
            print("\n--- Sample of first club profile ---")
            print(json.dumps(profiles[0], indent=2, ensure_ascii=False))