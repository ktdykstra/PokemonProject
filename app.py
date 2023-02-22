from flask import Flask, render_template
from flask import jsonify
import socket 
import pickle

app = Flask(__name__)

# two decorators, same function
@app.route('/')
@app.route('/home.html')
def home():
    return render_template('home.html', the_title='Home Page')

@app.route("/predict", methods=['GET','POST'])
def predict():
    return render_template("home.html")
    if request.method == 'POST':
        #access the data from form
        ## Age
        age = int(request.form["age"])
        bmi = int(request.form["bmi"])
        children = int(request.form["children"])
        Sex = int(request.form["Sex"])
        Smoker = int(request.form["Smoker"])
        Region = int(request.form["Region"])
        #get prediction
        input_cols = [[age, bmi, children, Sex, Smoker, Region]]
        prediction = model.predict(input_cols)
        output = round(prediction[0], 2)
        return render_template("home.html", prediction_text='Your predicted annual Healthcare Expense is $ {}'.format(output))

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
