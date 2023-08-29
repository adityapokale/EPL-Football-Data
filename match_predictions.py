import pandas as pd
matches = pd.read_csv("matches.csv", index_col=0 )

#   print(matches.head())
print(matches.shape)

# part 1 : Cleaning the data for machine learning

#   print(matches.dtypes)
# ML models cannot work with data that is an object type
# Needs to be in int64 or float64 type

matches["date"] = pd.to_datetime(matches["date"])
# date converted to datetime format
# print(matches.dtypes)

# Part 2 : Creating predictors for machine learning

# First one is home and away games

matches["venue_code"] = matches["venue"].astype("category").cat.codes
# converts data in venue to a categorical data type 
# .cat.codes converts to integers
# This is converting the venue data from string to categories, and categories to integers

# print(matches)
# venue_code is 1 for Home, 1 for Away matches 

# make opp_code category for opponent
matches["opp_code"] = matches["opponent"].astype("category").cat.codes

# do teams play better at certain hours?
# creates column of the hour of the match
matches["hour"] = matches["time"].str.replace(":.+", "", regex=True).astype("int")

# better on certain days of the week?
matches["day_code"] = matches["date"].dt.dayofweek

matches["target"] = (matches["result"] == "W")
# converts target column from boolean to int
matches["target"] = matches["target"].astype("int")

