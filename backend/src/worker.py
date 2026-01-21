# backend/src/worker.py
import os
import redis
from rq import Worker, Queue
from src.redis_config import redis_conn

listen = ['default']

if __name__ == '__main__':
    print("Worker started. Connecting to Redis...")
    
    # FIX: We create the Queue objects explicitly with the connection
    queues = [Queue(name, connection=redis_conn) for name in listen]
    
    # We pass the list of configured queues to the Worker
    worker = Worker(queues, connection=redis_conn)
    
    print("Worker is ready to process jobs.")
    worker.work()