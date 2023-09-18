# worker.py

import rq
import os
from redis import Redis
from rq import Worker, Queue
#from app import get_data_private # Import your long-running task function


# Get the Redis URL from environment variables
redis_url = os.environ.get('STACKHERO_REDIS_URL_TLS') or 'redis://localhost:6379/0'


# Create a Redis connection 
redis_conn = Redis.from_url(redis_url, ssl=True)

high_priority_queue = Queue("high_priority", connection=redis_conn)

# Create a list of queues to be processed by the worker
queues = [Queue("high_priority", connection=redis_conn)]

# Create the worker with the list of queues
worker = Worker(queues, connection=redis_conn)

if __name__ == "__main__":
    worker.work()
