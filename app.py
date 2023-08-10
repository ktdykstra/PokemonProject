from flask import Flask, redirect, render_template, request, url_for, session
from flask_caching import Cache
import redis 
import certifi
import ssl
import requests
from flask_oauthlib.client import OAuthException

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

from flask_oauthlib.client import OAuth

from requests.adapters import BaseAdapter
from requests.sessions import Session

from flask_session import Session
import sqlite3
from flask import g, flash 
import stripe
from stripe.error import SignatureVerificationError

# IMPORT DB functionality from database.py
from database import connect_to_db, close_connection, DatabaseHandler
import psycopg2


#for testing:
#sample_username="Broskander" 
#sample_game_type="gen9vgc2023series1"


## global variables
browser_type = "Unclear"
df1=None

app = Flask(__name__)
app.debug=True

#initialize session
app.config.from_object(__name__)

# Use Stackhero Redis as the session backend
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

# The Redis connection details
redis_host = 'qoxjxb.stackhero-network.com'
redis_port = '6380'
redis_password = '2SSlD7FN0buUpMoGeb4iR2eKf8vJ87GDm67hq6LEiQK6IloP3X01WFbCTfhiU0h8'

# Create a Redis connection using redis.StrictRedis
redis_connection = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, ssl=True)

# Set the Redis connection object as SESSION_REDIS
app.config['SESSION_REDIS'] = redis_connection

#DB URL
app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL')

app.secret_key = os.environ.get('FLASK_SECRET_KEY')

stripe.api_key = 'sk_test_51NchgQDypgtvgAYhWbgnSjTEd9fyiHx0gXeXRbwOLZwAWnm9Nqy1nV14lvaK2e3O46YSL1zeaQoh9lrSCmO9yP7J002sx3FOfN'

# This is your Stripe CLI webhook secret for testing your endpoint locally.
endpoint_secret = 'whsec_y8g6j902YUMrBD7HoeETzGHeF39prUqs'

PREMIUM_PRICE_ID = 'price_1NchwKDypgtvgAYhILRJc3RP'
STANDARD_PRICE_ID = 'price_1NchuvDypgtvgAYhETrGiaoo'

Session(app)


####################################################
# OAUTH CONFIG
####################################################
oauth = OAuth(app)
client_id = os.environ.get('OAUTH_CLIENT_ID')
client_secret = os.environ.get('OAUTH_CLIENT_SECRET')

google = oauth.remote_app(
    'google',
    consumer_key='112552042731-92ta2f95bd7s9hpk9po29t4k97lthemv.apps.googleusercontent.com',  # client ID
    consumer_secret='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',  # client secret
    request_token_params={
        'scope': 'email',
    },
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)



####################################################
# SETTING UP CACHE
####################################################

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

####################################################
# CONFIGURE DATABASE
####################################################
# Initialize the DatabaseHandler
# db_handler = DatabaseHandler()

def get_db():
    return connect_to_db()

#called automatically at end of each request :)
#@app.teardown_appcontext
#def close_db(error):
#    db_handler.close_connection()

## handling INSERT, UPDATE, or DELETE queries
def CUD_query(query, db, cursor):
    try:
        cursor.execute(query)
        db.commit()
        print("Successful query!")
    except Exception as e:
        db.rollback()
        print("Error:", e)
    return

####################################################
# FUNCTIONS FOR USER PROFILES IN OUR DATABASE
####################################################

# view all data in user table
def view_user_data():
    db, cursor = get_db() # open db
    try:
        cursor.execute("SELECT * FROM serapis_schema.serapis_users;")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
        close_connection(db, cursor) # close db
        return rows
    except Exception as e:
        close_connection(db, cursor) # close db
        print("Unable to view data. Error:", e)
        return

## adds entry to the serapis_schema.serapis_users table
def create_user(user_email, subscription_status='free', click_count=0, stripe_customer_id=''):
    db, cursor = get_db() # open db
    try:
        # check if user exists
        cursor.execute('SELECT email FROM serapis_schema.serapis_users WHERE email = %s', (user_email,))
        existing_email = cursor.fetchone()
        print(existing_email)
        if existing_email:
            print(f"User with email {user_email} already exists.")
            close_connection(db, cursor)  # Close db
            return
        
        # continue with entry
        cursor.execute('INSERT INTO serapis_schema.serapis_users (email, subscription_status, click_count, stripe_customer_id) VALUES (%s, %s, %s, %s)',
                   (user_email, subscription_status, click_count, stripe_customer_id))
        db.commit()
        print("Successful query! User created: {user_email}")
    except Exception as e:
        db.rollback()
        print("Unable to create user. Error:", e)
    close_connection(db, cursor) # close db
    return

