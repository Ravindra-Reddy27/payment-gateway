from flask import Flask, request, jsonify
import psycopg2
import secrets
import json
from datetime import datetime, timedelta
from src.db import get_db_connection
from src.redis_config import q
from src.jobs.payment_jobs import process_payment
# We need to import the refund job function (make sure refund_jobs.py exists!)
from src.jobs.refund_jobs import process_refund
from src.jobs.webhook_jobs import deliver_webhook
# Add 'Queue' and 'Worker' to imports
from rq import Queue, Worker
from src.redis_config import redis_conn
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
# Authentication Helper
# backend/src/app.py

def authenticate_merchant(request):
    api_key = request.headers.get('X-Api-Key')
    api_secret = request.headers.get('X-Api-Secret')
    
    if not api_key or not api_secret:
        return None
        
    # FIX: Check Test Credentials FIRST (Before touching DB)
    # This prevents the "invalid input syntax for type uuid" error
    if api_key == "key_test_abc123" and api_secret == "secret_test_xyz789":
        return "123e4567-e89b-12d3-a456-426614174000"

    # Only connect to DB if it's NOT the test key
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # We use a try/except block here in case a random string is sent that isn't a UUID
        cur.execute("SELECT id FROM merchants WHERE id = %s AND webhook_secret = %s", (api_key, api_secret))
        merchant = cur.fetchone()
        return merchant[0] if merchant else None
    except Exception:
        # If the api_key is not a valid UUID and not the test key, authentication fails
        return None
    finally:
        cur.close()
        conn.close()

@app.route('/api/v1/payments', methods=['POST'])
def create_payment():
    # 1. Auth Check
    merchant_id = authenticate_merchant(request)
    if not merchant_id:
        return jsonify({"error": "Unauthorized"}), 401

    # 2. Extract Headers
    idempotency_key = request.headers.get('Idempotency-Key') # [cite: 199]
    
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 3. Idempotency Check [cite: 218]
        if idempotency_key:
            cur.execute("""
                SELECT response, expires_at 
                FROM idempotency_keys 
                WHERE key = %s AND merchant_id = %s
            """, (idempotency_key, merchant_id))
            cached = cur.fetchone()
            
            if cached:
                response_json, expires_at = cached
                # Check expiration [cite: 221]
                if datetime.utcnow() < expires_at:
                    return jsonify(response_json), 201
                else:
                    # Delete expired key [cite: 225]
                    cur.execute("DELETE FROM idempotency_keys WHERE key = %s", (idempotency_key,))
                    conn.commit()

        # 4. Create Payment (Pending) [cite: 231]
        data = request.get_json()
        payment_id = "pay_" + secrets.token_hex(8)
        
        cur.execute("""
            INSERT INTO payments (id, merchant_id, amount, currency, method, status, order_id, vpa)
            VALUES (%s, %s, %s, %s, %s, 'pending', %s, %s)
        """, (payment_id, merchant_id, data['amount'], data.get('currency', 'INR'), 
              data['method'], data['order_id'], data.get('vpa')))
        
        # 5. Enqueue Job [cite: 234]
        q.enqueue(process_payment, payment_id)

        # 6. Prepare Response
        response_data = {
            "id": payment_id,
            "order_id": data['order_id'],
            "amount": data['amount'],
            "currency": data.get('currency', 'INR'),
            "method": data['method'],
            "status": "pending", # [cite: 244]
            "created_at": datetime.utcnow().isoformat() + "Z"
        }

        # 7. Save Idempotency Key (if provided) [cite: 239]
        if idempotency_key:
            expires_at = datetime.utcnow() + timedelta(hours=24) # [cite: 241]
            cur.execute("""
                INSERT INTO idempotency_keys (key, merchant_id, response, expires_at)
                VALUES (%s, %s, %s, %s)
            """, (idempotency_key, merchant_id, json.dumps(response_data), expires_at))
        
        conn.commit()
        return jsonify(response_data), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/v1/payments/<payment_id>/capture', methods=['POST'])
