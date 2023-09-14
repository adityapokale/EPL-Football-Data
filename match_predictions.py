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
# convert target column from boolean to int
# now True == 1, False == 0
matches["target"] = matches["target"].astype("int")

# Part 3: Creating our initial Machine Learning Model

from sklearn.ensemble import RandomForestClassifier

# RandomForestClassifier can pick up non-linearities in the data
# because oppinent code does not signify difficulty of opponent, just an identifier
# Random Forest is a series of decision trees
# n_estimators is the no. of individual decision trees we want to train. 
# Higher number = longer runtime, but more accurate
rf = RandomForestClassifier(n_estimators = 50, min_samples_split=10, random_state = 1 )

# put matches from before 2022 in our training set. Cannot use future results to predict past
train = matches[matches["date"] < '2022-01-01']

# test set will be matches in 2022
test = matches[matches["date"] > '2022-01-01']

predictors = ["venue_code", "opp_code", "hour", "day_code"]

# fit our randomforest model
rf.fit(train[predictors], train["target"])  

preds = rf.predict(test[predictors])

# Next, we need to determine how we determine the accuracy of the model
# This is an IMPORTANT choice. We're gonna try a few different metrics and see which one makes more sense.

# accuracy_score tells you what percent of the time was your prediction accurate
from sklearn.metrics import accuracy_score

acc = accuracy_score(test["target"], preds)
# check accuracy 
print("Accuracy with accuracy_score is: ", acc)
# accuracy was 60.6%
# Let's dig a little deeper into this and see in which situations our acc was high vs low

# create dataframe combining actual values and predicted values
combined =  pd.DataFrame(dict(actual=test["target"], prediction = preds))
# print(combined)

# create a cross tab using Pandas, Two-way table showing us what we predicted vs what happenedd
combined_cross = pd.crosstab(index = combined["actual"], columns=combined["prediction"])
print(combined_cross)

# not great at predicting wins
# try different metric
from sklearn.metrics import precision_score
prec = precision_score(test["target"], preds)
print("Accuracy with precision_score is: ", prec)
# 51%, not great precision. We can improve this model.


# Part 4: Improving precision with rolling averages
#   Create more predictors to improve accuracy

grouped_matches = matches.groupby("team")
# create one dataframe for every team
group = grouped_matches.get_group("Liverpool")
# print(group) 

# Use previous 3 matches W/L to predict result of match 4

def rolling_averages(group, cols, new_cols):
    group = group.sort_values("date")
    rolling_stats = group[cols].rolling(3, closed='left').mean()
    # closed = 'left' to prevent using future data for past preds
    group[new_cols] = rolling_stats
    group = group.dropna(subset=new_cols)
    return group

cols = ["gf", "ga", "sh", "sot", "dist", "fk", "pk", "pkatt"]
new_cols = [f"{c}_rolling" for c in cols]       # new columns with rolling averages of these stats
# print(rolling_averages(group, cols, new_cols))

# Next, apply this to all matches
# We took our matches dataFrame and grouped by team, creating a dataFrame for each team
# then apply function to calculate rolling averages for each team dataframe
matches_rolling = matches.groupby("team").apply(lambda x: rolling_averages(x, cols, new_cols))
# print(matches_rolling)
matches_rolling = matches_rolling.droplevel('team') 
# print(matches_rolling)
# don't need this so drop it to make working with dataframe easier
# Values in index are being repeated. We want unique values, so eliminate:
matches_rolling.index = range(matches_rolling.shape[0])

# Part 5: Retraining our Machine Learning model
# print(predictors+new_cols)

def make_predictions(data, predictors):

    train = data[data["date"] < '2022-01-01']
    test = data[data["date"] > '2022-01-01']

    rf.fit(train[predictors], train["target"])
    preds = rf.predict(test[predictors])
    combined = pd.DataFrame(dict(actual=test["target"], predicted=preds), index=test.index)
    precision = precision_score(test["target"], preds)
    return combined, precision

combined, precision = make_predictions(matches_rolling, predictors + new_cols)
print("Accuracy with rolling data is: ", precision) 
combined = combined.merge(matches_rolling[["date", "team", "opponent", "result"]], left_index=True, right_index=True)

# Combining home and away predictions
# taking into account both team A and team B predictions

# Team name discrepancy. For e.g. Wolverhampton Wanderers and Wolves
class MissingDict(dict):
    __missing__ = lambda self, key : key

map_values = {
    "Brighton and Hove Albion":"Brighton", "Manchester United": "Manchester Utd",
    "Newcastle United":"Newcastle Utd", "Tottenham Hotspur":"Tottenham",
    "West Ham United":"West Ham", "Wolverhampton Wanderers":"wolves"}

mapping = MissingDict(**map_values)
combined["new_team"] = combined["team"].map(mapping)
merged = combined.merge(combined, left_on=["date","new_team"], right_on=["date", "opponent"])
# print(merged)

# comparing prediction vs actual

compare = merged[(merged["predicted_x"]==1) & (merged["predicted_y"]==0)]["actual_x"].value_counts()
print(compare)
home_away_acc = (compare[1])/(compare[0]+compare[1]) 
print("Accuracy after combining home & away fixtures: ", home_away_acc) 