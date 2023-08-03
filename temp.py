# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import pandas as pd
import numpy as np
import poke_backend_v2 as sdg
import plotly.express as px
import plotly.graph_objects as go
import plotly.offline as pyo
import plotly.io as pio
pio.renderers.default='browser'
from selenium import webdriver

username = "Broskander"
gametype = "gen9vgc2023series1"


#print(username)
#print(gametype)
df1, df2, df_individual, df3, df4, df5, df6 = sdg.get_metrics(username, gametype)
x=sdg.get_individual_plot(sdg.get_individual_rates(df1))
x.show()
# x=sdg.get_individual_rates(df1)
temp=sdg.get_individual_rates(df1)

library=df1.copy()
library.columns

for i in range(df1.shape[0]):
    print(df1.iloc[i].match_scorecards)
df_individual


## function for checking

def check_conditional_win(row):
    if (row.used_total==1 and row.win==1):
        return 1
    else:
        return 0

## check if played

library.iloc[0].match_scorecards

result=df1[["match_id","hero_comp_six","win","match_scorecards"]].explode("hero_comp_six")
result["used_total"]=0
holder=pd.DataFrame()
holder
for x in df1.match_scorecards:
    holder=pd.concat([holder,x.loc["hero_pokemon","begins_field"]])
holder.columns=["began"]
holder["used"]=holder.began.apply(lambda x: 0 if x==0 else 1)
result["used_total"]=holder["used"].values
result["win_conditional"]=result.apply(check_conditional_win,axis=1)
result.rename(columns={"hero_comp_six":"hero_pokemon","match_id":"total_games"},inplace=True)
result=result.groupby("hero_pokemon").agg({"total_games":"count","used_total":"sum","win_conditional":"sum"})
df1
sdg.get_individual_rates(df1).reset_index().columns
sdg.get_villain_indiv_plot(get_villain_indiv_rates(df1)).show()
sdg.get_villain_indiv_rates(df1).reset_index().columns
result
df1.iloc[0].match_scorecards.columns
for i in range(result.shape[0]):
    target_pokemon=result.
    match_scorecard=result.iloc[i].match_scorecards.reset_index()
    for y in range(match_scorecard.shape[0]):
        match_scorecard.loc

result["win_rate"]=(result.win_conditional/result.used_total)*100
result
result.win_rate.fillna(0,inplace=True)
result
#print(output)

# #df with num_wins, num_games, win_rate
# overallStats = df2.to_html(index=False, classes='table table-responsive table-hover')
# num_games = str(df2.loc[0, 'num_games'])
# num_wins = str(df2.loc[0, 'num_wins'])
# win_rate = str(df2.loc[0, 'win_rate'])

# #dfs with individual pokemon winrates and elo scores
# df_individual = df_individual.reset_index()
# df_individual=df_individual.loc[:,["hero_pokemon","win","total_games","elo_score"]]
# df_individual.columns=['Hero Pokemon', "Games Won", "Games Played", "Weighted Win Rate"]
# # df_individual.to_csv("ind_stats.csv")
# df_individual["Weighted Win Rate"]=df_individual["Weighted Win Rate"].apply(lambda x: x+"%")
# individualStats = df_individual.to_html(index=False)

# #dfs with hero pairs, games and win rates breakdown 
# df3=df3.loc[:,["hero_one","hero_two","num_wins","num_games","elo_rate"]]
# df3.columns = ['Hero Lead 1', 'Hero Lead 2', "Games Won", "Games Played", "Weighted Win Rate"]
# df3.sort_values(by="Weighted Win Rate",ascending=False,inplace=True)
# df3["Weighted Win Rate"]=df3["Weighted Win Rate"].apply(lambda x: x+"%")
# heroStats = df3.to_html(index=False)

# ## villain pair stats
# df4=df4.loc[:,["villain_one","villain_two","num_losses","num_games","elo_rate"]]
# df4.columns = ['Villain Lead 1', 'Villain Lead 2', "Games Lost Against", "Games Played Against", "Weighted Loss Rate"]
# df4.sort_values(by="Weighted Loss Rate",ascending=False,inplace=True)
# df4["Weighted Loss Rate"]=df4["Weighted Loss Rate"].apply(lambda x: x+"%")
# villainStats = df4.to_html(index=False)

# ## hero comp stats
# df5=df5.loc[:,["hero_comp_six","num_wins","num_games","elo_score"]]
# df5.columns = ['Hero Teams', 'Games Won', "Games Played", "Weighted Win Rate"]
# df5.sort_values(by="Weighted Win Rate",ascending=False,inplace=True)
# df5["Weighted Win Rate"]=df5["Weighted Win Rate"].apply(lambda x: x+"%")
# df5
# sixTeamHeroStats = df5.to_html(index=False)

# ## hero comp stats
# df6=df6.loc[:,["villain_comp_six","num_losses","num_games","elo_score"]]
# df6.columns = ["Villain Teams","Games Lost Against", "Games Played Against", "Weighted Loss Rate"]
# df6.sort_values(by="Weighted Loss Rate",ascending=False,inplace=True)
# df6["Weighted Loss Rate"]=df6["Weighted Loss Rate"].apply(lambda x: x+"%")
# sixTeamVillainStats = df6.to_html(index=False)

