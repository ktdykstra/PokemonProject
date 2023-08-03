#!/usr/bin/env python
# coding: utf-8

# In[15]:


#!/usr/bin/env python
# coding: utf-8

# In[102]:


## Import libraries

import requests
import numpy as np
import pandas as pd
# !pip install beautifulsoup4
#from bs4 import BeautifulSoup
# !pip install selenium
#import selenium
#from selenium import webdriver
#from selenium.webdriver.common.by import By
#import json
import re
import warnings
import plotly.express as px
import plotly.graph_objects as go
from selenium import webdriver
import user_agent

## Logistics

warnings.filterwarnings('ignore')

## constant variables
ELO_SCALE=5
ELO_BENCH=0.5


# ### Hours logged
# 
# 24DEC: 45min
# 25DEC: 30min
# 1JAN: 27min
# 1JAN: 2:07
# 2JAN: 15min
# 2JAN: 1:03
# 7JAN: 1:36
# 
# 7FEB: 3:00
# 8FEB: 4:18
# 9FEB: 0:28
# 10FEB: 3:30
# 11FEB: 3:00 + 1:30 + 2:02
# 12FEB: 1:37 + 2:00
# Meetings: 2:00
# 28FEB: 2:57
# 6MAR: 1:15
# Hours: 34

## check person's browser during opening of page


# Create an instance of Chrome WebDriver
driver = webdriver.Chrome()
sample_url="https://play.pokemonshowdown.com/"
driver.get(sample_url)  # Replace with the website you want to access

# Wait for the user to log in or perform any required actions in the browser
input("Please log in and press Enter after login is complete.")

cookies = driver.get_cookies()
driver.quit()
print("test")
## Gather matches via the API

def gather_matches(username, game_type,session):
    
    ## Get first page
    
    match_page=1
    api_url="https://replay.pokemonshowdown.com/search.json?user=" + username + "&format=" + game_type + "&page=" + str(match_page) #"&format=" + game_type 
    s=session
    json=s.get(api_url).json()
    base_db=pd.json_normalize(json)
    
    ## Scroll through pages of games

    pagination=False
    while pagination == False:
        api_url="https://replay.pokemonshowdown.com/search.json?user=" + username + "&format=" + game_type + "&page=" + str(match_page) #"&format=" + game_type +
        json=s.get(api_url).json()
        if json==[]:
            print("Finished searching for matches.")
            pagination=True
        else:
            print("Not done searching for matches...")
            new_db=pd.json_normalize(json).iloc[1:,]
            base_db=pd.concat([base_db,new_db])
            match_page+=1
    
    ## Prettify match database
    
    base_db.rename(columns={"id":"match_id"},inplace=True)
    
    ## Add logs and turns to metadata df

    body_logs, head_logs, tail_logs, turns, turn_count = get_logs(base_db, s)
    base_db["body_logs"]=body_logs
    base_db["head_logs"]=head_logs
    base_db["tail_logs"]=tail_logs
    base_db["turn_logs"]=turns
    base_db["turn_count"]=turn_count
    
    # Get a hero/villian designator

    # MATCH_DB.loc[MATCH_DB['p1']==username, 'hero'] = 'p1'
    base_db['hero'] = base_db['p1'].apply(lambda x: 'p1' if x==username else 'p2')
    base_db['villian'] = base_db['hero'].apply(lambda x: 'p2' if x=="p1" else 'p1')
    
    return base_db


# In[104]:


# In[17]:


def get_logs(df, session):
    
    ## static requests
    s = session
    
    ## Storage lists

    body_logs=[]
    head_logs=[]
    tail_logs=[]
    turns=[]
    turn_count=[]

    ## Access single game log
    
    base_url="https://replay.pokemonshowdown.com"
    
    print("Chunking match log...")

    for i in df.match_id:
        
        ## Identify match
        
        match_id=i
        match_url=base_url + "/" + match_id + ".json"
        json=s.get(match_url).json()
        log=json["log"]

        ## Make LOG
        
        LOG = pd.DataFrame(log.split("\n"),columns=["line_str"])
        LOG.index.name = 'line_num'
        LOG.line_str = LOG.line_str.str.replace(r'\n', ' ', regex=True).str.strip()
        
        # PARAS = CHAPS['chap_str'].str.split(para_pat, expand=True).stack()\
        #     .to_frame('para_str').sort_index()
        # LOG.head()

        ## Get head and tail meta data, as well as body log
        
        head_pat=r"\|turn\|1"
        pat_a = LOG.line_str.str.match(head_pat)
        line_a = LOG.loc[pat_a].index[0]-1
        HEAD_LOG=LOG.loc[:line_a]
        
        tail_pat=r"\|win\|"
        pat_a = LOG.line_str.str.match(tail_pat)
        line_b = LOG.loc[pat_a].index[0]
        TAIL_LOG=LOG.loc[line_b:]

        BODY_LOG=LOG[line_a+1:line_b]
       
        head_logs.append(HEAD_LOG)
        tail_logs.append(TAIL_LOG)
        
        ## Identify where turns begin
        
        
        turn_pat=r"\|turn\|[1-99]"
        turn_lines = BODY_LOG.line_str.str.match(turn_pat, case=False) # Returns a truth vector
        BODY_LOG.loc[turn_lines]
        BODY_LOG.loc[turn_lines, 'turn_number'] = [i+1 for i in range(BODY_LOG.loc[turn_lines].shape[0])]
        
        ## Forward fill turn numbers for every line

        BODY_LOG.loc[turn_lines]
        BODY_LOG.turn_number = BODY_LOG.turn_number.ffill()
        BODY_LOG.head()

        ## Change turns to int and save turns for looping

        BODY_LOG.turn_number = BODY_LOG.turn_number.astype("int")
        body_logs.append(BODY_LOG)

        ## Split turns into separate dataframes into "turns" df
        
        turn_name=[]
        turn_text=[]
        number_turns=BODY_LOG.turn_number.unique()
        turn_count.append(len(number_turns))
        for x in number_turns:
            temp_name="turn_" + str(x)
            turn_name.append(temp_name)
            temp_df=BODY_LOG[BODY_LOG.turn_number==x]
            turn_text.append(temp_df)
        turns_df=pd.DataFrame(list(zip(turn_name, turn_text)),columns=["turn_name","turn_df"])
        turns.append(turns_df)
    
    print("Finished chunking match log.")
    return body_logs, head_logs, tail_logs, turns, turn_count


