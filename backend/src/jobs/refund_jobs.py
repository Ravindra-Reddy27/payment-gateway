# backend/src/jobs/refund_jobs.py
import time
import random
import os
import json
from datetime import datetime
from src.db import get_db_connection
from src.redis_config import q
from src.jobs.webhook_jobs import deliver_webhook

def process_refund(refund_id):
    print(f"Processing Refund: {refund_id}")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 1. Fetch Refund and Payment Details
        # We join with payments to check the payment status and original amount
        cur.execute("""
            SELECT r.amount, r.payment_id, r.merchant_id, 
                   p.amount, p.status 
            FROM refunds r
            JOIN payments p ON r.payment_id = p.id
            WHERE r.id = %s
        """, (refund_id,))
        
        data = cur.fetchone()
        if not data:
            print("Refund not found")
            return

        refund_amount, payment_id, merchant_id, payment_total_amount, payment_status = data

        # 2. Verify Payment State [cite: 166]
        if payment_status != 'success':
            print(f"Cannot refund: Payment {payment_id} is not successful (Status: {payment_status})")
            # In a real app, you might mark refund as failed here.
            return

        # 3. Verify Total Refunded Amount [cite: 167]
        # Calculate sum of all OTHER refunds (processed) + this one
        cur.execute("""
            SELECT COALESCE(SUM(amount), 0) 
            FROM refunds 
            WHERE payment_id = %s AND status = 'processed'
        """, (payment_id,))
        total_refunded_so_far = cur.fetchone()[0]
        
        if (total_refunded_so_far + refund_amount) > payment_total_amount:
            print(f"Cannot refund: Exceeds payment amount.")
            return

        # 4. Simulate Delay [cite: 168]
        # Wait 3-5 seconds
        time.sleep(random.uniform(3, 5))

        # 5. Update Refund Status [cite: 171]
        cur.execute("""
            UPDATE refunds 
            SET status = 'processed', processed_at = %s 
            WHERE id = %s
        """, (datetime.utcnow(), refund_id))
        
        conn.commit()
        print(f"Refund {refund_id} processed successfully.")

        # 6. Enqueue Webhook [cite: 175]
        payload = {
            "event": "refund.processed",
            "timestamp": int(time.time()),
            "data": {
                "refund": {
                    "id": refund_id,
                    "payment_id": payment_id,
                    "amount": refund_amount,
                    "status": "processed"
                }
            }
        }
        q.enqueue(deliver_webhook, merchant_id, "refund.processed", payload)

    except Exception as e:
        print(f"Error processing refund: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()