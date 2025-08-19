# scrapers/player_position_scraper.py (Final Version)
import requests
import pandas as pd
import os
import time
from tqdm import tqdm
import re

def extract_event_id(url):
    """Extracts the event ID from a Sofascore URL."""
    if not isinstance(url, str): return None
    match = re.search(r'#id:(\d+)', url)
    return match.group(1) if match else None

def scrape_player_positions(fixtures_path: str, matches_lookup_path: str, output_path: str):
    """
    Uses a lookup file and meticulously crafted headers (based on community findings)
    to fetch player positional data directly from the Sofascore API.
    """
    # --- THE FIX IS HERE: Headers that mimic a legitimate browser request ---
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "max-age=0",
        "priority": "u=1, i",
        "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site", # This was the critical missing piece
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    }

    try:
        fixtures_df = pd.read_csv(fixtures_path)
        matches_df = pd.read_csv(matches_lookup_path)
    except FileNotFoundError as e:
        print(f"❌ ERROR: Could not find a required file: {e}")
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
        event_id = extract_event_id(event_url)
        if not event_id: continue
        
        try:
            # We now add a referer for each specific call
            headers['referer'] = f'https://www.sofascore.com/event/{event_id}'
            
            lineups_url = f"https://api.sofascore.com/api/v1/event/{event_id}/lineups"
            lineups_response = requests.get(lineups_url, headers=headers)
            lineups_response.raise_for_status()
            lineups_data = lineups_response.json()

            incidents_url = f"https://api.sofascore.com/api/v1/event/{event_id}/incidents"
            incidents_response = requests.get(incidents_url, headers=headers)
            incidents_response.raise_for_status()
            incidents_data = incidents_response.json()

            lineup_incident = next((inc for inc in incidents_data.get('incidents', []) if inc.get('incidentType') == 'lineup'), None)

            if not lineup_incident:
                print(f"[WARN] No 'lineup' incident found for event ID {event_id}. Skipping.")
                continue

            position_map = {}
            for team_key in ['home', 'away']:
                for player_pos_data in lineup_incident.get(team_key, []):
                    player_id = player_pos_data.get('player', {}).get('id')
                    if player_id:
                        position_map[player_id] = {'row': player_pos_data.get('row'), 'column': player_pos_data.get('column')}

            for team_key in ['home', 'away']:
                for player_data in lineups_data.get(team_key, {}).get('players', []):
                    player_info = player_data.get('player', {})
                    player_id = player_info.get('id')
                    if player_id in position_map:
                        all_player_positions.append({
                            'eventId': event_id, 'playerId': player_id, 'playerName': player_info.get('name'),
                            'position': player_data.get('position'), 'formation_row': position_map[player_id]['row'],
                            'formation_col': position_map[player_id]['column']
                        })
            time.sleep(1)

        except Exception as e:
            print(f"  [ERROR] Failed to process event ID {event_id}: {e}")

    if all_player_positions:
        df = pd.DataFrame(all_player_positions)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"\n✅ Successfully processed {len(df['eventId'].unique())} unique matches.")
        print(f"Final data saved to: {output_path}")
    else:
        print("\n❌ No player position data was generated.")

if __name__ == "__main__":
    scrape_player_positions(
        fixtures_path="./data/processed/club_fixtures.csv",
        matches_lookup_path="./data/manual/sofascore_matches.csv",
        output_path="./data/processed/player_positions_by_match.csv"
    )