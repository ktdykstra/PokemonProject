# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import pandas as pd
import numpy as np
import poke_backend_v2 as sdg

username = "Broskander"
gametype = "gen9vgc2023series1"
#print(username)
#print(gametype)
df1, df2, df_individual, df3, df4, df5, df6 = sdg.get_metrics(username, gametype)
print(sdg.get_individual_plot(sdg.get_individual_rates(df1)))
# x=sdg.get_individual_rates(df1)



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

