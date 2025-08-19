# scrapers/data_collector.py (Final Version with Reliable URL)
import requests
import pandas as pd
import os
from tqdm import tqdm
import re

def extract_event_id(url):
    """Extracts the event ID from a Sofascore URL."""
    if not isinstance(url, str): return None
    match = re.search(r'#id:(\d+)', url)
    return match.group(1) if match else None

def collect_player_data(fixtures_path: str, matches_lookup_path: str, output_path: str):
    """
    Uses the soccerdata library to fetch player positional data for a list of matches.
    """
    try:
        fixtures_df = pd.read_csv(fixtures_path)
        matches_df = pd.read_csv(matches_lookup_path)
        print("[INFO] Successfully loaded both CSV files.")
    except FileNotFoundError as e:
        print(f"❌ ERROR: Could not find a required file: {e}")
        return

    # --- THE FIX IS HERE: Use a more reliable URL for the teams file ---
    try:
        print("[INFO] Downloading the official Wyscout teams mapping file from GitHub mirror...")
        teams_url = "https://raw.githubusercontent.com/koushikkirugulige/wyscout-data/master/teams.json"
        teams_json = requests.get(teams_url).json()
        teams_df = pd.DataFrame(teams_json)
        print("[INFO] Successfully downloaded and loaded teams data.")
    except Exception as e:
        print(f"❌ ERROR: Failed to download or process the teams.json file: {e}")
        return


    fixtures_df['matchday'] = pd.to_numeric(fixtures_df['matchday'])
    matches_df['matchday'] = pd.to_numeric(matches_df['matchday'])
    all_player_positions = []

    for _, fixture in tqdm(fixtures_df.iterrows(), total=fixtures_df.shape[0], desc="Processing Fixtures"):
        club_name = fixture['clubName']
        matchday = fixture['matchday']

        match_info = matches_df[
            (matches_df['matchday'] == matchday) & 
            ((matches_df['homeTeam'].str.contains(club_name, case=False, na=False)) | 
             (matches_df['awayTeam'].str.contains(club_name, case=False, na=False)))
        ]

        if match_info.empty: continue
        event_url = match_info.iloc[0]['eventURL']
        event_id = int(extract_event_id(event_url))
        if not event_id: continue
        
        try:
            # This part will be enabled once we move to heatmap collection
            pass

        except Exception as e:
            print(f"  [ERROR] Failed to process event ID {event_id}: {e}")

    # For now, let's just do the merge and save the enriched file
    team_profiles_df = pd.read_csv('Liga_II_team_profiles_24_25.csv')
    teams_df.rename(columns={'wyId': 'currentTeamId', 'officialName': 'teamName'}, inplace=True)
    enriched_profiles_df = pd.merge(
        team_profiles_df, 
        teams_df[['currentTeamId', 'teamName']], 
        on='currentTeamId', 
        how='left'
    )
    cols = ['currentTeamId', 'teamName'] + [col for col in enriched_profiles_df.columns if col not in ['currentTeamId', 'teamName']]
    enriched_profiles_df = enriched_profiles_df[cols]
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    enriched_profiles_df.to_csv(output_path, index=False)
    print(f"\n✅ Successfully enriched team profiles with names.")
    print(f"Final data saved to: {output_path}")
    print("\nHere is a sample of the final data:")
    print(enriched_profiles_df[['currentTeamId', 'teamName', 'total.goals', 'total.shots']].head())


if __name__ == "__main__":
    collect_player_data(
        fixtures_path="./data/processed/club_fixtures.csv",
        matches_lookup_path="./data/manual/sofascore_matches.csv",
        output_path="./data/processed/Liga_II_team_profiles_with_names_24_25.csv"
    )