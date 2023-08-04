import pandas as pd
import numpy as np
import importlib

# Reload the module before importing
importlib.reload(sdg)
import poke_backend_v2 as sdg
import plotly.express as px
import plotly.graph_objects as go
import plotly.offline as pyo
import plotly.io as pio
pio.renderers.default='browser'
from selenium import webdriver
import requests
from requests.adapters import BaseAdapter
from requests.sessions import Session
import json


match_page=1
api_url = "https://replay.pokemonshowdown.com/search.json?user=" + username + "&format=" + gametype + "&page=" + str(match_page)
print(api_url)

## collect cookies
def cookie_collecter(driver):
    driver.get('https://play.pokemonshowdown.com')
    input("Hit enter when done") # can't delete if want popup to stay open @katie: delete this when ready to incorporate. just using for testing
    return driver
driver.get(api_url)

driver = webdriver.Chrome()
driver=cookie_collecter(driver)
username = "DaFinisher"
gametype = "gen9vgc2023regulationd"

df1, df2, df_individual_hero, df_indiv_villain, df3, df4, df5, df6 = sdg.get_metrics(username, gametype, driver, True)


lib=sdg.gather_matches(username,gametype,driver, True)
match_db=sdg.get_all_data(lib)
match_db.iloc[6].match_id

temp=sdg.get_individual_plot(df_individual_hero)
temp.show()
driver.quit()



pd.set_option('display.max_columns', None)
lib[["hero","p1"]]
lib.iloc[1].turn_logs.iloc[0].turn_df
base_url="https://replay.pokemonshowdown.com"
match_url=base_url + "/" + lib.iloc[3].id + "pw"+".json"
driver.get(match_url)
json_element = driver.find_element(by="tag name", value='pre')
json_element
json_text=json_element.text
json_file=json.loads(json_text)
json_file["log"]

for i in range(lib.shape[0]):
    print(i)

lib.iloc[5].id
lib.iloc[5]
driver.quit()

json_element = driver.find_element(by="tag name", value='pre')
json_element
json_text=json_element.text
json_file=json.loads(json_text)
json_file[0]
pd.read_json(json_text)#.iloc[1:,]