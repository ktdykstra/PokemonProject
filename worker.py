# worker.py

import rq
import os
from redis import Redis
from rq import Worker, Queue
#from app import get_data_private # Import your long-running task function


# Get the Redis URL from environment variables
redis_url = os.environ.get('STACKHERO_REDIS_URL_TLS') or 'redis://localhost:6379/0'
# The Redis connection details
redis_host = 'qoxjxb.stackhero-network.com'
redis_port = '6380'
redis_password = '2SSlD7FN0buUpMoGeb4iR2eKf8vJ87GDm67hq6LEiQK6IloP3X01WFbCTfhiU0h8'

# Create a Redis connection using redis.StrictRedis
redis_conn = Redis(host=redis_host, port=redis_port, password=redis_password, ssl=True)

# Create a Redis connection 
#redis_conn = Redis.from_url(redis_url, ssl=True)

high_priority_queue = Queue("high_priority", connection=redis_url)

# Create a list of queues to be processed by the worker
queues = [high_priority_queue]

# Create the worker with the list of queues
worker = Worker(queues, connection=redis_conn)

if __name__ == "__main__":
    with Connection(redis_conn):
        worker.work()
