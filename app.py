from flask import Flask, redirect, render_template, request, url_for
from flask import jsonify
from flask_bootstrap import Bootstrap
from markupsafe import Markup
import pandas as pd
import poke_backend_v2 as sdg
import socket 
import pickle

app = Flask(__name__)


@app.route('/')
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
            df1, df2, df_individual, df3, df4, df5, df6 = sdg.get_metrics(username, gametype)
            #print(output)
            
            #df with num_wins, num_games, win_rate
            overallStats = df2.to_html(index=False, classes='table table-responsive table-hover')
            num_games = str(df2.loc[0, 'num_games'])
            num_wins = str(df2.loc[0, 'num_wins'])
            win_rate = str(df2.loc[0, 'win_rate'])

            #dfs with hero pairs, games and win rates breakdown 
            df3 = df3.iloc[:, -5:]
            cols = df3.columns.tolist()
            cols = cols[-2:] + cols[:-2]
            df3 = df3[cols]
            df3.columns = ['Hero #1', 'Hero #2', "Wins", "Games", "Pair Win Rate"]
            heroStats = df3.to_html(index=False)
            
            df4 = df4.iloc[:, -5:]
            cols = df4.columns.tolist()
            cols = cols[-2:] + cols[:-2]
            df4 = df4[cols]
            df4.columns = ['Villain #1', 'Villain #2', "Losses", "Games", "Pair Loss Rate"]
            villainStats = df4.to_html(index=False)
            
            
            df5 = df5.iloc[:, 1:5]
            df5.columns = ['Ordered Hero Team', 'Wins', "Games", "Win Rate"]
            sixTeamHeroStats = df5.to_html(index=False)
            

            df6 = df6.iloc[:, 1:5]
            df6.columns = ['Ordered Villain Team', 'Losses', "Games", "Loss Rate"]
            sixTeamVillainStats = df6.to_html(index=False)

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

            output_html = Markup(table_style + heroStats+ "<br><br>" +villainStats+ "<br><br>" +sixTeamHeroStats+ "<br><br>" +sixTeamVillainStats)

            return render_template('results.html', username = username, num_games=num_games, win_rate=win_rate, num_wins=num_wins, result = output_html)
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
