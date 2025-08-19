# sofascore_scraper.py (with click simulation)
import time
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def scrape_sofascore_event_ids(fixtures_path: str, output_path: str):
    """
    Scrapes Sofascore event IDs by simulating user clicks to select matchdays.
    """
    # --- Setup Selenium Webdriver ---
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 15)
    print("[INFO] WebDriver initialized successfully.")

    # --- Load Fixtures ---
    try:
        fixtures_df = pd.read_csv(fixtures_path)
    except FileNotFoundError:
        print(f"❌ ERROR: Fixtures file not found at {fixtures_path}")
        driver.quit()
        return

    all_match_data = []
    processed_event_ids = set()
    base_url = "https://www.sofascore.ro/en-us/tournament/soccer/romania/superliga/152#id:62837,tab:matches"
    
    print(f"  [INFO] Navigating to base URL: {base_url}")
    driver.get(base_url)
    time.sleep(5) # Allow initial page load

    # Group fixtures by matchday to process them efficiently
    for matchday, group in fixtures_df.groupby('matchday'):
        print(f"\n--- Processing Matchday {matchday} ---")
        
        try:
            # --- THE FIX IS HERE: Simulate Clicks ---
            # 1. Find and click the main dropdown button to open the list
            dropdown_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.jQruaf")))
            dropdown_button.click()
            print("  [INFO] Clicked the matchday dropdown.")

            # 2. Find the specific round in the list and click it
            round_selector = f"//li[text()='Round {matchday}']"
            round_option = wait.until(EC.element_to_be_clickable((By.XPATH, round_selector)))
            round_option.click()
            print(f"  [INFO] Selected 'Round {matchday}'.")

            # 3. Wait for the content to refresh
            time.sleep(3)

            # 4. Scrape the newly loaded data
            match_links = driver.find_elements(By.CSS_SELECTOR, "a[data-id]")
            print(f"  [DEBUG] Found {len(match_links)} match links for Matchday {matchday}.")
            
            for link in match_links:
                event_id = link.get_attribute('data-id')
                if event_id in processed_event_ids:
                    continue

                teams = link.find_elements(By.TAG_NAME, "bdi")
                if len(teams) >= 2:
                    team_names = [team.text for team in teams if team.text]
                    for _, fixture_row in group.iterrows():
                        club_name = fixture_row['clubName']
                        if any(club_name in name for name in team_names):
                            print(f"  [SUCCESS] Matched '{club_name}' -> Event ID: {event_id}")
                            all_match_data.append({
                                "clubName": club_name,
                                "matchday": matchday,
                                "eventId": event_id
                            })
                            processed_event_ids.add(event_id)
                            break
                            
        except Exception as e:
            print(f"  [ERROR] An error occurred while processing Matchday {matchday}: {e}")

    # --- Cleanup and Save ---
    driver.quit()

    if all_match_data:
        df = pd.DataFrame(all_match_data).drop_duplicates()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"\n✅ Found {len(df)} event IDs. Data saved to: {output_path}")
    else:
        print("\n❌ No event IDs were found.")

if __name__ == "__main__":
    scrape_sofascore_event_ids(
        fixtures_path="./data/processed/club_fixtures.csv",
        output_path="./data/processed/sofascore_event_ids.csv"
    )