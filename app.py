from flask import Flask, redirect, render_template, request, url_for, session
from flask_caching import Cache
import redis 
import certifi
import ssl

from flask import jsonify
import json
import os
import time
from flask_cors import CORS
# from flask_bootstrap import Bootstrap
from markupsafe import Markup
import pandas as pd
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



from requests.adapters import BaseAdapter
from requests.sessions import Session
# bring in dash_app
#from dash_app import create_dash

## global variables
browser_type = "Unclear"
df1=None
# cookies=[]
# driver.quit()
## try chatgpts reco
# class WebDriverAdapter(BaseAdapter):
#     def __init__(self, webdriver):
#         self.webdriver = webdriver

#     def send(self, request, *args, **kwargs):
#         response = self.webdriver.execute_script(
#             f"return fetch('{request.url}', {kwargs})")
#         return response

# # Create a custom session using the WebDriverAdapter
# def create_custom_session(webdriver):
#     session = Session()
#     session.mount('http://', WebDriverAdapter(webdriver))
#     session.mount('https://', WebDriverAdapter(webdriver))
#     return session



app = Flask(__name__)

#need secret key to save browser across sessions
app.secret_key = os.urandom(24)
df1=None

# Configure the shared cache
# Configure Redis as the cache backend
app.config['CACHE_TYPE'] = 'redis'
app.config['CACHE_REDIS_URL'] = os.environ.get('STACKHERO_REDIS_URL_CLEAR')
cache = Cache(app)

CORS(app)

# Set the REQUESTS_CA_BUNDLE environment variable to use certifi certificates
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# Create an SSL context with certificate verification
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Create the Redis client with SSL context
redis_client = redis.Redis.from_url(
    app.config['CACHE_REDIS_URL'],
    connection_class=redis.Connection
)



#  fetch the df1 value from the cache
def get_df1():
    df_bytes = redis_client.get('df')
    if df_bytes is not None:
        df = pickle.loads(df_bytes)
        return df
    else:
        return None
    
# update the value of df1 in the cache
def set_df1(df):
    df_bytes = pickle.dumps(df)
    redis_client.set('df', df_bytes)

## get the browser type of flask session
#@app.route('/test')
def get_browser():
    og_type = request.headers.get('User-Agent')
    if 'Chrome' in og_type:
        browser_type='Chrome'
    elif 'Mozilla' in og_type:
        browser_type='Mozilla'
    elif 'Safari' in og_type:
        browser_type='Safari'
    elif 'Edge' in og_type:
        browser_type='Edge'
    elif 'Opera' in og_type:
        browser_type='Opera'
    else:
        browser_type='Unclear'
    return browser_type #,render_template('test.html')

## generate webdriver depending on browser type
def open_login_tab(browser_type):
    if browser_type =="Chrome":
        driver=webdriver.Chrome()#options=chrome_options
        return driver
    elif browser_type=="Mozilla":
        driver=webdriver.Firefox()
        return driver
    elif browser_type=="Safari":
        driver=webdriver.Safari()
        return driver
    elif browser_type=="Edge":
        driver=webdriver.Edge()
        return driver
    else:
        raise ValueError(f"Invalid browser_type: {browser_type}")


def cookie_collecter(driver):
    driver.get('https://play.pokemonshowdown.com')

    # Define a list of button identifiers (names or XPath expressions)
    #button_identifiers = ['login',   '/html/body/div[5]/div/form/p[5]/button[1]']
    

    time.sleep(30)

    return driver



@app.route('/')
def collect_email():
    #submitted = request.args.get('submitted')
    return render_template('email.html')


# Route to handle the form submission
@app.route('/submit_form', methods=['POST'])
def submit_form():
    # Process the form data (you can save the email to your database or perform any other actions here)
    # Google forms does this for us, yay!
    # email = request.form.get('email')

    # Redirect the user to the main page page
    return redirect('/main')



@app.route('/main')
def index():
    #submitted = request.args.get('submitted')
    return render_template('index.html')


#sample_username="Broskander" 
#sample_game_type="gen9vgc2023series1"