# In[18]:


## Finding p1 and p2 pokemon. Searchs through "head log"

def find_pokemons_and_leads(target):
    
    ## Set up empty variables
    
    lead_1a="NA"
    lead_1b="NA"
    lead_2a="NA"
    lead_2b="NA"
    p1_pokemons=[]
    p2_pokemons=[]

    for x in target:

        # P1 pokemon list

        pat = re.compile(r"(\|poke\|p1\|)(.+?)(?=,)")
        result=pat.search(x)
        if result == None:
            pass
        else:
            p1_pokemons.append(clip_pokemon(result.group(2)))

        # P2 pokemon list

        pat = re.compile(r"(\|poke\|p2\|)(.+?)(?=,)")
        result=pat.search(x)
        if result == None:
            pass
        else:
            p2_pokemons.append(clip_pokemon(result.group(2)))

    
        # Search for leads
        
        pat_1a=re.compile(r"(\|switch\|p1a\:\s.+\|)(.+?)(?=\,)")
        pat_1b=re.compile(r"(\|switch\|p1b\:\s.+\|)(.+?)(?=\,)")
        pat_2a=re.compile(r"(\|switch\|p2a\:\s.+\|)(.+?)(?=\,)")
        pat_2b=re.compile(r"(\|switch\|p2b\:\s.+\|)(.+?)(?=\,)")
        result=pat_1a.search(x)
        if result == None:
            pass
        else:
            lead_1a=clip_pokemon(result.group(2))
        result=pat_1b.search(x)
        if result == None:
            pass
        else:
            lead_1b=clip_pokemon(result.group(2))
        result=pat_2a.search(x)
        if result == None:
            pass
        else:
            lead_2a=clip_pokemon(result.group(2))
        result=pat_2b.search(x)
        if result == None:
            pass
        else:
            lead_2b=clip_pokemon(result.group(2))
    
    p1_pokemons.sort()
    p2_pokemons.sort()
    
    return p1_pokemons, p2_pokemons, lead_1a, lead_1b, lead_2a, lead_2b


# In[106]:


# In[19]:


## Find winner. Searches through "tail log"

def find_winner(target):
    pat_win = re.compile(r"(\|win\|)(.*)")
    pat_lose = re.compile(r"(\|l\|)(.*)")
    for x in target:
        result_win=pat_win.search(x)
        if(result_win == None):
            pass
        else:
            return(result_win.group(2))


# In[107]:


# In[20]:


## Get rid of annoying male female tag

def clip_pokemon(poke):
    if poke[-2:]=="-M" or poke[-2:]=="-F":
        poke=poke[:-2]
    return poke
clip_pokemon("Indeedee-F")


# In[108]:


# In[21]:


## Run head log functions

