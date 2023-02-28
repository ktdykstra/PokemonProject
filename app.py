from flask import Flask, render_template
from flask import jsonify
from flask_bootstrap import Bootstrap
import pandas as pd
import socket 
import pickle

#matchdata = pd.read_csv('')
app = Flask(__name__)

# two decorators, same function
@app.route('/')

@app.route('/index.html')
def index():
    return render_template('index.html', the_title='Home Page')

@app.route("/username", methods=['GET','POST'])
def predict():
    return render_template('index.html', the_title='Home Page')
    if request.method == 'POST':
        #access the data from form
        ## Username
        user = int(request.form["username"])
        gametype = int(request.form["gametype"])
        #get stats
        #stats = model.predict(input_cols)
        #run_all_steps_metrics(user, gametype)!!!!!!!!
        output = round(prediction[0], 2)
        return render_template("home.html", prediction_text='Your predicted annual Healthcare Expense is $ {}'.format(output))

@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(matchdata.to_dict(orient='records'))

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
