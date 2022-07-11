from django.shortcuts import render
import psycopg2


# Create database connection.
# Source DB
def connection(database, user, password, host, port):
    conn = psycopg2.connect(
        database=database, 
        user=user, 
        password=password, 
        host=host, 
        port= port
    )

    return conn
    #Creating a cursor object using the cursor() method
    # return conn.cursor()

# Traget DB
def target_db_connection(database, user, password, host, port):
    conn = psycopg2.connect(
        database=database, 
        user=user, 
        password=password, 
        host=host, 
        port= port
    )

    return conn
    #Creating a cursor object using the cursor() method
    # return conn.cursor()
