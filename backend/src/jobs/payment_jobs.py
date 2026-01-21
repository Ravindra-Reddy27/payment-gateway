import time
import random
import os
from src.db import get_db_connection
from src.redis_config import q
# Import the webhook job so we can enqueue it
from src.jobs.webhook_jobs import deliver_webhook

def process_payment(payment_id):
    print(f"Processing Payment: {payment_id}")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 1. Fetch Payment details [cite: 118]
        cur.execute("SELECT amount, method, merchant_id FROM payments WHERE id = %s", (payment_id,))
        payment = cur.fetchone()
        if not payment:
            print("Payment not found!")
            return
            
        amount, method, merchant_id = payment

        # 2. Simulate Delay [cite: 119]
        if os.environ.get('TEST_MODE') == 'true':
            delay = float(os.environ.get('TEST_PROCESSING_DELAY', 1.0))
            time.sleep(delay)
        else:
            time.sleep(random.uniform(5, 10))

        # 3. Determine Outcome [cite: 122]
        success = False
        if os.environ.get('TEST_MODE') == 'true':
            success = os.environ.get('TEST_PAYMENT_SUCCESS', 'true').lower() == 'true'
        else:
            if method == 'upi':
                success = random.random() < 0.90
            else:
                success = random.random() < 0.95

        # 4. Update Database [cite: 126]
        if success:
            new_status = 'success'
            # If successful, we update status and captured
            cur.execute("""
                UPDATE payments 
                SET status = %s, captured = %s 
                WHERE id = %s
            """, (new_status, True, payment_id))
        else:
            new_status = 'failed'
            # If failed, we MUST update error fields 
            error_code = "PAYMENT_FAILED"
            error_desc = "Transaction declined by bank"
            cur.execute("""
                UPDATE payments 
                SET status = %s, error_code = %s, error_description = %s 
                WHERE id = %s
            """, (new_status, error_code, error_desc, payment_id))
            
        conn.commit()
        print(f"Payment {payment_id} processed. Status: {new_status}")

        # 5. Enqueue Webhook Job [cite: 129]
        event_type = 'payment.success' if success else 'payment.failed'
        
        payload = {
            "event": event_type,
            "timestamp": int(time.time()),
            "data": {
                "payment": {
                    "id": payment_id,
                    "amount": amount,
                    "status": new_status,
                    "method": method
                }
            }
        }
        
        # Add error details to webhook payload if failed
        if not success:
            payload["data"]["payment"]["error"] = {
                "code": "PAYMENT_FAILED",
                "description": "Transaction declined by bank"
            }
        
        print(f"Enqueuing webhook for {event_type}")
        q.enqueue(deliver_webhook, merchant_id, event_type, payload)

    except Exception as e:
        print(f"Error processing payment: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()