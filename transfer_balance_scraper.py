# transfer_balance_scraper.py (v3 - Final)

import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_transfer_balance(url: str):
    """
    Scrapes a Transfermarkt league transfer page to get the final transfer balance for each club,
    using precise selectors based on the page's HTML structure.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print(f"--- Scraping data from: {url} ---")
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all the main container boxes
        club_boxes = soup.find_all('div', class_='box')
        
        transfer_data = []
        
        for box in club_boxes:
            # --- THE FIX IS HERE ---
            # 1. Target the specific h2 and span elements you identified.
            club_name_tag = box.select_one('h2.content-box-headline--inverted a')
            # The comma acts as an 'OR' selector for either red or green text
            balance_tag = box.select_one('div.table-footer span.redtext, div.table-footer span.greentext')

            # 2. Only proceed if BOTH elements are found (this filters out the video box)
            if club_name_tag and balance_tag:
                club_name = club_name_tag.get('title', '').strip()
                balance = balance_tag.text.strip()
                
                print(f"Found: {club_name} | Balance: {balance}")
                
                transfer_data.append({
                    "club_name": club_name,
                    "transfer_balance": balance
                })

        if not transfer_data:
            print("\n❌ No transfer data found. The page structure may have changed.")
            return None

        df = pd.DataFrame(transfer_data)
        print("\n--- Transfer Balance Summary ---")
        print(df)
        
        return df

    except requests.exceptions.RequestException as e:
        print(f"❌ An error occurred during the request: {e}")
        return None

# --- HOW TO USE ---
if __name__ == "__main__":
    target_url = "https://www.transfermarkt.com/superliga/transfers/wettbewerb/RO1"
    scrape_transfer_balance(target_url)