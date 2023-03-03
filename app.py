from flask import Flask, render_template, request
from flask import jsonify
from flask_bootstrap import Bootstrap
import pandas as pd
import showdown_data_gathering as sdg
import socket 
import pickle

app = Flask(__name__)

# two decorators, same function
@app.route('/')

@app.route('/index.html', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
            #access the data from form
            ## Username
            username = request.form["username"]
            gametype = request.form["gametype"]
            print(username)
            print(gametype)
            output = sdg.run_all_steps_metrics(username, gametype)
            print(output)
            return render_template("index.html", result=output)
    else:
        return render_template('index.html', the_title='Home Page')

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
            output = sdg.run_all_steps_metrics(username, gametype)
            print(output)
            return render_template("index.html", result=output)
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