@app.route("/get_data", methods=['GET','POST'])
def get_data():
        if request.method == 'POST':
            #access the data from form
            ## Username
            username = request.form["username"]
            gametype = request.form["gametype"]
            #print(username)
            #print(gametype)
            
            #### WHERE EDITS BEGIN ####

            # prevent popup window when initializing driver
            # chrome_options = Options()
            # chrome_options.add_argument("--headless")


            # driver = webdriver.Chrome(options=chrome_options)

            #driver=cookie_collecter(driver)
            df1, df2, df_hero_indiv, df_villain_indiv, df3, df4, df5, df6 = sdg.get_metrics(username, gametype, driver, False)
            # driver.quit()
            #print(output)
            
            # hero individual plot
            hero_plotly = pyo.plot(sdg.get_individual_plot(df_hero_indiv), output_type="div")
            villain_plotly = pyo.plot(sdg.get_villain_indiv_plot(df_villain_indiv), output_type="div")
            
            #df with num_wins, num_games, win_rate
            overallStats = df2.to_html(index=False, classes='table table-responsive table-hover')
            num_games = str(df2.loc[0, 'num_games'])
            num_wins = str(df2.loc[0, 'num_wins'])
            win_rate = str(df2.loc[0, 'win_rate'])
            
            #dfs with individual hero pokemon winrates and elo scores
            df_hero_indiv = df_hero_indiv.reset_index()
            df_hero_indiv=df_hero_indiv.loc[:,["hero_pokemon","win_conditional","used_total","elo_score"]]
            df_hero_indiv.columns=['Hero Pokemon', "Games Won", "Games Played", "Weighted Win Rate"]
            # df_hero_indiv.to_csv("ind_stats.csv")
            df_hero_indiv["Weighted Win Rate"]=df_hero_indiv["Weighted Win Rate"].apply(lambda x: x+"%")
            df_hero_indiv.sort_values(by="Weighted Win Rate",ascending=False,inplace=True)
            hero_indiv_stats = df_hero_indiv.head(5).to_html(index=False)
            
            #dfs with individual villain pokemon loss rates and elo scores
            df_villain_indiv = df_villain_indiv.reset_index()
            df_villain_indiv=df_villain_indiv.loc[:,["villain_pokemon","loss_conditional","used_total","elo_score"]]
            df_villain_indiv.columns=['Villain Pokemon', "Games Lost Against", "Games Played Against", "Weighted Loss Rate"]
            # df_hero_indiv.to_csv("ind_stats.csv")
            df_villain_indiv["Weighted Loss Rate"]=df_villain_indiv["Weighted Loss Rate"].apply(lambda x: x+"%")
            df_villain_indiv.sort_values(by="Weighted Loss Rate",ascending=False,inplace=True)
            villain_indiv_stats = df_villain_indiv.head(5).to_html(index=False)
            
            #dfs with hero pairs, games and win rates breakdown 
            df3=df3.loc[:,["hero_one","hero_two","num_wins","num_games","elo_rate"]]
            df3.columns = ['Hero Lead 1', 'Hero Lead 2', "Games Won", "Games Played", "Weighted Win Rate"]
            df3.sort_values(by="Weighted Win Rate",ascending=False,inplace=True)
            df3["Weighted Win Rate"]=df3["Weighted Win Rate"].apply(lambda x: x+"%")
            heroPairStats = df3.head(5).to_html(index=False)
            
            ## villain pair stats
            df4=df4.loc[:,["villain_one","villain_two","num_losses","num_games","elo_rate"]]
            df4.columns = ['Villain Lead 1', 'Villain Lead 2', "Games Lost Against", "Games Played Against", "Weighted Loss Rate"]
            df4.sort_values(by="Weighted Loss Rate",ascending=False,inplace=True)
            df4["Weighted Loss Rate"]=df4["Weighted Loss Rate"].apply(lambda x: x+"%")
            villainPairStats = df4.head(5).to_html(index=False)
            
            ## hero comp stats
            df5=df5.loc[:,["hero_comp_six","num_wins","num_games","elo_score"]]
            df5.columns = ['Hero Teams', 'Games Won', "Games Played", "Weighted Win Rate"]
            df5.sort_values(by="Weighted Win Rate",ascending=False,inplace=True)
            df5["Weighted Win Rate"]=df5["Weighted Win Rate"].apply(lambda x: x+"%")
            df5
            sixTeamHeroStats = df5.head(5).to_html(index=False)
            
            ## hero comp stats
            df6=df6.loc[:,["villain_comp_six","num_losses","num_games","elo_score"]]
            df6.columns = ["Villain Teams","Games Lost Against", "Games Played Against", "Weighted Loss Rate"]
            df6.sort_values(by="Weighted Loss Rate",ascending=False,inplace=True)
            df6["Weighted Loss Rate"]=df6["Weighted Loss Rate"].apply(lambda x: x+"%")
            sixTeamVillainStats = df6.head(5).to_html(index=False)

            # Define the CSS style for the table
            table_style = """
            <style>
                table {
                    border-collapse: collapse;
                    width: 100%;
                    max-width: 800px;
                    margin: auto;
                    margin-bottom: 1em;
                }
                
                th {
                    font-weight: bold;
                    text-align: left;
                    color: white;
                    background-color: #9d5bd9;
                    padding: 0.5em;
                }
                
                tr:hover {
                    background-color: #a759d13f;
                }
                
                td, th {
                    border: 1px solid #ddd;
                    padding: 0.5em;
                    text-align: left;
                }
                
                @media (max-width: 768px) {
                    table {
                        font-size: 0.8em;
                    }
                    
                    th, td {
                        padding: 0.25em;
                    }
                }
            </style>
            """
            
            # katies original html creation
            output_html = Markup(table_style +"<h1 style='text-align: center;'>Top 5 Hero Pokemon</h1>" +
                                 "<br><br>" +
                                 hero_indiv_stats + 
                                 "<br><br>" +
                                 hero_plotly+ 
                                 "<br><br>" +
                                 "<h1 style='text-align: center;'>Top 5 Villain Pokemon</h1>" +
                                 "<br><br>" +
                                 villain_indiv_stats + 
                                 "<br><br>" +
                                 villain_plotly+ 
                                 "<br><br>" +
                                 "<h1 style='text-align: center;'>Top 5 Hero Comps</h1>"+
                                 "<br><br>" +
                                 sixTeamHeroStats+ 
                                 "<br><br>" +
                                 "<h1 style='text-align: center;'>Top 5 Villain Comps</h1>"+
                                 "<br><br>" +
                                 sixTeamVillainStats)
            
            
            return render_template('results.html', username = username, num_games=num_games, win_rate=win_rate, num_wins=num_wins, result = output_html)
        else:
            print("did not retrieve input")
            return render_template('index.html')


