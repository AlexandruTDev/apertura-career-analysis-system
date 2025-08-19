# fixture_scraper.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

TEAM_URL_MAPPING = {
    "Dinamo Bucuresti": {"name": "fc-dinamo-1948", "id": "312"},
    "FCS Bucuresti": {"name": "fcsb", "id": "301"},
    "Rapid Bucuresti": {"name": "fc-rapid-1923", "id": "455"},
    "Otelul": {"name": "sc-otelul-galati", "id": "4959"},
    "CFR Cluj": {"name": "cfr-cluj", "id": "7769"},
    "Botosani": {"name": "fc-botosani", "id": "8818"},
    "Unirea Slobozia": {"name": "afc-unirea-04-slobozia", "id": "29700"},
    "Universitatea Craiova": {"name": "cs-universitatea-craiova", "id": "40812"},
    "UTA Arad": {"name": "uta-arad", "id": "952"},
    "Hermannstadt": {"name": "fc-hermannstadt", "id": "58049"},
    "Universitatea Cluj": {"name": "fc-universitatea-cluj", "id": "6429"},
    "Petrolul 52": {"name": "petrolul-ploiesti", "id": "9465"},
    "Farul Constanta": {"name": "fcv-farul-constanta", "id": "29831"}
}

def scrape_fixtures(formations_path: str, output_path: str, season_id="2024"):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    base_url = "https://www.transfermarkt.com/{name}/spielplan/verein/{id}/saison_id/{season}"
    
    try:
        formations_df = pd.read_csv(formations_path)
        primary_formations = pd.Series(
            formations_df['formation.primary'].values,
            index=formations_df['team.name']
        ).to_dict()
    except FileNotFoundError:
        print(f"❌ ERROR: Formations file not found at {formations_path}")
        return

    all_fixtures = []

    for club_name, url_data in TEAM_URL_MAPPING.items():
        primary_formation_from_file = str(primary_formations.get(club_name))
        if not primary_formation_from_file:
            continue

        url = base_url.format(name=url_data['name'], id=url_data['id'], season=season_id)
        print(f"\n--- Scraping fixtures for: {club_name} ---")
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # --- THE FIX IS HERE ---
            # 1. Find the anchor tag for the SuperLiga (name="RO1")
            # 2. Find its parent <div class="box"> which contains the correct table
            league_anchor = soup.find('a', {'name': 'RO1'})
            if not league_anchor:
                print(f"  [WARN] Could not find the SuperLiga table anchor for {club_name}.")
                continue
            
            # Find the specific parent box for the league fixtures
            fixture_box = league_anchor.find_parent('div', class_='box')
            if not fixture_box:
                print(f"  [WARN] Could not find the parent 'box' for the fixture table.")
                continue

            table_body = fixture_box.select_one('.responsive-table tbody')

            if not table_body:
                print(f"  [WARN] Found the correct box, but no tbody inside for {club_name}.")
                continue
            
            matchday_count = 0
            for row in table_body.find_all('tr'):
                if matchday_count >= 13:
                    break

                columns = row.find_all('td')
                # A valid match row has exactly 11 columns
                if len(columns) == 10:
                    matchday = columns[0].text.strip()
                    venue = columns[3].text.strip()
                    
                    # Formation is in the 9th column (index 8)
                    formation_scraped = columns[7].text.strip().split(' ')[0]

                    if formation_scraped == primary_formation_from_file:
                        print(f"  [SUCCESS] Matchday {matchday}: Found primary formation ({formation_scraped})")
                        all_fixtures.append({
                            "clubName": club_name,
                            "matchday": matchday,
                            "venue": venue
                        })
                        matchday_count += 1

        except requests.exceptions.RequestException as e:
            print(f"  [ERROR] Could not fetch page for {club_name}: {e}")
            continue

    if all_fixtures:
        df = pd.DataFrame(all_fixtures)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"\n✅ Found {len(df)} relevant fixtures. Data saved to: {output_path}")
    else:
        print("\n❌ No relevant fixtures were found.")

if __name__ == "__main__":
    scrape_fixtures(
        formations_path="./data/raw/superliga_formations_24_25.csv",
        output_path="./data/processed/club_fixtures.csv"
    )