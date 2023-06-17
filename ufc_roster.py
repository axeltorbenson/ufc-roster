import pandas as pd
import numpy as np
import requests
import html5lib
from bs4 import BeautifulSoup
from unidecode import unidecode

url = r'https://en.wikipedia.org/wiki/List_of_current_UFC_fighters#Debuted_fighters'
rankings = pd.read_html(url, attrs = {"class":"wikitable"})

# table 0 has half, table 1 has other half
# df.melt(id_vars=['Name', 'Age'], var_name='Subject', value_name='Grades')

# looks ugly, should fix
rankings_full = rankings[0].set_index('Rank').join(rankings[1].set_index('Rank')).reset_index()
pivoted = rankings_full.melt(id_vars = ['Rank'], var_name = "weight_class", value_name = "name")
rankings_pivoted = pivoted.copy()

# 0 indicated champion
rankings_pivoted.Rank = pivoted.Rank.replace('(C)', 0)
rankings_pivoted.name = (
    rankings_pivoted.name
    .str.replace(r' \d', '', regex = True)
    .str.replace(r' \(.+\)', '', regex = True)
    .str.replace(r'\(\d\) ', '', regex = True)
    .str.replace(r'\.', '', regex = True))
clean_rankings = rankings_pivoted.dropna(axis = 0)
# gets rid of p4p rankings
clean_rankings = clean_rankings[~clean_rankings.weight_class.str.contains("pound-for-pound")]
roster = pd.read_html(url, attrs = {"class":"wikitable sortable"}, flavor = 'bs4')

# 3 is heav, 4 is l heav, etc until 14
weights = ["115W","125W", "135W", "145W", "125", "135", "145", "155", "170", "185", "205", "265"]

# reverse order weights, first table is 3rd of its class
for idx, wt in enumerate(weights[::-1]):
    roster[idx + 3]['Weight'] = wt

full_roster = pd.concat([roster[idx + 3] for idx in range(len(weights))])
tidy_roster = full_roster.drop(
    ['ISO', 'Nickname', 'Result / next fight / status', 'Ref'], axis = 1)
tidy_roster.Name = (
    tidy_roster.Name
    .str.replace(r'*', '', regex = False)
    .str.replace(r'\(.+\)', '', regex = True)
    .str.replace(r'\.', '', regex = True)
    )
tidy_roster['height'] = tidy_roster['Ht.'].str.extract(r'.+\((\d\.\d+).+\)')
tidy_roster['height'] = pd.to_numeric(tidy_roster['height'])

ufc_record = (tidy_roster['Endeavor record']
              .str.extract(
                  r'^(?P<ufc_wins>\d+)–(?P<ufc_loses>\d+)(?:–(?P<ufc_draws>\d+))?\s*(?:\((?P<ufc_no_contests>\d+) NC\))?')
              .fillna(0)
              .reset_index(drop = True)
              .apply(pd.to_numeric)
              )
mma_record = (tidy_roster['MMA record']
              .str.extract(
                  r'^(?P<mma_wins>\d+)–(?P<mma_loses>\d+)(?:–(?P<mma_draws>\d+))?\s*(?:\((?P<mma_no_contests>\d+) NC\))?')
              .fillna(0)
              .reset_index(drop = True)
              .apply(pd.to_numeric)
              )


clean_roster = (pd.concat(
    [tidy_roster.reset_index(drop = True), ufc_record, mma_record], axis=1)
    .drop(['Ht.', 'Endeavor record', 'MMA record'], axis = 1)
    .rename(columns = {'Name':'name', 'Age':'age', 'Weight':'weight'}))

# getting rid of accents and stuff, as well as any whitespace
clean_roster.name = clean_roster.name.apply(unidecode).str.strip()
clean_rankings.name = clean_rankings.name.apply(unidecode).str.strip()

# Khalil doesn't have the Jr
clean_rankings.name = clean_rankings.name.replace({'Khalil Rountree':'Khalil Rountree Jr'})

df = pd.merge(clean_roster, clean_rankings, on='name', how='outer')
