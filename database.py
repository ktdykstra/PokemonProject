## create database with email (primary key), subscription tracker, free trial tracker, usernames?, and webhooks
import os
from dotenv import load_dotenv
import psycopg2
# from mysql import connector # for mysql

## setup the database
load_dotenv()
DATABASE_URL = os.environ.get('DATABASE_URL') #for when deployed

def connect_to_db():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    return conn, cursor

def close_connection(conn, cursor):
    cursor.close()
    conn.close()


class DatabaseHandler:
    def __init__(self):
        self.conn, self.cursor = connect_to_db()

    def get_data(self):
        try:
            self.cursor.execute("SELECT * FROM serapis_schema.serapis_users;")
            rows = self.cursor.fetchall()
            return rows
        except Exception as e:
            print("Error:", e)

    def close_connection(self):
        close_connection(self.conn, self.cursor)

''' Testing
# # table name is third_schema.serapis_users

## create schema
try:
    # setup schema
    create_schema_query = """
    CREATE SCHEMA IF NOT EXISTS serapis_schema;
    """
    cursor.execute(create_schema_query)
    conn.commit()
except Exception as e:
    # Rollback the transaction in case of an error
    conn.rollback()
    print("Error:", e)

# create initial table
try:
    create_table_query = """
    CREATE TABLE IF NOT EXISTS serapis_schema.serapis_users (
        email VARCHAR(50) PRIMARY KEY,
        subscription_status TEXT,
        click_count INT,
        stripe_customer_id TEXT
    );
    """
    cursor.execute(create_table_query)
    conn.commit()
except Exception as e:
    # Rollback the transaction in case of an error
    conn.rollback()
    print("Error:", e)

# ## add an entry
# try:
#     # Define the values to be inserted
#     email = 'example@example.com'
#     subscription_status = 'free'
#     counter = 5

#     # Execute an INSERT query to add the entry to the table
#     cursor.execute("INSERT INTO third_schema.serapis_users (email, subscription_status, click_count) VALUES (%s, %s, %s)",
#                    (email, subscription_status, counter))

#     # Commit the transaction
#     conn.commit()
#     print("Entry added successfully!")
# except Exception as e:
#     # Rollback the transaction in case of an error
#     conn.rollback()
#     print("Error:", e)



# try:
#     cursor.execute("SELECT * FROM third_schema.serapis_users;")
#     # Fetch all rows
#     rows = cursor.fetchall()

#     # Print the retrieved data
#     for row in rows:
#         print(row)
# except Exception as e:
#     print("Error:", e)

# # Execute a query to get information about the table columns
# try:
#     table_name = "serapis_users"
#     cursor.execute(f"SELECT column_name, data_type FROM third_schema.columns WHERE table_name = '{table_name}'")
#     columns = cursor.fetchall()

#     # Execute a query to get all entries in the table
#     cursor.execute(f"SELECT * FROM {table_name}")
#     entries = cursor.fetchall()

#     # Print the columns and entries
#     print("Table Columns:")
#     for column in columns:
#         print(column)

#     print("\nTable Entries:")
#     for entry in entries:
#         print(entry)
# except Exception as e:
#     conn.rollback()
#     print("Error:", e)

'''


