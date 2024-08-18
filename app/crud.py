from .db import get_redis_client
from .models import Alumni
import json

redis_client = get_redis_client()

def add_alumni(alumni: Alumni):
    redis_client.hset("alumni", alumni.name, json.dumps(alumni.dict()))

def get_alumni(name: str) -> Alumni:
    alumni_data = redis_client.hget("alumni", name)
    if alumni_data:
        return Alumni(**json.loads(alumni_data))

def get_all_alumni():
    alumni_data = redis_client.hgetall("alumni")
    return [Alumni(**json.loads(data)) for data in alumni_data.values()]
