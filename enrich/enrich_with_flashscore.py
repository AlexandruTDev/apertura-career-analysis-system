# enrich_with_flashscore.py (Final Version - Enhanced Logging)

import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import os
from tqdm import tqdm
import json

# --- Configuration ---
INPUT_FILE = './data/raw/Romania_Superliga_Players_24_25_adv_stats.csv'
OUTPUT_FILE = './data/processed/players_enriched_flashscore_final.csv'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
# DEVELOPMENT_LIMIT = 10

def search_for_player_url(player_name: str) -> str | None:
    # This function is working well and remains the same
    search_query = requests.utils.quote(player_name)
    search_url = f"https://s.livesport.services/api/v2/search/?q={search_query}&lang-id=1&type-ids=1,2,3,4&project-id=2&project-type-id=1"
    try:
        response = requests.get(search_url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        for result in data:
            if result.get("sport", {}).get("name") == "Soccer":
                url_slug = result.get("url")
                player_id = result.get("id")
                if url_slug and player_id:
                    return f"https://www.flashscore.com/player/{url_slug}/{player_id}/"
        return None
    except (requests.exceptions.RequestException, json.JSONDecodeError):
        return None

def scrape_player_career(player_url: str, player_name: str, target_season: str, target_competition: str) -> str | None:
    """
    Scrapes the player's 'League' career table with the player's name in the logs.
    """
    try:
        response = requests.get(player_url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        league_career_table = soup.find('div', id='league')
        if not league_career_table:
            return None

        career_rows = league_career_table.find_all('div', class_='careerTab__row')
        
        for row in career_rows:
            season_tag = row.select_one("span.careerTab__season")
            team_tag = row.select_one("div.careerTab__participant strong")
            competition_tag = row.select_one("div.careerTab__competition span")

            if season_tag and team_tag and competition_tag:
                season = season_tag.text.strip()
                team = team_tag.text.strip()
                competition = competition_tag.text.strip()
                
                if season == target_season and target_competition in competition:
                    return team
        
        # --- THE FIX IS HERE ---
        # Added the player_name to the FAILED log message.
        print(f"[LOG] FAILED for '{player_name}': No row found for {target_season} in {target_competition}.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error for '{player_name}' while scraping career page: {e}")
        return None

def enrich_player_data_with_flashscore():
    """Main pipeline to enrich player data from Flashscore."""
    try:
        players_df = pd.read_csv(INPUT_FILE, na_values=[''])
    except FileNotFoundError:
        print(f"❌ ERROR: Input file not found at {INPUT_FILE}")
        return
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    if 'fs_club' not in players_df.columns: players_df['fs_club'] = pd.Series(dtype='str')

    missing_data_df = players_df[players_df['teams.name'].isna()].copy()
    unique_players_to_search = missing_data_df[['firstName', 'lastName']].drop_duplicates().reset_index(drop=True)
    
    print(f"--- Found {len(unique_players_to_search)} unique players with missing club data. ---")

    # if DEVELOPMENT_LIMIT is not None:
    #     print(f"🚀 DEVELOPMENT MODE ACTIVE: Processing a maximum of {DEVELOPMENT_LIMIT} players.")
    #     unique_players_to_search = unique_players_to_search.head(DEVELOPMENT_LIMIT)

    player_club_map = {}

    for index, row in tqdm(unique_players_to_search.iterrows(), total=len(unique_players_to_search), desc="Enriching from Flashscore"):
        full_name = f"{row.get('firstName', '')} {row.get('lastName', '')}".strip()
        if not full_name: continue

        player_url = search_for_player_url(full_name)
        time.sleep(1)

        if player_url:
            # Pass the full_name to the scraping function
            team_name = scrape_player_career(player_url, full_name, "2024/2025", "Superliga")
            if team_name:
                print(f"✅ Mapping found for {full_name}: {team_name}")
                player_club_map[full_name] = team_name
            time.sleep(1)
            
    print(f"\n[LOG] Finished scraping. Found clubs for {len(player_club_map)} players.")

    def map_found_club(row):
        full_name = f"{row.get('firstName', '')} {row.get('lastName', '')}".strip()
        return player_club_map.get(full_name, None)

    players_df['fs_club'] = players_df.apply(
        lambda row: map_found_club(row) if pd.isna(row['teams.name']) else None,
        axis=1
    )

    players_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✅ Flashscore enrichment complete. New file saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    enrich_player_data_with_flashscore()