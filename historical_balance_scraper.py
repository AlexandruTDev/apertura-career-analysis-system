# historical_balance_scraper.py

import requests
from bs4 import BeautifulSoup
import pandas as pd
from collections import defaultdict
import os

# Define the output path
OUTPUT_FILE = './data/processed/superliga_transfer_balances.csv'

def scrape_historical_balance(seasons: list):
    # ... (scraper logic is the same as before) ...
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    base_url = "https://www.transfermarkt.com/superliga/einnahmenausgaben/wettbewerb/RO1/plus/0?ids=a&sa=&saison_id={season}&saison_id_bis={season}&nat=&pos=&altersklasse=&w_s=&leihe=&intern=0"
    club_balances = defaultdict(float)
    for season in seasons:
        season_display = f"{season}/{season+1}"
        url = base_url.format(season=season)
        print(f"\n--- Scraping data for {season_display} season ---")
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('div', class_='responsive-table').find('tbody')
            for row in table.find_all('tr', class_=['odd', 'even']):
                club_name_tag = row.select_one('td.hauptlink a')
                balance_tag = row.select_one('td.rechts.hauptlink span')
                if club_name_tag and balance_tag:
                    club_name = club_name_tag.get('title').strip()
                    balance_str = balance_tag.text.strip().replace('€', '')
                    value = 0.0
                    multiplier = 1
                    if 'm' in balance_str:
                        multiplier = 1_000_000
                        balance_str = balance_str.replace('m', '')
                    elif 'k' in balance_str:
                        multiplier = 1_000
                        balance_str = balance_str.replace('k', '')
                    try:
                        value = float(balance_str) * multiplier
                    except ValueError:
                        value = 0.0
                    club_balances[club_name] += value
        except requests.exceptions.RequestException as e:
            print(f"❌ Error scraping season {season}: {e}")
            continue
    
    summary_data = [{"club_name_transfermarkt": name, "two_year_net_spend": f"€{balance/1_000_000:.2f}m"} for name, balance in club_balances.items()]
    df = pd.DataFrame(summary_data)
    
    # --- NEW: Save the output to a CSV file ---
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✅ Transfer balance data saved to: {OUTPUT_FILE}")
    
    return df

if __name__ == "__main__":
    seasons_to_scrape = [2023, 2024]
    scrape_historical_balance(seasons_to_scrape)