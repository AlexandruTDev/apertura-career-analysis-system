# crest_scraper.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

def scrape_club_crests(url: str, output_path: str):
    """
    Scrapes the Superliga website to get the name and crest URL for each club,
    with detailed logging for verification.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    print(f"--- Scraping club crests from: {url} ---")

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        crest_data = []
        base_url = "https://www.superliga.ro"

        crest_links = soup.select('div.flex.justify-between.bg-white a')

        print("\n--- [LOG] Starting to process found crests ---")
        for i, link in enumerate(crest_links):
            img_tag = link.find('img')
            if img_tag:
                # --- THE NEW LOGGING IS HERE ---
                print(f"\n[LOG] Processing item #{i+1}...")

                # 1. Get the raw data
                relative_url = img_tag['src']
                full_url = base_url + relative_url
                alt_text = img_tag.get('alt', 'NO ALT TEXT')

                print(f"  - Raw Alt Text: '{alt_text}'")

                # 2. Clean the name
                # This logic is designed to extract a clean name like "Fcsb"
                clean_name = alt_text.replace('Superliga Romania (Liga 1) - emblema ', '').replace('-', ' ').title()

                print(f"  - Cleaned Name: '{clean_name}'")
                print(f"  - Associated URL: '{full_url}'")

                crest_data.append({
                    "club_name_official": clean_name,
                    "crest_url": full_url
                })

        # Save the data to a CSV file
        df = pd.DataFrame(crest_data)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"\n✅ Club crest data saved successfully to: {output_path}")

        return df

    except requests.exceptions.RequestException as e:
        print(f"❌ An error occurred during the request: {e}")
        return None

if __name__ == "__main__":
    scrape_club_crests(
        url="https://www.superliga.ro/",
        output_path="./data/processed/club_crests.csv"
    )