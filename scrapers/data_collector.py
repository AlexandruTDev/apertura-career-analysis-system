import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

options = webdriver.ChromeOptions()
options.set_capability(
    "goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"}
)

# Make sure you already have Chrome installed
#driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
#driver.set_page_load_timeout(10)

# --- Setup Selenium Webdriver ---
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"})
    
driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 10)

try:
    driver.get("https://www.sofascore.com/inter-miami-cf-new-york-red-bulls/gabsccKc#id:11911622,tab:statistics")
except:
    pass


driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
# extract requests from logs
logs_raw = driver.get_log("performance")
logs = [json.loads(lr["message"])["message"] for lr in logs_raw]
#print(f"  Logs: {logs_raw}")

for x in logs:
    s = x['params'].get('headers', {}).get(':path', '')
    print(s)
    if 'shotmap' in x['params'].get('headers', {}).get(':path', ''):
        print(f" if condition called")
        print(x['params'].get('headers', {}).get(':path'))
        break

test = json.loads(driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': x["params"]["requestId"]})['body'])['shotmap']
test[0]