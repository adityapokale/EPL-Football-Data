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

# Part 4: Cleaning and Merging scraped data with Pandas 
shooting.columns = shooting.columns.droplevel()
# print(shooting.head())

# We have two dataframes now: matches and shooting.
# Now combine them as they are data for the same matches

team_data = matches[0].merge(shooting[["Date", "Sh", "SoT", "Dist", "FK", "PK", "PKatt"]], on="Date")


# Part 5: Scraping data for multiple seasons and teams with loops
# we have scraped and cleaned the data of one team so far

years = list(range(2022,2020,-1))      # two seasons

all_matches = []
standings_url = "https://fbref.com/en/comps/9/2021-2022/2021-2022-Premier-League-Stats"
# ^ might need to update links for previous years

import time
for year in years:
    data = requests.get(standings_url)
    soup = BeautifulSoup(data.text)
    standings_table = soup.select('table.stats_table')[0]

    links = [l.get("href") for l in standings_table.find_all('a')]
    links = [l for l in links if '/squads/' in l]
    team_urls = [f"https://fbref.com{l}" for l in links]


    # right-click on previous season link on fbref and inspect to see which tag
    # this is a.prev    then get the href link
    previous_season = soup.select("a.prev")[0].get("href")
    standings_url = f"https://fbref.com/{previous_season}"


    for team_url in team_urls:
        team_name = team_url.split("/")[-1].replace("-Stats","").replace("-"," ")

        data = requests.get(team_url)
        matches = pd.read_html(data.text, match="Scores & Fixtures")[0]

        soup = BeautifulSoup(data.text)
        links = [l.get("href") for l in soup.find_all('a')]
        links = [l for l in links if l and 'all_comps/shooting/' in l]
        data = requests.get(f"https://fbref.com{links[0]}")
        shooting = pd.read_html(data.text, match="Shooting")[0]
        shooting.columns = shooting.columns.droplevel()

        try:
            team_data = matches.merge(shooting[["Date", "Sh", "SoT", "Dist", "FK", "PK", "PKatt"]])
        
        except ValueError:
            continue
        
        #sort for only Premier League matches
        team_data = team_data[team_data["Comp"] == "Premier League"]
        team_data["Season"] = year
        team_data["Team"] = team_name   # team data table has data for all seasons
        all_matches.append(team_data)

        time.sleep(1)       # to get around websites not allowing quick scraping


# Part 6: Final match results Dataframe 
match_df = pd.concat(all_matches)                           # concatenate all matches
match_df.columns = [c.lower() for c in match_df.columns]    # change column names to lowercase
match_df.to_csv("matches.csv")                              # write to CSV file for further analysis

# print(match_df.shape)
# shape shows the rows, cols of pandas dataframe