#opening the pop-up for private replay data login
# @app.route('/open_popup', methods=['POST'])
# def open_popup():
#     # OPEN SHOWDOWN LOGIN
#     # browser_type=get_browser()
#     # driver=open_login_tab(browser_type) # builds initial driver
    

#     global driver
#     # Initialize the driver only if it hasn't been created yet
#     chrome_options = Options()
#     chrome_options.add_argument("--headless")  # Uncomment this line to run headless (without GUI)

#     if driver is None:
#         driver = webdriver.Chrome(options=chrome_options)
#     driver=cookie_collecter(driver) # takes user to login page via driver
    
#     # custom_session = create_custom_session(driver)
    
#     return {'success': True}

# Run selenium for user login
def login_showdown(username, password, driver):
    # global driver
    # Navigate to the login page
    login_url = "https://play.pokemonshowdown.com/"
    driver.get(login_url)

    # Wait for the login page to load
    time.sleep(2)  # Adjust the wait time as needed

    # Submit the login form
    login_button = driver.find_element(By.NAME, "login")
    login_button.click()

    # Find the username and password input fields and fill them out
    username_field = driver.find_element(By.NAME, "username")
    username_field.send_keys(username)
    button = driver.find_element(By.XPATH, "//button[@type='submit']")
    button.click()
    # time.sleep(2) 
    wait = WebDriverWait(driver, 10)
    pw_field = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "textbox")))
    pw_field.send_keys(password)
    button = driver.find_element(By.XPATH, "//button[@type='submit']")
    button.click()
    time.sleep(2)
    
    return driver