## get individual user info filtering by email
def get_user_by_email(user_email):
    db, cursor = get_db()
    try:
        cursor.execute('SELECT * FROM serapis_schema.serapis_users WHERE email = %s', (user_email,))
        result = cursor.fetchone()  # Fetch a single row
        close_connection(db, cursor) # close db
        print("Good query")
        return result
    except Exception as e:
        close_connection(db, cursor)
        print("Unable to get user. Error:",e)
        return

## update clicks
def increment_click_count(user_email):
    db, cursor = get_db()
    try:
        cursor.execute('UPDATE serapis_schema.serapis_users SET click_count = click_count + 1 WHERE email = %s', (user_email,))
        db.commit()
        close_connection(db,cursor) # close db
        print(f'Click count incremented: {user_email}')
    except Exception as e:
         db.rollback()
         close_connection(db,cursor) # close db
         print("Unable to update click count. Error:",e)

## update stripe customer ID
def update_stripe_customer_id(user_email, stripe_customer_id):
    db, cursor = get_db()
    try:
        cursor.execute('UPDATE serapis_schema.serapis_users SET stripe_customer_id = %s WHERE email = %s', (stripe_customer_id, user_email))
        db.commit()
        close_connection(db,cursor) # close db
        print(f'Stripe ID updated to {stripe_customer_id} for user: {user_email}')
    except Exception as e:
        db.rollback()
        close_connection(db,cursor) # close db
        print(f"Unable to update Stripe ID for user: {user_email}. Error:",e)

####################################################
# SUBSCRIPTION UPDATE FUNCTIONS
####################################################
# Function to get user's subscription status from the database
def get_subscription_status(user_email):
    db, cursor = get_db()
    try:
        cursor.execute('SELECT subscription_status FROM serapis_schema.serapis_users WHERE email = %s', (user_email,))
        result = cursor.fetchone()
        close_connection(db, cursor) # close db
        print(f"Found subscription status as {result} for user: {user_email}")
        return result[0]
    except Exception as e:
        close_connection(db, cursor)
        print(f"Unable to get subscription status for user: {user_email}. Error:",e)
        return

# Function to get user's stripe customer id status from the database
def get_customer_id_from_email(user_email):
    db, cursor = get_db()
    try:
        cursor.execute('SELECT stripe_customer_id FROM serapis_schema.serapis_users WHERE email = %s', (user_email,))
        result = cursor.fetchone()
        close_connection(db, cursor) # close db
        print(f"Found stripe customer id as {result} for user: {user_email}")
        return result[0]
    except Exception as e:
        close_connection(db, cursor)
        print(f"Unable to get stripe customer id for user: {user_email}. Error:",e)
        return

## updating stripe customer id for first-time subscriber
def new_customer_id(user_email, new_customer_id):
    db, cursor = get_db()
    try:
        cursor.execute('UPDATE serapis_schema.serapis_users SET stripe_customer_id = %s WHERE email = %s', (new_customer_id, user_email))
        db.commit()
        close_connection(db,cursor) # close db
        print(f'Stripe customer ID status added as {new_customer_id} for user with email: {user_email}')
    except Exception as e:
        db.rollback()
        close_connection(db,cursor) # close db
        print(f"Unable to create stripe customer ID for customer: {user_email}. Error:",e)
    return

## for updating subscriptions once stripe customer id exists
def update_subscription_and_customer_id(stripe_customer_id, new_status):
    db, cursor = get_db()
    try:
        cursor.execute('UPDATE serapis_schema.serapis_users SET subscription_status = %s WHERE stripe_customer_id = %s', (new_status, stripe_customer_id))
        db.commit()
        close_connection(db,cursor) # close db
        print(f'Subscription status updated to {new_status} for user with stripe id: {stripe_customer_id}')
    except Exception as e:
        db.rollback()
        close_connection(db,cursor) # close db
        print(f"Unable to update subscription status for stripe customer: {stripe_customer_id}. Error:",e)
    # # Update subscription status AND stripe customer id IFF stripe customer id is ""
    # if stripe_customer_id =="":

    # db, cursor = get_db()
    # try:

    # cursor.execute('UPDATE serapis_schema.serapis_users SET subscription_status = %s, stripe_customer_id = %s WHERE stripe_customer_id = %s',
    #            (new_subscription_status, customer_id, customer_id))
    # db.commit()

