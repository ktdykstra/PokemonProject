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

def cookie_collecter(driver):
    driver.get('https://play.pokemonshowdown.com')
    input("Hit enter when done") # can't delete if want popup to stay open @katie: delete this when ready to incorporate. just using for testing
    return driver
x=4
str(x)+"%"
username = "DaFinisher"
gametype = "gen9vgc2023regulationd"
driver = webdriver.Chrome()
driver=cookie_collecter(driver)

df1, df2, df_individual_hero, df_indiv_villain, df3, df4, df5, df6 = sdg.get_metrics(username, gametype, driver, True)
df2
pd.set_option('display.max_rows', 500)
df1.hero_comp_fused.max()
specified_comp='Flutter ManeGholdengoMaushold-FourScream TailTalonflameUrshifu-*'
# df1.iloc[0].hero_comp_fused
library=df1.loc[df1["hero_comp_fused"]==specified_comp,["hero_comp_fused","match_id","hero_comp_six","win","match_scorecards"]]
## display only matches for one specific comp. So comp matches -> library
library
result=library[["match_id","hero_comp_six","win","match_scorecards"]].explode("hero_comp_six")
result["used_total"]=0
holder=pd.DataFrame()
for x in library.match_scorecards:
    holder=pd.concat([holder,x.loc["hero_pokemon","begins_field"]])
holder.columns=["began"]
holder["used"]=holder.began.apply(lambda x: 0 if x==0 else 1)
result["used_total"]=holder["used"].values
result["win_conditional"]=result.apply(check_conditional_win,axis=1)
result.rename(columns={"hero_comp_six":"hero_pokemon","match_id":"total_games"},inplace=True)
result=result.groupby("hero_pokemon").agg({"total_games":"count","used_total":"sum","win_conditional":"sum"})
result["win_rate"]=result.win_conditional/result.used_total*100
result.win_rate.fillna(0,inplace=True)
result.win_rate=result.win_rate.apply(format_percent)
result["elo_score"]=get_elo(ELO_SCALE, ELO_BENCH, result.win_conditional, result.used_total).apply(format_percent)
result
# return result.sort_values(by="elo_score", ascending=True)
df1.columns

def check_conditional_loss(row):
    if (row.used_total==1 and row.loss==1):
        return 1
    else:
        return 0   
def check_conditional_win(row):
    if (row.used_total==1 and row.win==1):
        return 1
    else:
        return 0    

def format_percent(line):
    
    line="%.1f" % line
    
    return line

def get_elo(elo_scale, elo_benchmark, win_series, total_match_series):
    elo_score = (win_series + elo_scale * elo_benchmark)/(total_match_series + elo_scale)*100
    return elo_score

ELO_SCALE=5
ELO_BENCH=0.5

## try to get compspecific
df1.columns
hero_comp=df1.hero_comp_fused.max()
villain_comp="DragoniteOrthwormRabscaUrsaluna" # this only has four comp
sdg.get_individual_plot(sdg.get_individual_rates(sdg.get_hero_comp_library(hero_comp,df1))).show()
sdg.get_villain_indiv_plot(sdg.get_villain_indiv_rates(sdg.get_villain_comp_library(villain_comp,df1))).show()
sdg.get_meta_losses(sdg.get_villain_comp_library(villain_comp,df1))

result=result.explode("hero_comp_six")
result


result.iloc[0]
result["used_total"]=0
result.columns
# result.head().iloc[:,1:]
holder=pd.DataFrame()
result.shape[0]
for x in result.match_scorecards:
    holder=pd.concat([holder,x.loc["hero_pokemon","begins_field"]])
holder.columns=["began"]
holder["used"]=holder.began.apply(lambda x: 0 if x==0 else 1)
result["used_total"]=holder["used"].values
result["win_conditional"]=result.apply(check_conditional_win,axis=1)
result.rename(columns={"hero_comp_six":"hero_pokemon","match_id":"total_games"},inplace=True)
result=result.groupby("hero_pokemon").agg({"total_games":"count","used_total":"sum","win_conditional":"sum"})
result["win_rate"]=result.win_conditional/result.used_total*100
result.win_rate.fillna(0,inplace=True)
result.win_rate=result.win_rate.apply(format_percent)
result["elo_score"]=get_elo(ELO_SCALE, ELO_BENCH, result.win_conditional, result.used_total).apply(format_percent)
# return result.sort_values(by="elo_score", ascending=True)


driver.quit()

df5.explode("hero_comp_six")
df5.iloc[0]
for i in range(df5.shape[0]):
    print(len(df5.iloc[i].hero_comp_six))
df5["comp_size"]=df5.hero_comp_six.apply(lambda x: len(x))
df5["test_5"]=np.nan
df5["test_6"]=np.nan
for i in range(df5.shape[0]):
    # check the size of comp
    print(df5.iloc[i].comp_size)
    print(df5.iloc[i].hero_comp_six[4])
    if df5.iloc[i].comp_size==5:
        df5.loc[i,"test_5"]=df5.iloc[i].hero_comp_six[4]
    if df5.iloc[i].comp_size==6:
        df5.loc[i,"test_5"]=df5.iloc[i].hero_comp_six[4]
        df5.loc[i,"test_6"]=df5.iloc[i].hero_comp_six[5]
stored_hero=df5.copy()
stored_villain=df6.copy()
stored_villain
df6.iloc[8]
df5["test_5"]= np.nan
df5["test_5"]= df5.apply(lambda x: x==np.nan if df5["comp_size"]<5 else x==df5.hero_comp_six[4])

df5.apply(lambda x: None if x.comp_size<5 else x.hero_comp_six[4])
df5["test_5"]= df5.apply(lambda x: x.test_5==1)

df5
df5["test_6"]=df5.apply(lambda x: None if x.comp_size<6 else x.hero_comp_six[5])
df6.iloc[8]

df6.columns
len(df1.iloc[0].hero_comp_six)

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