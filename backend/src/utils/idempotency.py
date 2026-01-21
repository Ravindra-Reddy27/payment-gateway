# backend/src/utils/idempotency.py
import json
from datetime import datetime, timedelta
# Import your database connection (adjust import based on your existing project structure)
from src.db import get_db_connection 

def get_idempotency_key(key, merchant_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check if key exists and belongs to this merchant
    cur.execute("""
        SELECT response, expires_at 
        FROM idempotency_keys 
        WHERE key = %s AND merchant_id = %s
    """, (key, merchant_id))
    
    record = cur.fetchone()
    cur.close()
    conn.close()
    
    if record:
        response_json, expires_at = record
        # Check if expired
        if datetime.now() > expires_at:
            # Delete expired key so we can process as new
            delete_idempotency_key(key, merchant_id)
            return None
        return response_json
    return None

def save_idempotency_key(key, merchant_id, response_data):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Expires in 24 hours [cite: 91, 241]
    expires_at = datetime.now() + timedelta(hours=24)
    
    cur.execute("""
        INSERT INTO idempotency_keys (key, merchant_id, response, expires_at)
        VALUES (%s, %s, %s, %s)
    """, (key, merchant_id, json.dumps(response_data), expires_at))
    
    conn.commit()
    cur.close()
    conn.close()

def delete_idempotency_key(key, merchant_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM idempotency_keys WHERE key = %s AND merchant_id = %s", (key, merchant_id))
    conn.commit()
    cur.close()
    conn.close()