def get_head_tail_data(db):
    
    print("Finding meta data...")
    ## Get list of pokemons brought, leads, and wins/losses

    hero_comp_six=[]
    villain_comp_six=[]
    win=[]
    hero_lead_one=[]
    hero_lead_two=[]
    villain_lead_one=[]
    villain_lead_two=[]
    hero_pair_list=[]
    villain_pair_list=[]

    for i, x in enumerate(db.head_logs):

        ## Find Pokemons brought and leads

        p1_pokemons, p2_pokemons, lead_1a, lead_1b, lead_2a, lead_2b = find_pokemons_and_leads(x.line_str)
        if db.iloc[i].hero=="p1":
            hero_comp_six.append(p1_pokemons)
            villain_comp_six.append(p2_pokemons)
        else:
            hero_comp_six.append(p2_pokemons)
            villain_comp_six.append(p1_pokemons)

        ## Mark the win or loss

        winner=find_winner(db.iloc[i].tail_logs.line_str)
        if db.iloc[i].p1==winner:
            winning_player="p1"
        else:
            winning_player="p2"
        if db.iloc[i].hero==winning_player: # If winner
            win.append(1)
        else:
            win.append(0)

        ## Mark the leads and add sorted list for katie
        
        temp_hero=[]
        temp_villain=[]

        if db.iloc[i].hero=="p1":
            hero_lead_one.append(lead_1a)
            hero_lead_two.append(lead_1b)
            villain_lead_one.append(lead_2a)
            villain_lead_two.append(lead_2b)
            temp_hero.append(lead_1a)
            temp_hero.append(lead_1b)
            temp_hero.sort()
            temp_villain.append(lead_2a)
            temp_villain.append(lead_2b)
            temp_villain.sort()
            hero_pair_list.append(temp_hero)
            villain_pair_list.append(temp_villain)
            
        else:
            hero_lead_one.append(lead_2a)
            hero_lead_two.append(lead_2b)
            villain_lead_one.append(lead_1a)
            villain_lead_two.append(lead_1b)
            temp_hero.append(lead_2a)
            temp_hero.append(lead_2b)
            temp_hero.sort()
            temp_villain.append(lead_1a)
            temp_villain.append(lead_1b)
            temp_villain.sort()
            hero_pair_list.append(temp_hero)
            villain_pair_list.append(temp_villain)
 
    db["win"]=win
    db['hero_comp_six']=hero_comp_six
    db['villain_comp_six']=villain_comp_six
    db["hero_lead_one"]=hero_lead_one
    db["hero_lead_two"]=hero_lead_two
    db["villain_lead_one"]=villain_lead_one
    db["villain_lead_two"]=villain_lead_two
    db["sorted_hero_pair"]=hero_pair_list
    db["sorted_villain_pair"]=villain_pair_list
    
    # MATCH_DB['hero_comp_six'] = MATCH_DB['hero_comp_six'].apply(lambda x: 'p1' if x==username else 'p2')
    
    print("Meta data found.")
    return db


# In[109]:


# In[22]:


## Get hero and villain leads

def get_hero_leads(df_row):
    
    hero_lead_one=df_row.hero_lead_one
    hero_lead_two=df_row.hero_lead_two
    villain_lead_one=df_row.villain_lead_one
    villain_lead_two=df_row.villain_lead_two
    return hero_lead_one, hero_lead_two,villain_lead_one,villain_lead_two


# In[110]:


# In[23]:


## Create a turn data structure

def generate_turn_df(db_row):
    turn_data=[]
    hero_pokemon=pd.DataFrame(db_row.hero_comp_six,columns=["pokemon"])
    hero_pokemon["label"]="hero_pokemon"
    villain_pokemon=pd.DataFrame(db_row.villain_comp_six,columns=["pokemon"])
    villain_pokemon.index.rename("villain_pokemon",inplace=True)
    villain_pokemon["label"]="villain_pokemon"
    turn_df=pd.concat([hero_pokemon,villain_pokemon])
    turn_df=turn_df.set_index(["label"])
    turn_df[["begins_field","current_field","ends_field","full_turn", "item_activated","ability_activated"]]=0
    turn_df["move_used"]="NA"
    turn_df=turn_df.reset_index()
    return turn_df


# In[111]:


# In[24]:


def populate_fresh_scorecard(db_row, old_turn, turn_number):

    ## Generate turn score card

    hero_lead_one, hero_lead_two,villain_lead_one,villain_lead_two=get_hero_leads(db_row)
    new_turn=generate_turn_df(db_row)

    ## Include code for looking at past turn's begin_field pokemon/setting up leads for turn 1

    if turn_number==1:
        new_turn.loc[(new_turn["pokemon"]==hero_lead_one) & (new_turn["label"]=="hero_pokemon"),"begins_field"]=1
        new_turn.loc[(new_turn["pokemon"]==hero_lead_one) & (new_turn["label"]=="hero_pokemon"),"current_field"]=1
        new_turn.loc[(new_turn["pokemon"]==hero_lead_two) & (new_turn["label"]=="hero_pokemon"),"begins_field"]=1
        new_turn.loc[(new_turn["pokemon"]==hero_lead_two) & (new_turn["label"]=="hero_pokemon"),"current_field"]=1
        new_turn.loc[(new_turn["pokemon"]==villain_lead_one) & (new_turn["label"]=="villain_pokemon"),"begins_field"]=1
        new_turn.loc[(new_turn["pokemon"]==villain_lead_one) & (new_turn["label"]=="villain_pokemon"),"current_field"]=1
        new_turn.loc[(new_turn["pokemon"]==villain_lead_two) & (new_turn["label"]=="villain_pokemon"),"begins_field"]=1
        new_turn.loc[(new_turn["pokemon"]==villain_lead_two) & (new_turn["label"]=="villain_pokemon"),"current_field"]=1
    else:
        new_turn["begins_field"]=old_turn["ends_field"]
        new_turn["current_field"]=old_turn["ends_field"]
    
    return new_turn


# In[112]:


# In[25]:


def scorecards(db):
    
    print("Generating scorecards...")
    aggregate_scorecards=[]
    
    for x in range(db.shape[0]):
        
        target_match=db.iloc[x]
        target_turns=target_match.turn_logs.turn_df
        #sample_turn=target_turns.iloc[1].line_str
        old_turn=generate_turn_df(target_match)
        turn_number=1
        new_turn=populate_fresh_scorecard(target_match, old_turn, turn_number)
#         #display(new_turn)
        
        match_scorecards=[]
        
        for i in range(target_match.turn_count):
            
            sample_turn=target_turns.iloc[i].line_str
