import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def scrape_ipl_matches(season_url, season_name):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get(season_url)
        time.sleep(5)  # Wait for JavaScript to load the content
        matches = []
        
        match_elements = driver.find_elements(By.CSS_SELECTOR, 'div.cb-col-100.cb-col')
        
        for match in match_elements:
            try:
                teams = match.find_element(By.CSS_SELECTOR, 'a.text-hvr-underline').text.strip()
            except:
                teams = "N/A"
            
            try:
                date = match.find_element(By.CSS_SELECTOR, 'span.ng-binding').text.strip()
            except:
                date = "N/A"
                
            try:
                stadium = match.find_element(By.CSS_SELECTOR, 'div.text-gray').text.strip()
            except:
                stadium = "N/A"
            
            try:
                match_time = match.find_element(By.CSS_SELECTOR, 'span.schedule-date').text.strip()
            except:
                match_time = "N/A"
                
            matches.append([season_name, teams, date, stadium, match_time])
        
        return matches
    except Exception as e:
        print(f"Error fetching {season_name}: {e}")
        return []
    finally:
        driver.quit()

# IPL seasons and URLs
seasons = {
    'IPL 2008': 'https://www.cricbuzz.com/cricket-series/2058/indian-premier-league-2008/matches',
    'IPL 2009': 'https://www.cricbuzz.com/cricket-series/2059/indian-premier-league-2009/matches',
    'IPL 2010': 'https://www.cricbuzz.com/cricket-series/2060/indian-premier-league-2010/matches',
    'IPL 2011': 'https://www.cricbuzz.com/cricket-series/2037/indian-premier-league-2011/matches',
    'IPL 2012': 'https://www.cricbuzz.com/cricket-series/2115/indian-premier-league-2012/matches',
    'IPL 2013': 'https://www.cricbuzz.com/cricket-series/2170/indian-premier-league-2013/matches',
    'IPL 2014': 'https://www.cricbuzz.com/cricket-series/2261/indian-premier-league-2014/matches',
    'IPL 2015': 'https://www.cricbuzz.com/cricket-series/2330/indian-premier-league-2015/matches',
    'IPL 2016': 'https://www.cricbuzz.com/cricket-series/2430/indian-premier-league-2016/matches',
    'IPL 2017': 'https://www.cricbuzz.com/cricket-series/2568/indian-premier-league-2017/matches',
    'IPL 2018': 'https://www.cricbuzz.com/cricket-series/2676/indian-premier-league-2018/matches',
    'IPL 2019': 'https://www.cricbuzz.com/cricket-series/2810/indian-premier-league-2019/matches',
    'IPL 2020': 'https://www.cricbuzz.com/cricket-series/3130/indian-premier-league-2020/matches',
    'IPL 2021': 'https://www.cricbuzz.com/cricket-series/3472/indian-premier-league-2021/matches',
    'IPL 2022': 'https://www.cricbuzz.com/cricket-series/4061/indian-premier-league-2022/matches',
    'IPL 2023': 'https://www.cricbuzz.com/cricket-series/5945/indian-premier-league-2023/matches',
    'IPL 2024': 'https://www.cricbuzz.com/cricket-series/7607/indian-premier-league-2024/matches',
}

all_matches = []
for season, url in seasons.items():
    all_matches.extend(scrape_ipl_matches(url, season))

# Save to CSV
with open('ipl_matches3.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Season', 'Teams', 'Date', 'Stadium', 'Time'])
    writer.writerows(all_matches)

print("✅ Data saved to ipl_matches3.csv")