#function for retrieving analytics on private & public replays 
@app.route("/get_data_private", methods=['GET','POST'])
@cache.cached(timeout=60)
def get_data_private():
        global driver
        #global df1

        # Set up the Chrome WebDriver in headless mode
        # chrome_options = Options()
        #chrome_options.add_argument("--headless")  # Uncomment this line to run headless (without GUI)
        service = Service(ChromeDriverManager().install())
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        # download and use the latest ChromeDriver automatically using
        # Set up ChromeOptions for headless mode

        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get("https://www.google.com/")
        #driver = webdriver.Chrome(options=chrome_options) #
        #print("DRIVER:", driver)
        if request.method == 'POST':

            username_private = request.form.get('usernamePrivate')
            password = request.form.get('showdown_pw')
            gametype = request.form.get('gametype')
            driver=login_showdown(username_private, password, driver)            
            # time.sleep(3)
            print("DRIVER:", driver)
            print("User:", username_private)
            print("pass:", password)

            if driver is not None:

                # Deserialize the driver object from the request data
                #driver_serialized = data.get('driverData')
                #driver = json.loads(base64.b64decode(driver_serialized).decode('utf-8'))

            
                ## run the data gathering
                df1, df2, df_hero_indiv, df_villain_indiv, df3, df4, df5, df6 = sdg.get_metrics(username_private, gametype, driver, True)
                time.sleep(2)

                #update value of df1 in cache
                set_df1(df1)

                #driver.quit()
                #print(output)
                # hero individual plot
                hero_plotly = pyo.plot(sdg.get_individual_plot(df_hero_indiv), output_type="div")
                villain_plotly = pyo.plot(sdg.get_villain_indiv_plot(df_villain_indiv), output_type="div")
                
                #df with num_wins, num_games, win_rate
                overallStats = df2.to_html(index=False, classes='table table-responsive table-hover')
                num_games = str(df2.loc[0, 'num_games'])
                num_wins = str(df2.loc[0, 'num_wins'])
                win_rate = str(df2.loc[0, 'win_rate'])
                
                #dfs with individual hero pokemon winrates and elo scores
                df_hero_indiv = df_hero_indiv.reset_index()
                df_hero_indiv=df_hero_indiv.loc[:,["hero_pokemon","win_conditional","used_total","elo_score"]]
                df_hero_indiv.columns=['Hero Pokemon', "Games Won", "Games Played", "Weighted Win Rate"]
                # df_hero_indiv.to_csv("ind_stats.csv")
                df_hero_indiv["Weighted Win Rate"]=df_hero_indiv["Weighted Win Rate"].apply(lambda x: x+"%")
                df_hero_indiv.sort_values(by="Weighted Win Rate",ascending=False,inplace=True)
                hero_indiv_stats = df_hero_indiv.head(5).to_html(index=False)
                
                #dfs with individual villain pokemon loss rates and elo scores
                df_villain_indiv = df_villain_indiv.reset_index()
                df_villain_indiv=df_villain_indiv.loc[:,["villain_pokemon","loss_conditional","used_total","elo_score"]]
                df_villain_indiv.columns=['Villain Pokemon', "Games Lost Against", "Games Played Against", "Weighted Loss Rate"]
                # df_hero_indiv.to_csv("ind_stats.csv")
                df_villain_indiv["Weighted Loss Rate"]=df_villain_indiv["Weighted Loss Rate"].apply(lambda x: x+"%")
                df_villain_indiv.sort_values(by="Weighted Loss Rate",ascending=False,inplace=True)
                villain_indiv_stats = df_villain_indiv.head(5).to_html(index=False)
                
                #dfs with hero pairs, games and win rates breakdown 
                df3=df3.loc[:,["hero_one","hero_two","num_wins","num_games","elo_rate"]]
                df3.columns = ['Hero Lead 1', 'Hero Lead 2', "Games Won", "Games Played", "Weighted Win Rate"]
                df3.sort_values(by="Weighted Win Rate",ascending=False,inplace=True)
                df3["Weighted Win Rate"]=df3["Weighted Win Rate"].apply(lambda x: x+"%")
                heroPairStats = df3.head(5).to_html(index=False)
                
                ## villain pair stats
                df4=df4.loc[:,["villain_one","villain_two","num_losses","num_games","elo_rate"]]
                df4.columns = ['Villain Lead 1', 'Villain Lead 2', "Games Lost Against", "Games Played Against", "Weighted Loss Rate"]
                df4.sort_values(by="Weighted Loss Rate",ascending=False,inplace=True)
                df4["Weighted Loss Rate"]=df4["Weighted Loss Rate"].apply(lambda x: x+"%")
                villainPairStats = df4.head(5).to_html(index=False)
                
                ## hero comp stats
                df5=df5.loc[:,["hero_comp_fused","hero_comp_six","num_wins","num_games","elo_score"]]
                df5.columns = ["Hero Comp ID",'Hero Comp', 'Games Won', "Games Played", "Weighted Win Rate"]
                df5.sort_values(by="Weighted Win Rate",ascending=False,inplace=True)
                df5["Weighted Win Rate"]=df5["Weighted Win Rate"].apply(lambda x: x+"%")
                df5["Hero Comp ID"] = df5["Hero Comp ID"].apply(lambda x: f"<a href='/hero_comp_data/{x}'>Comp-Internal Data Link</a>") # trying
                sixTeamHeroStats = df5.head(5).to_html(index=False, escape=False)

                ## hero comp stats
                df6=df6.loc[:,["villain_comp_fused","villain_comp_six","num_losses","num_games","elo_score"]]
                df6.columns = ["Villain Comp ID", "Villain Comp","Games Lost Against", "Games Played Against", "Weighted Loss Rate"]
                df6.sort_values(by="Weighted Loss Rate",ascending=False,inplace=True)
                df6["Weighted Loss Rate"]=df6["Weighted Loss Rate"].apply(lambda x: x+"%")
                df6["Villain Comp ID"] = df6["Villain Comp ID"].apply(lambda x: f"<a href='/villain_comp_data/{x}'>Comp-Internal Data Link</a>")
                sixTeamVillainStats = df6.head(5).to_html(index=False, escape=False)

                # Define the CSS style for the table
                table_style = """
                <style>
                    table {
                        border-collapse: collapse;
                        width: 100%;
                        max-width: 800px;
                        margin: auto;
                        margin-bottom: 1em;
                    }
                    
                    th {
                        font-weight: bold;
                        text-align: left;
                        color: white;
                        background-color: #9d5bd9;
                        padding: 0.5em;
                    }
                    
                    tr:hover {
                        background-color: #a759d13f;
                    }
                    
                    td, th {
                        border: 1px solid #ddd;
                        padding: 0.5em;
                        text-align: left;
                    }
                    
                    @media (max-width: 768px) {
                        table {
                            font-size: 0.8em;
                        }
                        
                        th, td {
                            padding: 0.25em;
                        }
                    }
                </style>
                """

                driver.quit()
                # driver = None
                
                # katies original html creation
                output_html = Markup(table_style +"<h1 style='text-align: center;'>Top 5 Hero Pokemon</h1>" +
                                    "<br><br>" +
                                    hero_indiv_stats + 
                                    "<br><br>" +
                                    hero_plotly+ 
                                    "<br><br>" +
                                    "<h1 style='text-align: center;'>Top 5 Villain Pokemon</h1>" +
                                    "<br><br>" +
                                    villain_indiv_stats + 
                                    "<br><br>" +
                                    villain_plotly+ 
                                    "<br><br>" +
                                    "<h1 style='text-align: center;'>Top 5 Hero Comps</h1>"+
                                    "<br><br>" +
                                    sixTeamHeroStats+ 
                                    "<br><br>" +
                                    "<h1 style='text-align: center;'>Top 5 Villain Comps</h1>"+
                                    "<br><br>" +
                                    sixTeamVillainStats)

                #close pop-up after data is processed
                #driver.close()
                # Optional: If you need to store additional data in the session, you can do so here
                # For example, if you want to store the processed data in the session and retrieve it in another route

                # Clear the driver from the session to release resources
                #session.pop('driver', None)

                # Store the processed data in the session


                return render_template('resultsPrivateAndPublic.html', username = username_private, num_games=num_games, win_rate=win_rate, num_wins=num_wins, result = output_html)
        
            else:
                return 'Pop-up window not opened yet!'
        else:
            print("did not retrieve input")
            #return {'success': False}
            return render_template('index.html')