# def update_subscription_status(stripe_customer_id, new_status):
#     db, cursor = get_db()
#     try:
#         cursor.execute('UPDATE serapis_schema.serapis_users SET subscription_status = %s WHERE stripe_customer_id = %s', (new_status, stripe_customer_id))
#         db.commit()
#         close_connection(db,cursor) # close db
#         print(f'Subscription status updated to {new_status} for user with stripe id: {stripe_customer_id}')
#     except Exception as e:
#         db.rollback()
#         close_connection(db,cursor) # close db
#         print(f"Unable to update subscription status for stripe customer: {stripe_customer_id}. Error:",e)
    

####################################################
# STRIPE WEBHOOK LISTENERS
####################################################
@app.route('/stripe/webhook', methods=['POST'])
def webhook():
    event = None
    payload = request.data
    sig_header = request.headers['STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise e

    # Update subscription if stripe payment succeeds
    if event['type'] == 'invoice.payment_succeeded':
        # Extract relevant information from the event
        subscription_id = event['data']['object']['subscription']
        customer_id = event['data']['object']['customer']
        customer_email = event['data']['object']['customer_details']['email']
        update_stripe_customer_id(customer_email, customer_id)
        subscription = stripe.Subscription.retrieve(subscription_id)

        # Determine the new subscription status based on the subscription type
        if subscription.items.data[0].price.id == PREMIUM_PRICE_ID:
            new_subscription_status = 'premium'
        elif subscription.items.data[0].price.id == STANDARD_PRICE_ID:
            new_subscription_status = 'standard'

        # Update the user's subscription status in the database
        update_subscription_and_customer_id(customer_id, new_subscription_status)

    # If a user cancels
    elif event['type'] == 'subscription_schedule.canceled':
        subscription_schedule_id = event['data']['object']['id']
        customer_id = event['data']['object']['customer']
        
        # Update the user's subscription status in the database to reflect cancellation
        update_subscription_and_customer_id(customer_id, 'canceled')

    #user deletes subscription
    elif event['type'] == 'customer.subscription.deleted':
        subscription_id = event['data']['object']['id']
        customer_id = event['data']['object']['customer']
        
        # Update the user's subscription status in the database to reflect subscription deletion
        update_subscription_and_customer_id(customer_id, 'deleted')

    elif event['type'] == 'checkout.session.async_payment_succeeded':
        # Handle checkout.session.async_payment_succeeded event
        handle_checkout_session_async_payment_succeeded(event)

    elif event['type'] == 'checkout.session.completed':
        # Handle checkout.session.completed event
        handle_checkout_session_completed(event)

    elif event['type'] == 'customer.subscription.paused':
        # Handle customer.subscription.paused event
        handle_subscription_paused(event)

    elif event['type'] == 'customer.subscription.resumed':
        # Handle customer.subscription.resumed event
        handle_subscription_resumed(event)

    elif event['type'] == 'invoice.payment_succeeded':
        # Handle invoice.payment_succeeded event
        handle_invoice_payment_succeeded(event)

    elif event['type'] == 'plan.updated':
        # Handle plan.updated event
        handle_plan_updated(event)

    # ... handle other event types
    else:
      print('Unhandled event type {}'.format(event['type']))

    return jsonify(success=True)

## FXNS TO HANDLE WEBHOOK EVENT TYPES

def handle_checkout_session_async_payment_succeeded(event):
    # Handle checkout.session.async_payment_succeeded event
    # Extract relevant information from the event
    subscription_id = event['data']['object']['subscription']
    customer_id = event['data']['object']['customer']
    subscription = stripe.Subscription.retrieve(subscription_id)
    customer_email = event['data']['object']['customer_details']['email']
    update_stripe_customer_id(customer_email, customer_id)

    # Determine the new subscription status based on the subscription type (replace with your logic)
    if subscription.items.data[0].price.id == PREMIUM_PRICE_ID:
            new_subscription_status = 'premium'
    elif subscription.items.data[0].price.id == STANDARD_PRICE_ID:
        new_subscription_status = 'standard'

    # Update the user's subscription status and customer ID in the database
    update_subscription_and_customer_id(customer_id, new_subscription_status)


def handle_checkout_session_completed(event):
    # Handle checkout.session.completed event
    # Extract relevant information from the event
    customer_id = event['data']['object']['customer']
    subscription_id = event['data']['object']['subscription']
    subscription = stripe.Subscription.retrieve(subscription_id)
    customer_email = event['data']['object']['customer_details']['email']
    update_stripe_customer_id(customer_email, customer_id)

    # Determine the new subscription status based on the subscription type
    if subscription.items.data[0].price.id == PREMIUM_PRICE_ID:
        new_subscription_status = 'premium'
    elif subscription.items.data[0].price.id == STANDARD_PRICE_ID:
        new_subscription_status = 'standard'
    else:
        new_subscription_status = 'free'  # Or handle other subscription cases

    # Update the subscription status and customer ID in your database
    update_subscription_and_customer_id(customer_id, new_subscription_status)


def handle_subscription_paused(event):
    # Handle customer.subscription.paused event
    customer_id = event['data']['object']['customer']
    update_subscription_and_customer_id(customer_id, 'paused')


def handle_subscription_resumed(event):
    # Handle customer.subscription.resumed event
    customer_id = event['data']['object']['customer']
    update_subscription_and_customer_id(customer_id, 'resumed')


def handle_invoice_payment_succeeded(event):
    # Handle invoice.payment_succeeded event
    customer_id = event['data']['object']['customer']
    subscription_id = event['data']['object']['subscription']
    subscription = stripe.Subscription.retrieve(subscription_id)
    
    # Determine the new subscription status based on the subscription type
    if subscription.items.data[0].price.id == PREMIUM_PRICE_ID:
        new_subscription_status = 'premium'
    elif subscription.items.data[0].price.id == STANDARD_PRICE_ID:
        new_subscription_status = 'standard'
    else:
        new_subscription_status = 'free'  # Or handle other subscription cases
    
    update_subscription_and_customer_id(customer_id, new_subscription_status)


def handle_plan_updated(event):
    # try:
    #     user = get_user_by_email(user_email)
    #     if not user or not user[3]:
    #         return False

    #     # Set the Stripe API key
    #     stripe.api_key = 'sk_test_51NchgQDypgtvgAYhWbgnSjTEd9fyiHx0gXeXRbwOLZwAWnm9Nqy1nV14lvaK2e3O46YSL1zeaQoh9lrSCmO9yP7J002sx3FOfN'

    #     # Get the customer from Stripe
    #     customer = stripe.Customer.retrieve(user[3])

    #     # Find the IDs of the old and new subscription plans
    #     old_subscription_id = customer.subscriptions.data[0].id
    #     if new_subscription_type == 'premium':
    #         new_subscription_price_id = PREMIUM_PRICE_ID
    #     elif new_subscription_type == 'standard':
    #         new_subscription_price_id = STANDARD_PRICE_ID

    #     # Update the subscription plan
    #     customer.subscriptions.modify(
    #         old_subscription_id,
    #         items=[{
    #             'id': customer.subscriptions.data[0].items.data[0].id,
    #             'price': new_subscription_price_id,
    #         }],
    #     )
    #     return
    # except stripe.error.StripeError:
    #     print("Error in subscription adjustment for this subscriber in Stripe")
    #     return
    pass

####################################################
# ROUTES FOR Google Login and Callback 
####################################################
#Protect Pages from unauthenticated users
@app.before_request
def check_authentication():
    # List of routes that do not require authentication
    public_routes = ['/', 'login', 'privacy', 'authorized', 'ads.txt', 'pricing']

    # If the requested route is public, allow access without authentication
    if request.endpoint in public_routes or request.endpoint == '/':
        return

    # Check if the session identifier is present and the user is authenticated
    if 'user_authenticated' not in session or not session['user_authenticated']:
        # Redirect to the login page or display an access denied message
        return redirect('/login')

@app.route('/login')
def login():
    # Check if the user is already authenticated (optional)
    #if 'user_authenticated' in session and session['user_authenticated']:
    #return redirect('/infoForm')

     # If not authenticated, initiate Google OAuth authentication
     #http://127.0.0.1:5000
    return google.authorize(callback=url_for('authorized', _external=True))


def verify_google_access_token(access_token):
    # Make a request to Google's token validation endpoint
    url = f'https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={access_token}'
    response = requests.get(url)
    if response.status_code != 200:
        # Handle invalid response from the validation endpoint
        return None

    token_info = response.json()

    if 'error' in token_info:
        # Handle token validation error
        return None

    return token_info

@app.route('/login/authorized')
def authorized():
    resp = google.authorized_response()

    if resp is None or resp.get('access_token') is None:
        return 'Access denied: reason={} error={}'.format(
            request.args['error_reason'],
            request.args['error_description']
        )

    # Verify the access token with Google's token validation endpoint
    access_token = resp['access_token']
    token_info = verify_google_access_token(access_token)

    if not token_info or 'error' in token_info:
        # If the token validation fails or the token is expired, clear session data
        session.clear()
        return 'Token validation failed or expired. Please log in again.'

    # Authentication successful, set the session flag to indicate user is authenticated
    session['user_authenticated'] = True

    # Fetch user email address from Google API using the access token
    email = get_google_user_email(access_token)

    # Store user email address in session
    session['user_email'] = email

    ## ADD USER TO DATABASE
    # Check if the user already exists in your database
    user = get_user_by_email(email)
    if user is None:
        # If the user doesn't exist, create a new user profile
        create_user(email)  # Call the create_user function

    # Save the access_token in the session (optional, useful for future API calls)
    session['access_token'] = resp['access_token']

    return redirect('/infoForm')


def verify_google_access_token(access_token):
    # Make a request to Google's token validation endpoint
    url = f'https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={access_token}'
    response = requests.get(url)
    if response.status_code != 200:
        # Handle invalid response from the validation endpoint
        return None
    return response.json()



def get_google_user_email(access_token):
    # Make a request to Google's userinfo endpoint to get user information
    headers = {'Authorization': f'Bearer {access_token}'}
    url = 'https://www.googleapis.com/oauth2/v3/userinfo'
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        # Handle error response from the userinfo endpoint
        return None

    user_info = response.json()
    return user_info.get('email')


####################################################
# LOGOUT FUNCTIONALITY
####################################################
def clear_user_cache():
    # Retrieve the user email and showdown username from the session
    user_email = session.get('user_email')
    showdown_username = session.get('showdown_username')

    if user_email is not None and showdown_username is not None:
        # Construct the cache key using the user's email and showdown username
        cache_key = f'user_df:{user_email}:{showdown_username}'
        # Delete the cache entry
        redis_client.delete(cache_key)

@app.route('/logout')
def logout():
    # Clear the user's cache
    clear_user_cache()
    
    # Clear session data to log the user out
    session.clear()
    return redirect(url_for('login'))

####################################################
# FXNS FOR STORING DF1 IN CACHE 
####################################################
'''
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

    '''

# setting up code for concurrent sessions, need to wait for account management
def get_user_df1():
    # Retrieve the user email from the session
    user_email = session.get('user_email')
    showdown_username = session.get('showdown_username')

    if user_email is None or showdown_username is None:
        return None

    cache_key = f'user_df:{user_email}:{showdown_username}' # Use the user's email in the cache key
    df_bytes = redis_client.get(cache_key)
    if df_bytes is not None:
        df = pickle.loads(df_bytes)
        return df
    else:
        return None


def set_user_df1(df1):
    # Retrieve the user email from the session
    user_email = session.get('user_email')
    showdown_username = session.get('showdown_username')

    if user_email is not None or showdown_username is None:
        cache_key = f'user_df:{user_email}:{showdown_username}'  # Use the user's email in the cache key
        df_bytes = pickle.dumps(df1)
        redis_client.set(cache_key, df_bytes)



####################################################
# Get the browser type of flask session
####################################################

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

####################################################
# Generate webdriver depending on browser type
####################################################
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
    time.sleep(30)

    return driver

#Route for login button
@app.route('/')
def login_OAuth():
    return render_template('loginOAuth.html')

@app.route('/infoForm')
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

############################################################
# RENDER THE MAIN PAGE
############################################################
@app.route('/main')
def index():
    #submitted = request.args.get('submitted')
    if 'user_email' in session:
        user = get_user_by_email(session['user_email'])
        return render_template('index.html', user=user)
    return render_template('index.html')

############################################################
# RENDER THE PRIVACY POLICY
############################################################
@app.route('/privacy')
def privPol():
    return render_template('PrivacyPolicy.html')

############################################################
# RENDER THE GOOGLE ADS TEXT
############################################################
@app.route('/ads.txt')
def ads():
    return render_template('ads.txt')

############################################################
#
# PROCESSING PUBLICLY AVAILABLE MATCHES ONLY
#
############################################################
@app.route("/get_data", methods=['GET','POST'])
@cache.cached(timeout=60)
def get_data():
        global driver
        #global df1
        
        service = Service(ChromeDriverManager().install())
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")

        # download and use the latest ChromeDriver automatically using
        # Set up ChromeOptions for headless mode
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get("https://www.google.com/")

        ## INCREMENT CLICK COUNT IN DB FOR USER
        increment_click_count(session['user_email'])

        #print("DRIVER:", driver)
        if request.method == 'POST':
            # METERED PAYWALL LOGIC
            if 'user_email' in session:
                user = get_user_by_email(session['user_email'])
                if user[1] == 'premium' or user[1] == 'standard' or user[2] < 6:
                    username = request.form.get('username')
                    gametype = request.form.get('gametype')

                    #UPDATE USERNAME IN SESSION
                    session['showdown_username'] = username

                    if driver is not None:
                        ## run the data gathering. all_matches == False 
                        df1, df2, df_hero_indiv, df_villain_indiv, df3, df4, df5, df6 = sdg.get_metrics(username, gametype, driver, False)
                        time.sleep(2)

                        #update value of df1 in cache
                        set_user_df1(df1)

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

                        return render_template('resultsPrivateAndPublic.html', username = username, num_games=num_games, win_rate=win_rate, num_wins=num_wins, result = output_html)
                
                    else:
                        return 'Pop-up window not opened yet!'
                else:
                    flash('Please subscribe to access more content.')
                    return redirect(url_for('pricing'))  # Redirect to the subscription page
            else:
                flash('Please log in to access content.')
                return redirect(url_for('login'))  # Redirect to the login page
        else:
            print("did not retrieve input")
            return render_template('index.html')

############################################################
# LOGIN TO PS! WITH SELENIUM
############################################################
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

############################################################
#
# RETRIVE PUBLIC AND PRIVATE MATCHES
#
############################################################
@app.route("/get_data_private", methods=['GET','POST'])
@cache.cached(timeout=60)
def get_data_private():
        global driver
        #global df1

        # Set up the Chrome WebDriver in headless mode
        service = Service(ChromeDriverManager().install())
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")

        # download and use the latest ChromeDriver automatically using
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get("https://www.google.com/")

        ## INCREMENT CLICK COUNT IN DB FOR USER
        increment_click_count(session['user_email'])

        if request.method == 'POST':

            # METERED PAYWALL LOGIC
            if 'user_email' in session:
                user = get_user_by_email(session['user_email'])
                if user[1] == 'premium' or user[1] == 'standard' or user[2] < 6:

                    username_private = request.form.get('usernamePrivate')
                    password = request.form.get('showdown_pw')
                    gametype = request.form.get('gametype')
                    driver=login_showdown(username_private, password, driver)            
                    # time.sleep(3)
                    print("DRIVER:", driver)
                    print("User:", username_private)
                    print("pass:", password)

                    #UPDATE USERNAME IN SESSION
                    session['showdown_username'] = username_private

                    if driver is not None:
                        ## run the data gathering
                        df1, df2, df_hero_indiv, df_villain_indiv, df3, df4, df5, df6 = sdg.get_metrics(username_private, gametype, driver, True)
                        time.sleep(2)

                        #update value of df1 in cache
                        set_user_df1(df1)

                        

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

                        return render_template('resultsPrivateAndPublic.html', username = username_private, num_games=num_games, win_rate=win_rate, num_wins=num_wins, result = output_html)
                
                    else:
                        return 'Pop-up window not opened yet!'
                else:
                    flash('Please subscribe to access more content.')
                    return redirect(url_for('pricing'))  # Redirect to the subscription page
            else:
                flash('Please log in to access content.')
                return redirect(url_for('login'))  # Redirect to the login page
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

############################################################
# LINK HTML TO HERO COMP IDENTIFIERS
############################################################
@app.route('/hero_comp_data/<comp_id>',methods=["GET","POST"])
def hero_comp_link(comp_id):
    #global df1

    #get df1 from the cache
    df1 = get_user_df1()

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

############################################################
# LINK HTML TO VILLAIN COMP IDENTIFIERS
############################################################
@app.route('/villain_comp_data/<comp_id>',methods=["GET","POST"])
def villain_comp_link(comp_id):
    #global df1

    #get df1 from the cache
    df1 = get_user_df1()

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

############################################################
# SUBSCRIPTION FUNCTIONALITY
############################################################

## return a stripe customer id depending on whether existing or new subscriber
def create_stripe_customer_and_store_id(user_email, subscription_price_id):
    try:
        # Check if the customer already exists in your application's database
        existing_user = get_user_by_email(user_email)
        if existing_user and existing_user[3]:
            # If the customer already has a Stripe customer ID, return it
            return existing_user[3]
        
        # Create a customer in Stripe
        customer = stripe.Customer.create(
            email=user_email,
            source='tok_visa',  # Replace with the actual payment method details
        )

        # Store the customer ID in your application's database
        # create_user(user_email, customer.id, subscription_price_id)  # Store customer ID along with other user data
        return customer.id  # Return the Stripe customer ID
    except stripe.error.StripeError as e:
        # Handle any errors from Stripe
        print(e)
        return None


@app.route('/subscription_success')
def subscription_success():
    return render_template('subscription_success.html')

@app.route('/subscription_cancel')
def subscription_cancel():
    return render_template('subscription_cancelled.html')

@app.route('/update_subscription', methods=['POST'])
def update_subscription():
    if request.method == 'POST':
        data = request.json  # Get JSON data from the request
        session_id = data.get('sessionID')
        user_email = data.get('user_email')

        # Get the customer ID associated with the user's email
        customer_id = get_customer_id_from_email(user_email)

        if customer_id:
            try:
                # Retrieve the Stripe session and check its payment status
                stripe_session = stripe.checkout.Session.retrieve(session_id)
                if stripe_session.payment_status == 'paid':
                    # Determine the new subscription status based on the session
                    subscription_price_id = session.display_items[0].custom.price

                    # Determine the new subscription status based on the subscription type
                    if subscription_price_id  == PREMIUM_PRICE_ID:
                        new_subscription_status = 'premium'
                    elif subscription_price_id  == STANDARD_PRICE_ID:
                        new_subscription_status = 'standard'

                    # Update the subscription status and customer ID in your database
                    update_subscription_and_customer_id(customer_id, new_subscription_status)

                    # Return a success response
                    return jsonify(success=True)
                else:
                    return jsonify(success=False, error='Payment not completed')
            except stripe.error.StripeError as e:
                return jsonify(success=False, error=str(e))
        else:
            return jsonify(success=False, error='User not found')


@app.route('/pricing', methods=["GET", "POST"])
def pricing():
    if 'user_email' in session:
        user = get_user_by_email(session['user_email'])

        if request.method == 'POST':
            selected_price_id = request.form.get('selected_price_id')  # Retrieve the selected price ID from the form

            # Create a Stripe Checkout session
            stripe_session = stripe.checkout.Session.create(
                customer_email=user[0],  # Use the user's email
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': selected_price_id,  # Use the selected price ID
                        'quantity': 1,
                    },
                ],
                mode='subscription',
                success_url=url_for('subscription_success', _external=True),
                cancel_url=url_for('subscription_cancel', _external=True),
            )

            return redirect(stripe_session.url)  # Redirect the user to the Stripe Checkout session

        # List of subscription plans and their price IDs
        subscription_plans = [
            {'name': 'premium', 'price_id': 'price_1NchwKDypgtvgAYhILRJc3RP'},
            {'name': 'standard', 'price_id': 'price_1NchwKDypgtvgAYhILRJc3RP'}
        ]

        return render_template('stripe.html', user=user, subscription_plans=subscription_plans)

    flash('Please log in to subscribe.')
    return redirect(url_for('login'))



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


############################################################
#
# OLD FUNCTIONS NO LONGER IN USE
#
############################################################
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