#             print(sample_turn)
#             #display(new_turn)
            new_turn=check_changes(sample_turn, new_turn, target_match, turn_number)
            
            new_turn.loc[new_turn["current_field"]==1,"ends_field"]=1
            new_turn.loc[(new_turn["begins_field"]==1) & (new_turn["ends_field"]==1),"full_turn"]=1
            
            old_turn=new_turn
#             display(new_turn)
            match_scorecards.append(new_turn)
            turn_number=turn_number+1
            new_turn=populate_fresh_scorecard(target_match, old_turn, turn_number)
        
        combined_turns_scorecard=pd.concat(match_scorecards)
        product=create_match_scorecard(combined_turns_scorecard)
#         display(product)
        aggregate_scorecards.append(product)
    
    print("Scorecards generated.")
    return aggregate_scorecards


# In[113]:


# In[26]:


## Create match aggregate scorecard

def create_match_scorecard(combined_turns_scorecard):
    temp=combined_turns_scorecard
    x=temp[["move_used"]]
    moves=pd.get_dummies(x,prefix="")
    full=pd.concat([temp,moves],axis=1).drop("move_used",axis=1)
    full=full.groupby(["label","pokemon"]).agg("sum")
    return full
#temp.groupby(["label","pokemon"])


# In[27]:


# In[114]:


def check_changes(sample_turn, new_turn, target_match, turn_number):
    
    ## KNOWN BUG: Moves, as well as some item/ability extraction, not regexing properly. "gen9vgc2023series1-1765435913"

    ## Check curent turn text

    hero_lead_one, hero_lead_two,villain_lead_one,villain_lead_two=get_hero_leads(target_match)
        
    for x in sample_turn:
        
        ## Move extraction

        move_name="NA"
        pat=re.compile(r"(\|move\|)(p[1-2][a-b])(\:\s+)(.+)(\|)(.+?)(?=\|)")
        result=pat.search(x)
        if result == None:
            pass
        else:
            pokemon_name=result.group(4)
            move_name=result.group(6)
#             print(move_name)
            player_number=result.group(2)
#             print(player_number)
            if "p1" in player_number and target_match.hero=="p1":
                new_turn.loc[(new_turn["pokemon"]==pokemon_name) & (new_turn["label"]=="hero_pokemon"),"move_used"]=move_name
            else:
                new_turn.loc[(new_turn["pokemon"]==pokemon_name) & (new_turn["label"]=="villain_pokemon"),"move_used"]=move_name

        ## Item extraction

        pat=re.compile(r"(p[1-2][a-b])(\:\s+)(.+?)(?=\|)(.+?)(?=item\:\s+)(.+)") #.+?)(?=\|)
        #pat=re.compile(r"(p[1-2][a-b])(.+)(item\:\s+)(.+?)")
        result=pat.search(x)
        if result == None:
            pass
        else:
            player_number=result.group(1)
            pokemon_name=result.group(3)
            #item_name=result.group(5)
            if "p1" in player_number and target_match.hero=="p1":
                new_turn.loc[(new_turn["pokemon"]==pokemon_name) & (new_turn["label"]=="hero_pokemon"),"item_activated"]=1
            else:
                new_turn.loc[(new_turn["pokemon"]==pokemon_name) & (new_turn["label"]=="villain_pokemon"),"item_activated"]=1

        ## Check for switches

        pat=re.compile(r"(\|switch\|)(p[1-2][a-b])(\:\s)(.+?)(?=\|)")
        result=pat.search(x)
        if result == None:
            pass
        else:
            new_lead_number=result.group(2)
            new_lead_name=result.group(4)
            if new_lead_number=="p1a" and target_match.hero=="p1":
    #             new_lead_1a=True
                new_turn.loc[(new_turn["pokemon"]==hero_lead_one) & (new_turn["label"]=="hero_pokemon"),"current_field"]=0
                hero_lead_one=new_lead_name
                new_turn.loc[(new_turn["pokemon"]==hero_lead_one) & (new_turn["label"]=="hero_pokemon"),"current_field"]=1
            if new_lead_number=="p1a" and target_match.hero=="p2":
    #             new_lead_1a=True
                new_turn.loc[(new_turn["pokemon"]==villain_lead_one) & (new_turn["label"]=="villain_pokemon"),"current_field"]=0
                villain_lead_one=new_lead_name
                new_turn.loc[(new_turn["pokemon"]==villain_lead_one) & (new_turn["label"]=="villain_pokemon"),"current_field"]=1
            if new_lead_number=="p1b" and target_match.hero=="p1":
    #             new_lead_1a=True
                new_turn.loc[(new_turn["pokemon"]==hero_lead_two) & (new_turn["label"]=="hero_pokemon"),"current_field"]=0
                hero_lead_two=new_lead_name
                new_turn.loc[(new_turn["pokemon"]==hero_lead_two) & (new_turn["label"]=="hero_pokemon"),"current_field"]=1
            if new_lead_number=="p1b" and target_match.hero=="p2":
    #             new_lead_1a=True
                new_turn.loc[(new_turn["pokemon"]==villain_lead_two) & (new_turn["label"]=="villain_pokemon"),"current_field"]=0
                villain_lead_two=new_lead_name
                new_turn.loc[(new_turn["pokemon"]==villain_lead_two) & (new_turn["label"]=="villain_pokemon"),"current_field"]=1
            if new_lead_number=="p2a" and target_match.hero=="p2":
    #             new_lead_1a=True
                new_turn.loc[(new_turn["pokemon"]==hero_lead_one) & (new_turn["label"]=="hero_pokemon"),"current_field"]=0
                hero_lead_one=new_lead_name
                new_turn.loc[(new_turn["pokemon"]==hero_lead_one) & (new_turn["label"]=="hero_pokemon"),"current_field"]=1
            if new_lead_number=="p2a" and target_match.hero=="p1":
    #             new_lead_1a=True
                new_turn.loc[(new_turn["pokemon"]==villain_lead_one) & (new_turn["label"]=="villain_pokemon"),"current_field"]=0
                villain_lead_one=new_lead_name
                new_turn.loc[(new_turn["pokemon"]==villain_lead_one) & (new_turn["label"]=="villain_pokemon"),"current_field"]=1
            if new_lead_number=="p2b" and target_match.hero=="p2":
    #             new_lead_1a=True
                new_turn.loc[(new_turn["pokemon"]==hero_lead_two) & (new_turn["label"]=="hero_pokemon"),"current_field"]=0
                hero_lead_two=new_lead_name
                new_turn.loc[(new_turn["pokemon"]==hero_lead_two) & (new_turn["label"]=="hero_pokemon"),"current_field"]=1
            if new_lead_number=="p2b" and target_match.hero=="p1":
    #             new_lead_1a=True
                new_turn.loc[(new_turn["pokemon"]==villain_lead_two) & (new_turn["label"]=="villain_pokemon"),"current_field"]=0
                villain_lead_two=new_lead_name
                new_turn.loc[(new_turn["pokemon"]==villain_lead_two) & (new_turn["label"]=="villain_pokemon"),"current_field"]=1
    
    ## Account for ability extraction
    
    if turn_number==1:
        target_turn=target_match.turn_logs.turn_df.iloc[0]
        target_turn=pd.concat([target_match.head_logs,target_turn])
