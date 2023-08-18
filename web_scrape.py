import requests
# Part 1: parsing HTML links with Beautiful Soup 
standings_url = "https://fbref.com/en/comps/9/2021-2022/2021-2022-Premier-League-Stats"

data = requests.get(standings_url)
data.text

from bs4 import BeautifulSoup
soup = BeautifulSoup(data.text)

# In browser, Inspect the fbref data page and find the HTML element for the standings table 
# which is <table class=" stats_table ...">  
# select stats_table below
standings_table = soup.select('table.stats_table')[0]

# find all "a" tags in the table as these have the link to each team's stats
links = standings_table.find_all('a')

# then need to get href property of each link
links = [l.get("href") for l in links]
links = [l for l in links if '/squads/' in l]

# add fbref url to links
team_urls = [f"https://fbref.com{l}" for l in links]

# Part 2: Extract match stats using pandas and requests

#looking at first team
team_url = team_urls[0]
data = requests.get(team_url)

import pandas as pd
matches = pd.read_html(data.text, match="Scores & Fixtures") 
# ^ got string from from HTML inspect

# Part 3: Get match shooting stats with requests and pandas
soup = BeautifulSoup(data.text)
links = soup.find_all('a')
links = [l.get("href") for l in links]
links = [l for l in links if l and 'all_comps/shooting/' in l]

data = requests.get(f"https://fbref.com{links[0]}")
shooting = pd.read_html(data.text, match="Shooting")[0]
print(shooting.head())