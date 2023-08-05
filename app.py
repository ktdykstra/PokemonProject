from flask import Flask, redirect, render_template, request, url_for, session
from flask import jsonify
import os
import time
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
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from requests.adapters import BaseAdapter
from requests.sessions import Session
# bring in dash_app
#from dash_app import create_dash

## global variables
browser_type = "Unclear"
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
        driver=webdriver.Chrome()
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
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            driver = webdriver.Chrome(options=chrome_options)

            #driver=cookie_collecter(driver)
            df1, df2, df_hero_indiv, df_villain_indiv, df3, df4, df5, df6 = sdg.get_metrics(username, gametype, driver, False)
            driver.quit()
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

#get driver from pop up
@app.route('/get_driver', methods=['GET'])
def get_driver():
    # Retrieve the driver object from the session
    driver_serialized = session.get('driver')

    if driver_serialized is None:
        # Handle the case when the driver is not present in the session
        return jsonify({'error': 'Driver not found in the session'})

    # Deserialize the driver object
    try:
        driver = pickle.loads(driver_serialized.encode('latin1'))
    except Exception as e:
        # Handle errors during deserialization
        return jsonify({'error': 'Failed to deserialize the driver object'})

    # Serialize the driver again and send it back to the client
    serialized_driver = pickle.dumps(driver).decode('latin1')
    return jsonify({'driver': serialized_driver})

#opening the pop-up for private replay data login
@app.route('/open_popup', methods=['POST'])
def open_popup():
    global user_interaction_complete
    # OPEN SHOWDOWN LOGIN
    # browser_type=get_browser()
    # driver=open_login_tab(browser_type) # builds initial driver
    driver = webdriver.Chrome()
    
    driver=cookie_collecter(driver) # takes user to login page via driver
    # custom_session = create_custom_session(driver)

    # Set user_interaction_complete to False at the beginning of interaction
    user_interaction_complete = False

    driver.session_id  # Get the session ID

    # Store the session ID in the session
    session['driver_session_id'] = driver.session_id
    

    # Return a JSON response to the AJAX call to indicate success
    return jsonify({'status': 'success'})

# Function to handle user interaction in the Selenium browser
def handle_user_interaction():
    global user_interaction_complete
    while not user_interaction_complete:
        try:
            # Check if user interaction is complete (e.g., buttons are clickable)
            # Modify this part based on your specific website and user interaction requirements
            # For example, you can use WebDriverWait to wait for elements to be clickable.
            # Example: button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, 'button_name')))
            # If user interaction is detected, set user_interaction_complete to True

            # For demonstration purposes, we use a simple input() function here to simulate user input.
            # In your actual implementation, you should replace this with your specific user interaction checks.
            user_input = input("Enter 'done' when user interaction is complete: ")
            if user_input.lower() == 'done':
                user_interaction_complete = True
        except Exception as e:
            print("Error during user interaction check:", e)
            # Handle any exceptions during the interaction check

# Function to notify the server when the user has completed the interaction
@app.route('/user_interaction_complete', methods=['POST'])
def user_interaction_complete_route():
    global user_interaction_complete
    # Set user_interaction_complete to True when the AJAX request is received
    user_interaction_complete = True
    return jsonify({'status': 'success'})

#function for retrieving analytics on private & public replays 
@app.route("/get_data_private", methods=['GET','POST'])
def get_data_private():
        global user_interaction_complete

        # Check if the user has completed the interaction
        if not user_interaction_complete:
            # If the user has not completed the interaction, return an error response or do nothing
            return jsonify({'error': 'User interaction not complete'})

        if request.method == 'POST':
            # Retrieve the driver session ID from the session
            driver_session_id = session.get('driver_session_id')

            if driver_session_id is None:
                # Handle the case when the driver session ID is not present in the session
                return jsonify({'error': 'Driver session ID not found in the session'})

            # Use the driver_session_id to connect to the existing Selenium driver
            driver = webdriver.Remote(command_executor='http://127.0.0.1:4444/wd/hub', desired_capabilities={})
            driver.session_id = driver_session_id

            # Retrieve the driver data from the request JSON
            form_data = request.json

            # ... Process the form data and other actions on the server-side ...
            # Get the form data from the AJAX request
            username = form_data.get("usernamePrivate")
            gametype = form_data.get("gametype")

            # Construct the response data
            response_data = {
                'success': True,  # Add any relevant success flag or data here
                'message': 'Form data successfully processed.',
                'additional_data': 'You can include any additional data you want to send back to the client.'
            }

           
            ## run the data gathering
            df1, df2, df_hero_indiv, df_villain_indiv, df3, df4, df5, df6 = sdg.get_metrics(username, gametype, driver, True)
            driver.quit()
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

            #close pop-up after data is processed
            driver.close()
            # Optional: If you need to store additional data in the session, you can do so here
            # For example, if you want to store the processed data in the session and retrieve it in another route

            # Clear the driver from the session to release resources
            session.pop('driver', None)

            return render_template('resultsPrivateAndPublic.html', data=response_data, username = username, num_games=num_games, win_rate=win_rate, num_wins=num_wins, result = output_html)
        else:
            print("did not retrieve input")
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