@app.route('/ip')
def ip():
    hostname = socket.gethostname()    
    IPAddr = socket.gethostbyname(hostname)
    d = {
        "hostname": hostname,
        "IPAddr": IPAddr,
    }   
    return jsonify(d)

# try to create linked htmls to hero comp identifiers
@app.route('/hero_comp_data/<comp_id>',methods=["GET","POST"])
def hero_comp_link(comp_id):
    #global df1

    #get df1 from the cache
    df1 = get_df1()

    ## make comp-specific match library
    hero_comp_library=sdg.get_hero_comp_library(comp_id, df1) # isolate to comp id relevant matches

    ## meta metrics for comp
    comp_meta=sdg.get_metametrics(hero_comp_library)
    overallStats = comp_meta.to_html(index=False, classes='table table-responsive table-hover')
    num_games = str(comp_meta.loc[0, 'num_games'])
    num_wins = str(comp_meta.loc[0, 'num_wins'])
    win_rate = str(comp_meta.loc[0, 'win_rate']) # change to percent

    # Define the CSS style for the table
    table_style = """
    <style>
        table {
            border-collapse: collapse;
            width: 100%;
            max-width: 800px;
            margin: auto;
            margin-bottom: 1em;
        }
        
        th {
            font-weight: bold;
            text-align: left;
            color: white;
            background-color: #9d5bd9;
            padding: 0.5em;
        }
        
        tr:hover {
            background-color: #a759d13f;
        }
        
        td, th {
            border: 1px solid #ddd;
            padding: 0.5em;
            text-align: left;
        }
        
        @media (max-width: 768px) {
            table {
                font-size: 0.8em;
            }
            
            th, td {
                padding: 0.25em;
            }
        }
    </style>
    """

    ## individual pokemon stats
    df_hero_indiv=sdg.get_individual_rates(hero_comp_library)
    hero_plotly = pyo.plot(sdg.get_individual_plot(df_hero_indiv), output_type="div")
    # print(df_hero_indiv)
    output_html = Markup(table_style +"<h3 style='text-align: center;'><strong>Hero Comp ID:</strong> {}</h3>".format(comp_id) +
                    "<br><br>" +
                    hero_plotly+ 
                    "<br><br>" )
    return render_template("hero_comp_data.html", num_games=num_games, win_rate=win_rate, num_wins=num_wins, result = output_html)

