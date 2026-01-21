# backend/src/redis_config.py
import os
import redis
from rq import Queue

# 1. Get the address of the Redis server from the environment (or use default)
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

# 2. Create the connection
redis_conn = redis.from_url(REDIS_URL)

# 3. Create the Queues
# We can have different priority queues, but 'default' is fine for now.
# This 'q' variable is what the API will use to add jobs.
q = Queue('default', connection=redis_conn)