## necessary imports for testing
import json
import os
import time
from flask_cors import CORS
import pandas as pd
import numpy as np
import importlib
# from flask_bootstrap import Bootstrap
from markupsafe import Markup
importlib.reload(sdg)
import poke_backend_v2 as sdg
import socket 
import pickle
import plotly.express as px
import plotly.graph_objects as go
import plotly.offline as pyo
import re
from selenium import webdriver
import base64
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

## setup a driver
global driver
#global df1
# set up webdriver in headless mode
# service = Service(ChromeDriverManager().install())
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
# download and use the latest ChromeDriver automatically using
# Set up ChromeOptions for headless mode
driver = webdriver.Chrome(options=chrome_options) #service=service, 
driver.get("https://www.google.com/")

## run test
sample_username = "Broskander"
sample_gametype = "gen9vgc2024regf"

## run the data gathering. all_matches == False 
df1, df2, df_hero_indiv, df_villain_indiv, df3, df4, df5, df6 = sdg.get_metrics(username, gametype, driver, False)

test_db=sdg.gather_matches(sample_username, sample_gametype, driver, all_matches=True)
test_db.head()
driver.quit()