#         print("ability turn")
#         display(target_turn)
        for x in target_turn.line_str:
            #pat=re.compile(r"(p[1-2][a-b])(\:\s+)(.+?)(?=\|)(.+?)(?=item\:\s+)(.+)") #.+?)(?=\|)
            pat=re.compile(r"(ability\:\s+)(.+?)(?=\|)(.+)(p[1-2][a-b])(\:\s+)(.+)")
            result=pat.search(x)
            if result == None:
                pass
            else:
                player_number=result.group(4)
                pokemon_name=result.group(6)
                ability_name=result.group(2)
                #item_name=result.group(5)
                if "p1" in player_number and target_match.hero=="p1":
                    new_turn.loc[(new_turn["pokemon"]==pokemon_name) & (new_turn["label"]=="hero_pokemon"),"ability_activated"]=1
                else:
                    new_turn.loc[(new_turn["pokemon"]==pokemon_name) & (new_turn["label"]=="villain_pokemon"),"ability_activated"]=1 
    
    return new_turn


# In[115]:


# In[28]:


## Publish lead pairs

def publish_lead_pairs(MATCH_DB):

    hero_pairs=[]
    villain_pairs=[]

    for i in range(MATCH_DB.shape[0]):
        hero_pair=[]
        hero_pair.append(MATCH_DB.iloc[i].hero_lead_one)
        hero_pair.append(MATCH_DB.iloc[i].hero_lead_two)
        hero_pair.sort()
        hero_pairs.append("".join(hero_pair))
        villain_pair=[]
        villain_pair.append(MATCH_DB.iloc[i].villain_lead_one)
        villain_pair.append(MATCH_DB.iloc[i].villain_lead_two)
        villain_pair.sort()
        villain_pairs.append("".join(villain_pair))

    MATCH_DB["hero_pair"]=hero_pairs
    MATCH_DB["villain_pair"]=villain_pairs
    return MATCH_DB


# In[116]:


# In[29]:


## Publish comps

def publish_comps(MATCH_DB):
    hero_comps=[]
    villain_comps=[]
    for i in range(MATCH_DB.shape[0]):
        hero_comp=MATCH_DB.iloc[i].hero_comp_six
        hero_comp="".join(hero_comp)
        hero_comps.append(hero_comp)
        villain_comp=MATCH_DB.iloc[i].villain_comp_six
        villain_comp="".join(villain_comp)
        villain_comps.append(villain_comp)
        
    MATCH_DB["hero_comp_fused"]=hero_comps
    MATCH_DB["villain_comp_fused"]=villain_comps
        
    return MATCH_DB


# In[117]:


# In[30]:


## publish losses

def publish_losses(MATCH_DB):
    MATCH_DB["loss"]=0
    MATCH_DB.loc[MATCH_DB["win"]==0,"loss"]=1
    return MATCH_DB


# In[118]:


# In[31]:


## Convert to formatted string

def format_percent(line):
    
    line="%.1f" % line
    
    return line


# In[119]:


# In[32]:


## Create pair hero metrics

