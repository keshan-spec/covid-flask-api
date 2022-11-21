import redis
from datetime import timedelta
from dotenv import load_dotenv
import os, json

load_dotenv()


def redis_connect() -> redis.client.Redis:
    try:
        client = redis.Redis(
            host=os.getenv("REDIS_HOST"),
            port=os.getenv("REDIS_PORT"),
            password=os.getenv("REDIS_PASSWORD"),
            db=os.getenv("REDIS_DB"),
            socket_timeout=5,
        )
        return client if client.ping() else None
    except redis.AuthenticationError:
        print("AuthenticationError")
        exit()


def get_routes_from_cache(client, key) -> str:
    """Data from redis."""

    val = client.get(key)
    return val


def set_routes_to_cache(client, key, value) -> bool:
    """Data to redis."""
    state = client.setex(
        key,
        timedelta(seconds=3000),
        value=value,
    )
    return state


def route_optima(coordinates: str) -> dict:
    # First it looks for the data in redis cache
    data = get_routes_from_cache(key=coordinates)

    # If cache is found then serves the data from cache
    if data is not None:
        data = json.loads(data)
        data["cache"] = True
        return data

    else:
        # If cache is not found then sends request to the MapBox API
        data = get_routes_from_api(coordinates)

        # This block sets saves the respose to redis and serves it directly
        if data.get("code") == "Ok":
            data["cache"] = False
            data = json.dumps(data)
            state = set_routes_to_cache(key=coordinates, value=data)

            if state is True:
                return json.loads(data)
        return data
