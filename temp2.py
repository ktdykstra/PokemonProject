import pandas as pd
import numpy as np
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

username = "Broskander"
gametype = "gen9vgc2023series1"
api_url = "https://replay.pokemonshowdown.com/search.json?user=" + username + "&format=" + gametype + "&page=" + str(match_page)
driver = webdriver.Chrome()
sdg.gather_matches(username,gametype,driver).text