def get_pair_metrics(MATCH_DB):


    pairs_db=MATCH_DB.groupby(["hero_pair"]).agg({"sorted_hero_pair":"first","win":"sum","match_id":"count"}).reset_index()
    pairs_db["pairs_winrate"]= pairs_db.win/pairs_db.match_id*100
    pairs_db.rename(columns={"match_id":"num_games","win":"num_wins"},inplace=True)
    pairs_db["elo_rate"]=get_elo(ELO_SCALE, ELO_BENCH, pairs_db.num_wins, pairs_db.num_games).apply(format_percent)
    pairs_db["pairs_winrate"]=pairs_db.apply(lambda row: format_percent(row["pairs_winrate"]),axis=1)
    pairs_db["hero_one"]=pairs_db.sorted_hero_pair.apply(lambda x: x[0])
    pairs_db["hero_two"]=pairs_db.sorted_hero_pair.apply(lambda x: x[1])
    hero_pairs_db=pairs_db
    
    villains_pairs_db=MATCH_DB.groupby(["villain_pair"]).agg({"sorted_villain_pair":"first","loss":"sum","match_id":"count"}).reset_index()
    villains_pairs_db["pairs_loserate"]=villains_pairs_db.loss/villains_pairs_db.match_id*100
    villains_pairs_db.rename(columns={"match_id":"num_games","loss":"num_losses"},inplace=True)
    villains_pairs_db["elo_rate"]=get_elo(ELO_SCALE, ELO_BENCH,villains_pairs_db.num_losses, villains_pairs_db.num_games).apply(format_percent)
    villains_pairs_db["pairs_loserate"]=villains_pairs_db.apply(lambda row: format_percent(row["pairs_loserate"]),axis=1)
    villains_pairs_db["villain_one"]=villains_pairs_db.sorted_villain_pair.apply(lambda x: x[0])
    villains_pairs_db["villain_two"]=villains_pairs_db.sorted_villain_pair.apply(lambda x: x[1])
    
    return hero_pairs_db, villains_pairs_db


# In[120]:


# In[33]:


## Comps metrics

def get_comps_metrics(MATCH_DB):

    hero_comps_db=MATCH_DB.groupby(["hero_comp_fused"]).agg({"hero_comp_six":"first","win":"sum","match_id":"count"}).reset_index()
    hero_comps_db["comps_winrate"]=hero_comps_db.win/hero_comps_db.match_id*100
    hero_comps_db.rename(columns={"match_id":"num_games","win":"num_wins"},inplace=True)
    hero_comps_db["elo_score"]=get_elo(ELO_SCALE, ELO_BENCH, hero_comps_db.num_wins, hero_comps_db.num_games).apply(format_percent)
    hero_comps_db["comps_winrate"]=hero_comps_db.comps_winrate.apply(format_percent)
    hero_comps_db["hero_one"]=hero_comps_db.hero_comp_six.apply(lambda x: x[0])
    hero_comps_db["hero_two"]=hero_comps_db.hero_comp_six.apply(lambda x: x[1])
    hero_comps_db["hero_three"]=hero_comps_db.hero_comp_six.apply(lambda x: x[2])
    hero_comps_db["hero_four"]=hero_comps_db.hero_comp_six.apply(lambda x: x[3])
    hero_comps_db["hero_five"]=hero_comps_db.hero_comp_six.apply(lambda x: x[4])
    hero_comps_db["hero_six"]=hero_comps_db.hero_comp_six.apply(lambda x: x[5])

    villain_comps_db=MATCH_DB.groupby(["villain_comp_fused"]).agg({"villain_comp_six":"first","loss":"sum","match_id":"count"}).reset_index()
    villain_comps_db["comps_lossrate"]=villain_comps_db.loss/villain_comps_db.match_id*100
    villain_comps_db.rename(columns={"match_id":"num_games","loss":"num_losses"},inplace=True)
    villain_comps_db["elo_score"]=get_elo(ELO_SCALE, ELO_BENCH, villain_comps_db.num_losses,  villain_comps_db.num_games).apply(format_percent)
    villain_comps_db["comps_lossrate"]=villain_comps_db.comps_lossrate.apply(format_percent)
    villain_comps_db["villain_one"]=villain_comps_db.villain_comp_six.apply(lambda x: x[0])
    villain_comps_db["villain_two"]=villain_comps_db.villain_comp_six.apply(lambda x: x[1])
    villain_comps_db["villain_three"]=villain_comps_db.villain_comp_six.apply(lambda x: x[2])
    villain_comps_db["villain_four"]=villain_comps_db.villain_comp_six.apply(lambda x: x[3])
    villain_comps_db["villain_five"]=villain_comps_db.villain_comp_six.apply(lambda x: x[4])
    villain_comps_db["villain_six"]=villain_comps_db.villain_comp_six.apply(lambda x: x[5])
    
    return hero_comps_db, villain_comps_db


# In[121]:


# In[34]:


## Get metametrics

def get_metametrics(MATCH_DB):
    
    num_wins=MATCH_DB[MATCH_DB.win==1].shape[0]
    num_games=MATCH_DB.shape[0]
    win_rate=(num_wins/num_games*100)
    win_rate=format_percent(win_rate)
    meta_df=pd.DataFrame({"num_wins":num_wins,"num_games":num_games,"win_rate":win_rate}, index=[0])
    return meta_df


# In[122]:


# In[35]:


## Creates the full MATCH_DB with all relevant data

