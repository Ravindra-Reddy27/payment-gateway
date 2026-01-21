# backend/src/db.py
import os
import psycopg2

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('POSTGRES_HOST', 'postgres'),
        database=os.environ.get('POSTGRES_DB', 'payment_gateway'),
        user=os.environ.get('POSTGRES_USER', 'gateway_user'),
        password=os.environ.get('POSTGRES_PASSWORD', 'gateway_pass')
    )
    return conn