# try to create linked htmls to villain comp identifiers
@app.route('/villain_comp_data/<comp_id>',methods=["GET","POST"])
def villain_comp_link(comp_id):
    #global df1

    #get df1 from the cache
    df1 = get_df1()



    ## make comp-specific match library
    villain_comp_library=sdg.get_villain_comp_library(comp_id, df1) # isolate to comp id relevant matches

    ## meta metrics for comp
    comp_meta=sdg.get_meta_losses(villain_comp_library)
    overallStats = comp_meta.to_html(index=False, classes='table table-responsive table-hover')
    num_games = str(comp_meta.loc[0, 'num_games'])
    num_losses = str(comp_meta.loc[0, 'num_losses'])
    loss_rate = str(comp_meta.loc[0, 'loss_rate']) # change to percent

    # Define the CSS style for the table
    table_style = """
    <style>
        table {
            border-collapse: collapse;
            width: 100%;
            max-width: 800px;
            margin: auto;
            margin-bottom: 1em;
        }
        
        th {
            font-weight: bold;
            text-align: left;
            color: white;
            background-color: #9d5bd9;
            padding: 0.5em;
        }
        
        tr:hover {
            background-color: #a759d13f;
        }
        
        td, th {
            border: 1px solid #ddd;
            padding: 0.5em;
            text-align: left;
        }
        
        @media (max-width: 768px) {
            table {
                font-size: 0.8em;
            }
            
            th, td {
                padding: 0.25em;
            }
        }
    </style>
    """

    ## individual pokemon stats
    df_villain_indiv=sdg.get_villain_indiv_rates(villain_comp_library)
    villain_plotly = pyo.plot(sdg.get_villain_indiv_plot(df_villain_indiv), output_type="div")
    # print(df_hero_indiv)
    output_html = Markup(table_style +"<h3 style='text-align: center;'><strong>Villain Comp ID:</strong> {} </h3>".format(comp_id) +
                    "<br><br>" +
                    villain_plotly+ 
                    "<br><br>" )
    return render_template("villain_comp_data.html", num_games=num_games, loss_rate=loss_rate, num_losses=num_losses, result = output_html)


@app.route('/test-mysql-db-connection')
def test_db_connection():
    try:
        # google sql cloud database -- ip whitelisting test for heroku app
        from mysql.connector import connect
        cnx = connect(
            host='35.238.34.27',
            database='demo',
            user='nivratti',
            password='nivpoijkldfghcc@@', 
            port=3306
        )
        d = {
            "success": True,
            "message": "Connected to database successfully",
        }
    except Exception as e:
        d = {
            "success": False,
            "message": str(e),
        }
    return jsonify(d)

if __name__ == '__main__':

    app.run(host="0.0.0.0", debug=True)