def get_all_data(MATCH_DB):
    
    ## Head and tail metadata
    
    MATCH_DB=get_head_tail_data(MATCH_DB)
    
    ## Aggregate scorecards

    MATCH_DB["match_scorecards"]=scorecards(MATCH_DB)
    
    
    ## Get lead pairs fused
    
    MATCH_DB=publish_lead_pairs(MATCH_DB)
    
    ## Get comps fused
    
    MATCH_DB=publish_comps(MATCH_DB)
    
    ## Get losses
    
    MATCH_DB=publish_losses(MATCH_DB)
    
    return MATCH_DB


# In[123]:


## Run all steps (for front end)


# In[36]:


def get_metrics(sample_username, sample_game_type):
    
    ## establish requests session
    s = requests.Session()
    
    ## Gather matches from Showdown
    
    MATCH_DB=gather_matches(sample_username, sample_game_type,s)
    
    ## Aggregate data from matches
    
    MATCH_DB=get_all_data(MATCH_DB)
    
    ## Generate match library, metametrics df, pair metric df, comp metric df
    
    print("Generating metrics...")
    
    hero_comps_db, villain_comps_db = get_comps_metrics(MATCH_DB)
    hero_pairs_db, villain_pairs_db = get_pair_metrics(MATCH_DB)
    
    print("Metrics generated.")
    return MATCH_DB, get_metametrics(MATCH_DB), get_individual_rates(MATCH_DB), get_villain_indiv_rates(MATCH_DB), hero_pairs_db, villain_pairs_db, hero_comps_db, villain_comps_db


# In[127]:


# In[37]:


## calculate elo score
def get_elo(elo_scale, elo_benchmark, win_series, total_match_series):
    elo_score = (win_series + elo_scale * elo_benchmark)/(total_match_series + elo_scale)*100
    return elo_score


# In[56]:


# # ## Samples for testing
# ## original time: 28 seconds
# import time
# # username=input("Please input username to search:")
# # game_type=input("Please input game type to search:")
# sample_username="Broskander" #"Broskander"
# sample_game_type="gen9vgc2023series1" #"gen9vgc2023series1"
# library, meta, hero_pairs_db, villain_pairs_db, hero_comps_db, villain_comps_db =get_metrics(sample_username, sample_game_type)


# In[12]:


# # ## Get data
# import time
# start = time.time()
# library, meta, hero_pairs_db, villain_pairs_db, hero_comps_db, villain_comps_db =get_metrics(sample_username, sample_game_type)
# end = time.time()
# print(end - start)


# In[10]:

## helper function for determining if pokemon assisted with win
def check_conditional_win(row):
    if (row.used_total==1 and row.win==1):
        return 1
    else:
        return 0    

## helper function for determining if pokemon assisted with loss
def check_conditional_loss(row):
    if (row.used_total==1 and row.loss==1):
        return 1
    else:
        return 0    


## get HERO individual pokemon win rates
def get_individual_rates(library):
    
    ## second version
    
    result=library[["match_id","hero_comp_six","win","match_scorecards"]].explode("hero_comp_six")
    result["used_total"]=0
    holder=pd.DataFrame()
    holder
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
    return result.sort_values(by="elo_score", ascending=True)
    
    # ## implement algo
    # result=library[["match_id","hero_comp_six","win","match_scorecards"]].explode("hero_comp_six")
    
    # # search for played or not
    # result["used"]=0
    # holder=pd.DataFrame()
    # for x in library.match_scorecards:
    #     holder=pd.concat([holder,x.loc["hero_pokemon","begins_field"]])
    # holder.columns=["began"]
    # result["used"]=holder.began.apply(lambda x: 0 if x==0 else 1)
    
    # result.rename(columns={"hero_comp_six":"hero_pokemon","match_id":"total_games"},inplace=True)
    # #result["conditional_total"]=result.total_games.apply
    # result=result.groupby("hero_pokemon").agg({"total_games":"count","win":"sum"})
    # result["win_rate"]=result.win/result.total_games*100
    # result.win_rate=result.win_rate.apply(format_percent)
    # result["elo_score"]=get_elo(ELO_SCALE, ELO_BENCH, result.win, result.total_games).apply(format_percent)
    # return result.sort_values(by="elo_score", ascending=True)

## run code
# get_individual_rates(library)

## create HERO plotly graph and render html
def get_individual_plot(individual_result):
    
    ## reconfigure dataset so that shows up pretty in plot
    df=individual_result.copy()
    df=df.reset_index()
    df.columns=["Hero Pokemon","Games Played","Games Used", "Games Won","Raw Win Rate","Weighted Win Rate"]
    df["Games Lost"]=df["Games Used"]-df["Games Won"]
    
    ## the perfect chart
    fig = go.Figure()
    
    
    # Add the stacked bar plot for "Games Won" and "Games Played2"
    fig.add_trace(
        go.Bar(
            x=df["Hero Pokemon"],
            y=df["Games Won"],
            marker_color="#72B7B2",
            name="Games Won",
        )
    )
    
    fig.add_trace(
        go.Bar(
            x=df["Hero Pokemon"],
            y=df["Games Lost"],
            marker_color="#7F7F7F",
            name="Games Lost",
        )
    )
    
    # Calculate the weighted win rate (Games Won / Games Played2) and add it as a line plot on the second y-axis
    weighted_win_rate = df["Weighted Win Rate"]
    fig.add_trace(
        go.Scatter(
            x=df["Hero Pokemon"],
            y=weighted_win_rate,
            mode="lines+markers",
            line=dict(color="#FF0000"),  # You can specify the color you want for the line plot
            name="Weighted Win Rate",
            yaxis="y2",  # Specify the second y-axis for this trace
        )
    )
    
    # Update the layout with axis labels and other configurations
    fig.update_layout(
        barmode="stack",  # Set barmode to "stack" for stacked bar plots
        yaxis=dict(title="Games Used", side="left"),  # Update the y-axis title as needed
        yaxis2=dict(title="Weighted Win Rate %", overlaying="y", side="right"),
        showlegend=True,
        title=dict(text="Weighted Win Rate of Individual Pokemon (Used in Matches)",x=0.5),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis_tickangle=-90, 
        xaxis_automargin=True
    )
        
    return fig