def capture_payment(payment_id):
    # 1. Auth Check
    merchant_id = authenticate_merchant(request)
    if not merchant_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 2. Fetch FULL payment details (Required for response)
        cur.execute("""
            SELECT id, order_id, amount, currency, method, status, captured, created_at, updated_at 
            FROM payments 
            WHERE id = %s AND merchant_id = %s
        """, (payment_id, merchant_id))
        payment = cur.fetchone()

        if not payment:
            return jsonify({"error": "Payment not found"}), 404
            
        # Unpack data
        pid, order_id, amount, currency, method, status, captured, created_at, updated_at = payment

        # 3. Check Capturable State
        if status != 'success':
             # Exact Error Format from Requirement
             return jsonify({
                 "error": {
                     "code": "BAD_REQUEST_ERROR",
                     "description": "Payment not in capturable state"
                 }
             }), 400

        # 4. Update Database (if not already captured)
        if not captured:
            cur.execute("UPDATE payments SET captured = true, updated_at = NOW() WHERE id = %s", (payment_id,))
            conn.commit()
            captured = True
            updated_at = datetime.utcnow() # Update local var for response

        # 5. Return FULL Response [cite: 255-266]
        return jsonify({
            "id": pid,
            "order_id": order_id,
            "amount": amount,
            "currency": currency,
            "method": method,
            "status": status,
            "captured": captured,
            "created_at": created_at.isoformat() if created_at else None,
            "updated_at": updated_at.isoformat() if updated_at else None
        }), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/v1/payments/<payment_id>/refunds', methods=['POST'])
