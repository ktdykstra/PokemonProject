# IMPORT DB functionality from database.py
from database import connect_to_db, close_connection, DatabaseHandler
import psycopg2

DATABASE_URL=os.environ.get('DATABASE_URL')

# db_handler = DatabaseHandler()

def get_db():
    return connect_to_db()

#called automatically at end of each request :)
@app.teardown_appcontext
def close_db(error):
    db_handler.close_connection()

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
            print("\n")
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
        print("Good query")
        result = cursor.fetchone()  # Fetch a single row
        close_connection(db, cursor) # close db
        return result
    except Exception as e:
        print("Unalbe to get user. Error:",e)
        close_connection(db, cursor)
        return


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

## update strip customer ID
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

## update subscription status
def update_subscription_status(user_email, new_status):
    db, cursor = get_db()
    try:
        cursor.execute('UPDATE serapis_schema.serapis_users SET subscription_status = %s WHERE email = %s', (new_status, user_email))
        db.commit()
        close_connection(db,cursor) # close db
        print(f'Subscription status updated to {new_status} for user: {user_email}')
    except Exception as e:
        db.rollback()
        close_connection(db,cursor) # close db
        print(f"Unable to update subscription status for user: {user_email}. Error:",e)

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

    cursor.close()
    if user:
        return user[0]
    return 'free'


def update_subscription_status(stripe_customer_id, new_status):
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

# Update subscription status and customer ID in your database
def update_subscription_and_customer_id(stripe_customer_id, new_subscription_status):

    db, cursor = get_db()
    cursor.execute('UPDATE serapis_schema.serapis_users SET subscription_status = %s, stripe_customer_id = %s WHERE stripe_customer_id = %s',
               (new_subscription_status, customer_id, customer_id))
    db.commit()

# Function to get user's subscription status from the database
def get_stripe_customer_id(user_email):
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

# Function to get user's subscription status from the database
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
###### TESTING #####
x=get_user_by_email("ngk22@gmail.com")
x[3]

update_subscription_status()
for row in result:
    print(row)
close_connection(db,cursor) # close db
view_user_data()
get_subscription_status("ngk@gmail.com")
update_subscription_status("123dx_d!","free")
get_user_by_email("ngk@gmail.com")
update_subscription_and_customer_id("1222cvadsgx","premium")
create_user("newcust@email.com","free",0)
if get_user_by_email("newcust@email.com")[3]:
    print("passed")