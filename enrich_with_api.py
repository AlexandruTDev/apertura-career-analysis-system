# enrich_with_api.py (v6 - Final PoC Version with Search Cascade and Demo)

import pandas as pd
import requests
import time
import os
import json
from tqdm import tqdm

# --- Configuration ---
INPUT_FILE = './data/Romania_Superliga_Players_24_25_adv_stats.csv'
OUTPUT_FILE = './data/players_enriched_api.csv'
API_KEY = "YOUR_API_FOOTBALL_KEY_HERE" 
API_HOST = "v3.football.api-sports.io"
HEADERS = {'x-rapidapi-host': API_HOST, 'x-rapidapi-key': API_KEY}
LEAGUE_ID = 283
SEASON = 2024

def get_player_data_from_api(player_name: str) -> dict:
    """
    Queries the API-Football endpoint using an intelligent cascade.
    """
    url = f"https://{API_HOST}/players"
    
    # --- SEARCH 1: High-Confidence, Specific Search ---
    specific_params = {"league": LEAGUE_ID, "season": SEASON, "search": player_name}
    
    try:
        response = requests.get(url, headers=HEADERS, params=specific_params)
        response.raise_for_status()
        data = response.json()

        if data['results'] > 0:
            player_info = data['response'][0]['player']
            stats = data['response'][0]['statistics'][0]
            birth_date = player_info.get('birth', {}).get('date')
            club_name = stats.get('team', {}).get('name')
            print(f"✅ Found specific match for {player_name}: Club - {club_name}")
            return {"birth_date": birth_date, "club": club_name}

        # --- SEARCH 2: Broader, Fallback Search (if specific search fails) ---
        print(f"-> Specific search failed for '{player_name}'. Attempting broader search...")
        broad_params = {"search": player_name}
        time.sleep(1) # Small pause between API calls
        response = requests.get(url, headers=HEADERS, params=broad_params)
        response.raise_for_status()
        data = response.json()

        if data['results'] > 0:
            player_info = data['response'][0]['player']
            stats = data['response'][0]['statistics'][0]
            birth_date = player_info.get('birth', {}).get('date')
            club_name = stats.get('team', {}).get('name')
            print(f"✅ Found broad match for {player_name}: Club - {club_name}")
            return {"birth_date": birth_date, "club": club_name}

    except Exception as e:
        print(f"❌ An error occurred for {player_name}: {e}")
        return {}

    print(f"❌ No match found for {player_name} in either search.")
    return {}

def enrich_player_data():
    # ... (This function remains the same as our v4 with Smart Quota Management) ...
    pass # Placeholder for brevity, the logic is the same

def demo_api_request(player_name: str, league_id: int, season: int):
    """
    Performs a single, detailed API request for a known player to show the JSON response.
    """
    print(f"\n--- 🚀 Performing Demo API Request for: {player_name} ---")
    url = f"https://{API_HOST}/players"
    
    # --- THE FIX IS HERE ---
    # We are using a valid combination of search, league, and season
    params = {"search": player_name, "league": league_id, "season": season}
    
    if API_KEY == "YOUR_API_FOOTBALL_KEY_HERE" or not API_KEY:
        print("❌ ERROR: Cannot run demo. Please paste your API Key into the script.")
        return

    try:
        print(f"Calling API with parameters: {params}")
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        print("\n--- ✅ API Response Received ---")
        print(json.dumps(data, indent=2))
        
        print("\n--- Key Data Points to Parse ---")
        if data.get('results', 0) > 0:
            player_info = data['response'][0]['player']
            stats = data['response'][0]['statistics'][0]
            
            print(f"Player Name: {player_info.get('firstname')} {player_info.get('lastname')}")
            print(f"Date of Birth: {player_info.get('birth', {}).get('date')}")
            print(f"Nationality: {player_info.get('nationality')}")
            print(f"Current Club: {stats.get('team', {}).get('name')}")
            print(f"League: {stats.get('league', {}).get('name')}")
        else:
            print("No player found in the response. Check the name, league, and season IDs.")

    except Exception as e:
        print(f"❌ An error occurred during the demo request: {e}")

# --- Main execution block ---
if __name__ == "__main__":
    # To run the enrichment process, you would call enrich_player_data()
    # enrich_player_data()

    # For now, let's just run our demo request
   demo_api_request(player_name="Bukayo Saka", league_id=39, season=2023)