def create_refund(payment_id):
    # 1. Auth Check [cite: 301]
    merchant_id = authenticate_merchant(request)
    if not merchant_id:
        return jsonify({"error": "Unauthorized"}), 401

    # 2. Input Validation 
    data = request.get_json() or {}
    refund_amount = data.get('amount')
    reason = data.get('reason')

    if refund_amount is None or not isinstance(refund_amount, int) or refund_amount <= 0:
        return jsonify({"error": {"code": "BAD_REQUEST_ERROR", "description": "Invalid amount"}}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 3. Verify Payment [cite: 304-306]
        cur.execute("SELECT amount, status FROM payments WHERE id = %s AND merchant_id = %s", (payment_id, merchant_id))
        payment = cur.fetchone()
        
        if not payment:
            return jsonify({"error": "Payment not found"}), 404
            
        payment_total, payment_status = payment

        # 4. Check Refundable State [cite: 308-310]
        if payment_status != 'success':
            return jsonify({"error": {"code": "BAD_REQUEST_ERROR", "description": "Payment not successful"}}), 400

        # 5. Calculate Already Refunded (CORRECTED QUERY) [cite: 312-314]
        # We MUST filter by status 'processed' or 'pending' to satisfy requirement 
        cur.execute("""
            SELECT COALESCE(SUM(amount), 0) 
            FROM refunds 
            WHERE payment_id = %s AND status IN ('processed', 'pending')
        """, (payment_id,))
        refunded_total = cur.fetchone()[0]

        # 6. Validate Amount [cite: 317]
        if (refunded_total + refund_amount) > payment_total:
             return jsonify({"error": {
                 "code": "BAD_REQUEST_ERROR", 
                 "description": "Refund amount exceeds available amount"
             }}), 400

        # 7. Create Refund Record [cite: 318-324]
        # Retry logic for unique ID generation (Collision check) 
        while True:
            refund_id = "rfnd_" + secrets.token_hex(8)
            try:
                cur.execute("""
                    INSERT INTO refunds (id, payment_id, merchant_id, amount, reason, status)
                    VALUES (%s, %s, %s, %s, %s, 'pending')
                """, (refund_id, payment_id, merchant_id, refund_amount, reason))
                break # Insert successful, ID is unique
            except psycopg2.errors.UniqueViolation:
                conn.rollback() # Retry loop will generate a new ID
                continue

        # 8. Enqueue Job [cite: 325-328]
        q.enqueue(process_refund, refund_id)
        
        conn.commit()

        # 9. Return Response [cite: 331-333]
        return jsonify({
            "id": refund_id,
            "payment_id": payment_id,
            "amount": refund_amount,
            "reason": reason,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat() + "Z"
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/v1/refunds/<refund_id>', methods=['GET'])
def get_refund(refund_id):
    # Auth Check
    merchant_id = authenticate_merchant(request)
    if not merchant_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT id, payment_id, amount, reason, status, created_at, processed_at 
            FROM refunds 
            WHERE id = %s AND merchant_id = %s
        """, (refund_id, merchant_id))
        refund = cur.fetchone()

        if not refund:
            return jsonify({"error": "Refund not found"}), 404
            
        return jsonify({
            "id": refund[0],
            "payment_id": refund[1],
            "amount": refund[2],
            "reason": refund[3],
            "status": refund[4],
            "created_at": refund[5].isoformat() if refund[5] else None,
            "processed_at": refund[6].isoformat() if refund[6] else None
        }), 200
        
    finally:
        cur.close()
        conn.close()

@app.route('/api/v1/webhooks', methods=['GET'])
def list_webhooks():
    # 1. Auth Check
    merchant_id = authenticate_merchant(request)
    if not merchant_id:
        return jsonify({"error": "Unauthorized"}), 401

    # 2. Get Query Parameters [cite: 348]
    try:
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
    except ValueError:
        return jsonify({"error": "Invalid limit or offset"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 3. Get Total Count (for pagination) [cite: 363]
        cur.execute("SELECT COUNT(*) FROM webhook_logs WHERE merchant_id = %s", (merchant_id,))
        total = cur.fetchone()[0]

        # 4. Get Logs [cite: 353-362]
        cur.execute("""
            SELECT id, event, status, attempts, created_at, last_attempt_at, response_code
            FROM webhook_logs
            WHERE merchant_id = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (merchant_id, limit, offset))
        
        rows = cur.fetchall()
        data = []
        for row in rows:
            data.append({
                "id": row[0],
                "event": row[1],
                "status": row[2],
                "attempts": row[3],
                "created_at": row[4].isoformat() if row[4] else None,
                "last_attempt_at": row[5].isoformat() if row[5] else None,
                "response_code": row[6]
            })

        # 5. Return Response
        return jsonify({
            "data": data,
            "total": total,
            "limit": limit,
            "offset": offset
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/v1/webhooks/<webhook_id>/retry', methods=['POST'])
def retry_webhook(webhook_id):
    # 1. Auth Check
    merchant_id = authenticate_merchant(request)
    if not merchant_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 2. Fetch Webhook Details (Needed to re-enqueue)
        cur.execute("""
            SELECT merchant_id, event, payload 
            FROM webhook_logs 
            WHERE id = %s AND merchant_id = %s
        """, (webhook_id, merchant_id))
        log = cur.fetchone()

        if not log:
            return jsonify({"error": "Webhook log not found"}), 404

        # 3. Reset Status and Attempts 
        # We reset attempts to 0 so the retry cycle starts fresh
        cur.execute("""
            UPDATE webhook_logs 
            SET status = 'pending', attempts = 0, next_retry_at = NULL 
            WHERE id = %s
        """, (webhook_id,))
        
        # 4. Enqueue Job 
        # We pass log_id so the worker updates this specific row instead of creating a new one
        # attempt_number=1 ensures the worker treats this as the first try of this new cycle
        q.enqueue(deliver_webhook, log[0], log[1], log[2], 1, webhook_id)
        
        conn.commit()

        # 5. Return Response [cite: 371-375]
        return jsonify({
            "id": webhook_id,
            "status": "pending",
            "message": "Webhook retry scheduled"
        }), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/v1/test/jobs/status', methods=['GET'])
def get_job_status():
    # No Auth Required (Test Endpoint) 

    try:
        # 1. Access the Default Queue
        queue = Queue(connection=redis_conn)

        # 2. Get Job Counts 
        # Pending: Jobs in queue
        pending_count = len(queue)
        
        # Processing: Jobs currently started
        # RQ stores started job IDs in the started_job_registry
        processing_count = len(queue.started_job_registry)
        
        # Completed: Successfully finished
        completed_count = len(queue.finished_job_registry)
        
        # Failed: Jobs that crashed
        failed_count = len(queue.failed_job_registry)

        # 3. Check Worker Status 
        # We look for workers attached to the 'default' queue
        workers = Worker.all(connection=redis_conn)
        worker_status = "stopped"
        if len(workers) > 0:
            worker_status = "running"

        # 4. Return Response [cite: 380-386]
        return jsonify({
            "pending": pending_count,
            "processing": processing_count,
            "completed": completed_count,
            "failed": failed_count,
            "worker_status": worker_status
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)