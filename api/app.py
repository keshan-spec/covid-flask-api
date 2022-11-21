from flask import Flask
import requests
from bs4 import BeautifulSoup
import os
import json
import redis
from datetime import timedelta

# from dotenv import load_dotenv

# load_dotenv()
KEY = "covid19"
app = Flask(__name__)

commands = {
    "updates": "Gets the latest updates about the virus",
    "show/:country": "Shows the stats for a specific country (use 'all' to show all countries)",
    "stats/:option": "Shows the stats for a specific option (cases, deaths, recovered)",
}


def get_info_table(cache=True) -> dict:
    """
    @desc: Scrapes the data from the website and returns it as a json
    @params: None
    @returns: json
    """

    # Check if the cache is available
    if cache:
        entries = check_cache()
        if entries:
            return entries

    soup = BeautifulSoup(requests.get(os.getenv("URL")).content, features="html.parser")
    table = soup.find("table", {"id": "main_table_countries_today"})
    tmp = []
    keys = [
        "Country",
        "Total Cases",
        "New Cases",
        "Total Deaths",
        "New Deaths",
        "Total Recovered",
        "New Recovered",
        "Active Cases",
    ]  # the keys of the table

    for tr in table.findAll("tr")[:-1]:
        if tr.has_attr("data-continent") == False:
            for td in tr.findAll("td")[1:9]:
                if td.has_attr("data-continent") == False:
                    try:
                        tmp.append(
                            td.find(text=True)
                            .strip()
                            .lower()
                            .replace(".", "")
                            .replace("-", "")
                            .replace(" ", "_")
                        )
                    except Exception as e:
                        tmp.append(td.find(text=True))
                        pass

    s, e = 0, len(keys)
    entries = []
    entries.append({"cache": False})

    # Loop through the temp list and make a dict with every 9 items
    for _ in range(len(tmp) // len(keys)):
        d = dict(zip(keys, tmp[s:e]))
        if d:
            entries.append(d)
        s += len(keys)
        e += len(keys)
    return {"data": entries}


# REDIS SETUP
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


def get_cache(client: redis.client.Redis, key: str) -> str:
    return client.get(key)


def set_cache(client: redis.client.Redis, key: str, value: str) -> bool:
    state = client.setex(
        key,
        timedelta(seconds=10),
        value=value,
    )
    return state


def check_cache() -> dict:
    # First it looks for the data in redis cache
    data = get_cache(client=REDIS_CLIENT, key=KEY)

    # If cache is found then serves the data from cache
    if data is not None:
        data = json.loads(data)
        return {"cache": True, "data": data}
    else:
        # If cache is not found then sends request to the MapBox API
        data = get_info_table(cache=False)
        # This block sets saves the respose to redis and serves it directly
        if data:
            state = set_cache(client=REDIS_CLIENT, key=KEY, value=json.dumps(data))
            return {"cache": False, "data": data} if state else None
        return data


# REDIS SETUP END

# get redis client
REDIS_CLIENT = redis_connect()

# ROUTES
@app.route("/")
def home():
    # return the commands
    return json.dumps(commands)


@app.route("/updates")
def get_updates():
    soup = BeautifulSoup(requests.get(os.getenv("URL")).content, features="html.parser")
    infect_count = soup.find_all("div", {"class": "maincounter-number"})
    infect_count = [i.find("span").findAll(text=True)[0].strip() for i in infect_count]
    return json.dumps(
        {
            "Infected": infect_count[0],
            "Deaths": infect_count[1],
            "Recovered": infect_count[2],
        }
    )


@app.route("/stats/<opt>")
def get_stats(opt):
    # get the stats for a specific option
    # opt can be cases, deaths, recovered
    entries = get_info_table()
    opts = {
        "death": "Total Deaths",
        "recovered": "Total Recovered",
        "cases": "Total Cases",
    }
    if opt not in opts.keys():
        return json.dumps({"Invalid option": opts})

    key = opts[opt]
    key_vals = {}
    for entry in entries["data"]:
        if entry[key]:
            if entry["Country"] != "world":
                key_vals[entry["Country"]] = int(entry[key].replace(",", ""))

    max_key = max(key_vals, key=key_vals.get)
    return json.dumps({max_key: key_vals[max_key], "cache": entries["cache"]})


@app.route("/show/<country>")
def get_country(country):
    entries = get_info_table()
    if country == "all":
        return json.dumps(entries)
    else:
        for entry in entries["data"]:
            if entry["Country"] == country.lower():
                return json.dumps({**entry, "cache": entries["cache"]})
        return json.dumps({"error": f"Country not found: {country}"})


# Run the app
if __name__ == "__main__":
    app.run(debug=True)
