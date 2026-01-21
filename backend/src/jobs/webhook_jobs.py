# backend/src/jobs/webhook_jobs.py
import hmac
import hashlib
import json
import requests
import os
from datetime import datetime, timedelta
from src.db import get_db_connection

def generate_signature(payload, secret):
    if not secret:
        return ""
    payload_str = json.dumps(payload, separators=(',', ':'))
    signature = hmac.new(
        key=secret.encode('utf-8'),
        msg=payload_str.encode('utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()
    return signature

def get_next_retry_time(attempts):
    if os.environ.get('WEBHOOK_RETRY_INTERVALS_TEST') == 'true':
        intervals = [0, 5, 10, 15, 20]
    else:
        intervals = [0, 60, 300, 1800, 7200]
        
    if attempts < len(intervals):
        return datetime.utcnow() + timedelta(seconds=intervals[attempts])
    return None

def deliver_webhook(merchant_id, event_type, payload, attempt_number=1, log_id=None):
    print(f"Webhook Delivery: {event_type} to {merchant_id} (Attempt {attempt_number})")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 1. Fetch Merchant Details
        cur.execute("SELECT webhook_url, webhook_secret FROM merchants WHERE id = %s", (merchant_id,))
        merchant = cur.fetchone()
        
        db_url = merchant[0] if merchant else None
        webhook_secret = merchant[1] if merchant else None
        
        # Use DB URL, fallback to local test override if needed
        webhook_url = db_url 
        
        # Test Mode Hack for your local setup
        if not webhook_url or "localhost" in webhook_url:
             # REPLACE WITH YOUR REAL IP IF NEEDED
             webhook_url = "http://host.docker.internal:4000/webhook" 

        if not webhook_url:
            print("No webhook_url configured, skipping.")
            return

        # 2. Generate Signature
        signature = generate_signature(payload, webhook_secret)
        
        # 3. Log Attempt (or update existing)
        if not log_id:
            cur.execute("""
                INSERT INTO webhook_logs (merchant_id, event, payload, status, attempts, created_at)
                VALUES (%s, %s, %s, 'pending', %s, %s)
                RETURNING id
            """, (merchant_id, event_type, json.dumps(payload), attempt_number, datetime.utcnow()))
            log_id = cur.fetchone()[0]
        else:
            cur.execute("""
                UPDATE webhook_logs 
                SET attempts = %s, last_attempt_at = %s 
                WHERE id = %s
            """, (attempt_number, datetime.utcnow(), log_id))
        conn.commit()

        # 4. Send Request
        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Signature': signature
        }
        
        response = requests.post(
            webhook_url,
            data=json.dumps(payload, separators=(',', ':')),
            headers=headers,
            timeout=5
        )
        
        # 5. Handle Success
        if 200 <= response.status_code < 300:
            # FIXED: Removed 'processed_at' from this query
            cur.execute("""
                UPDATE webhook_logs 
                SET status = 'success', response_code = %s, response_body = %s, last_attempt_at = %s
                WHERE id = %s
            """, (response.status_code, response.text[:1000], datetime.utcnow(), log_id))
            print("Webhook delivered successfully.")
        else:
            raise Exception(f"HTTP {response.status_code}")

    except Exception as e:
        print(f"Webhook failed: {e}")
        conn.rollback() # <--- IMPORTANT: Fixes the "transaction aborted" error
        
        # 6. Handle Failure & Retries
        if attempt_number >= 5:
            cur.execute("""
                UPDATE webhook_logs 
                SET status = 'failed', response_body = %s 
                WHERE id = %s
            """, (str(e)[:1000], log_id))
            print("Max retries reached. Marking as failed.")
        else:
            next_retry_time = get_next_retry_time(attempt_number)
            cur.execute("""
                UPDATE webhook_logs 
                SET status = 'pending', next_retry_at = %s, response_body = %s
                WHERE id = %s
            """, (next_retry_time, str(e)[:1000], log_id))
            
            delay_seconds = (next_retry_time - datetime.utcnow()).total_seconds()
            print(f"Scheduling retry #{attempt_number + 1} in {delay_seconds}s")

    finally:
        conn.commit()
        cur.close()
        conn.close()