## get VILLAIN individual pokemon win rates
def get_villain_indiv_rates(library):
    
    ## second version
    
    result=library[["match_id","villain_comp_six","loss","match_scorecards"]].explode("villain_comp_six")
    result["used_total"]=0
    holder=pd.DataFrame()
    holder
    for x in library.match_scorecards:
        holder=pd.concat([holder,x.loc["villain_pokemon","begins_field"]])
    holder.columns=["began"]
    holder["used"]=holder.began.apply(lambda x: 0 if x==0 else 1)
    result["used_total"]=holder["used"].values
    result["loss_conditional"]=result.apply(check_conditional_loss,axis=1)
    result.rename(columns={"villain_comp_six":"villain_pokemon","match_id":"total_games"},inplace=True)
    result=result.groupby("villain_pokemon").agg({"total_games":"count","used_total":"sum","loss_conditional":"sum"})
    result["loss_rate"]=result.loss_conditional/result.used_total*100
    result.loss_rate.fillna(0,inplace=True)
    result.loss_rate=result.loss_rate.apply(format_percent)
    result["elo_score"]=get_elo(ELO_SCALE, ELO_BENCH, result.loss_conditional, result.used_total).apply(format_percent)
    return result.sort_values(by="elo_score", ascending=True)

## create VILLAIN plotly graph and render html
def get_villain_indiv_plot(individual_result):
    
    ## reconfigure dataset so that shows up pretty in plot
    df=individual_result.copy()
    df=df.reset_index()
    df.columns=["Villain Pokemon","Games Played","Games Played Against", "Games Lost Against","Raw Loss Rate","Weighted Loss Rate"]
    df["Games Won Against"]=df["Games Played Against"]-df["Games Lost Against"]
    
    ## the perfect chart
    fig = go.Figure()
    
    
    # Add the stacked bar plot for "Games Won" and "Games Played2"
    fig.add_trace(
        go.Bar(
            x=df["Villain Pokemon"],
            y=df["Games Lost Against"],
            marker_color="#72B7B2",
            name="Games Lost Against",
        )
    )
    
    fig.add_trace(
        go.Bar(
            x=df["Villain Pokemon"],
            y=df["Games Won Against"],
            marker_color="#7F7F7F",
            name="Games Won Against",
        )
    )
    
    # Calculate the weighted win rate (Games Won / Games Played2) and add it as a line plot on the second y-axis
    weighted_win_rate = df["Weighted Loss Rate"]
    fig.add_trace(
        go.Scatter(
            x=df["Villain Pokemon"],
            y=weighted_win_rate,
            mode="lines+markers",
            line=dict(color="#FF0000"),  # You can specify the color you want for the line plot
            name="Weighted Loss Rate",
            yaxis="y2",  # Specify the second y-axis for this trace
        )
    )
    
    # Update the layout with axis labels and other configurations
    fig.update_layout(
        barmode="stack",  # Set barmode to "stack" for stacked bar plots
        yaxis=dict(title="Games Used", side="left"),  # Update the y-axis title as needed
        yaxis2=dict(title="Weighted Loss Rate %", overlaying="y", side="right"),
        showlegend=True,
        title=dict(text="Weighted Loss Rate Against Individual Pokemon (Used in Matches)",x=0.5),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis_tickangle=-90, 
        xaxis_automargin=True
    )
        
    return fig
# In[9]:


# display(library, meta, hero_comps_db, hero_pairs_db, library.iloc[0].turn_logs.iloc[-1].turn_df, library.iloc[0].match_scorecards)


# In[7]:


# start = time.time()
# temp=gather_matches(sample_username, sample_game_type)
# end = time.time()
# print(end - start)


# In[8]:


# start = time.time()
# temp=gather_matches(sample_username, sample_game_type)
# end = time.time()
# print(end - start)


# In[4]:


# start = time.time()
# get_logs(temp)
# end = time.time()
# print(end - start)


# In[5]:


# start = time.time()
# get_all_data(temp)
# end = time.time()
# print(end - start)


# In[6]:


# # In[26]:


# display(library, meta, hero_pairs_db,library.iloc[0].turn_logs.iloc[-1].turn_df, library.iloc[0].match_scorecards)
# # display(library, meta, hero_pairs_db, villain_pairs_db, hero_comps_db, villain_comps_db)


# In[ ]:




