# enrich_player_data.py (v2 - More Robust)

import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import os

# --- Configuration ---
INPUT_FILE = './data/Romania_Superliga_Players_24_25_adv_stats.csv'
OUTPUT_FILE = './data/players_enriched_v2.csv'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

def get_player_data_from_transfermarkt(player_name: str) -> dict:
    """
    Scrapes Transfermarkt for a player's data.
    Returns a dictionary with birth_date and club, or a search URL on ambiguity.
    """
    search_query = requests.utils.quote(player_name)
    search_url = f"https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?query={search_query}"
    
    try:
        response = requests.get(search_url, headers=HEADERS)
        response.raise_for_status() 

        soup = BeautifulSoup(response.content, 'html.parser')
        
        results_table = soup.find('div', class_='grid-view')
        if not results_table:
            return {}

        player_rows = results_table.find_all('tr', class_=['odd', 'even'])
        
        if len(player_rows) == 1:
            player_cell = player_rows[0].find('td', class_='hauptlink')
            if player_cell and player_cell.a:
                player_profile_link = player_cell.a['href']
                player_profile_url = f"https://www.transfermarkt.com{player_profile_link}"
                
                profile_response = requests.get(player_profile_url, headers=HEADERS)
                profile_soup = BeautifulSoup(profile_response.content, 'html.parser')
                
                birth_date_span = profile_soup.find('span', itemprop='birthDate')
                club_span = profile_soup.find('span', itemprop='affiliation')

                birth_date = birth_date_span.text.strip().split('(')[0].strip() if birth_date_span else None
                club = club_span.a.img['alt'] if club_span and club_span.a and club_span.a.img else None
                
                if birth_date or club:
                    print(f"✅ Found match for {player_name}: Birth Date - {birth_date}, Club - {club}")
                return {"birth_date": birth_date, "club": club}
        
        elif len(player_rows) > 1:
            print(f"⚠️ Ambiguous match for {player_name}. Manual verification needed.")
            return {"search_url": search_url}

    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error for {player_name}: {e}")
        return {}
        
    return {}


def enrich_player_data():
    """
    Main function to read the player CSV, enrich it with Transfermarkt data,
    and save a new CSV.
    """
    try:
        players_df = pd.read_csv(INPUT_FILE, na_values=[''])
    except FileNotFoundError:
        print(f"❌ ERROR: Input file not found at {INPUT_FILE}")
        return

    # Create new columns if they don't exist
    if 'tm_birthDate' not in players_df.columns:
        players_df['tm_birthDate'] = None
    if 'tm_club' not in players_df.columns:
        players_df['tm_club'] = None

    print("--- Starting Player Data Enrichment Process ---")
    
    for index, row in players_df.iterrows():
        # Check which specific pieces of data are missing
        birth_date_missing = pd.isna(row['birthDate'])
        team_name_missing = pd.isna(row['teams.name'])

        if birth_date_missing or team_name_missing:
            # FIX 1: Use full name for better search results
            first_name = row.get('firstName', '')
            last_name = row.get('lastName', '')
            full_name = f"{first_name} {last_name}".strip()
            
            if not full_name:
                continue # Skip if we don't even have a name to search for

            data = get_player_data_from_transfermarkt(full_name)
            
            # FIX 2 & 4: Intelligently fill only the missing data
            if data.get("search_url"):
                # If ambiguous, put the URL in both columns for the user to resolve
                if birth_date_missing:
                    players_df.at[index, 'tm_birthDate'] = data["search_url"]
                if team_name_missing:
                    players_df.at[index, 'tm_club'] = data["search_url"]
            else:
                if birth_date_missing and data.get("birth_date"):
                    players_df.at[index, 'tm_birthDate'] = data["birth_date"]
                if team_name_missing and data.get("club"):
                    players_df.at[index, 'tm_club'] = data["club"]
            
            time.sleep(1) 

    players_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✅ Enrichment process complete. New file saved to: {OUTPUT_FILE}")
    print("Please open the new CSV file to manually verify rows containing a URL.")


if __name__ == "__main__":
    enrich_player_data()