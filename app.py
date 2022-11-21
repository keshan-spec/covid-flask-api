from flask import Flask
import requests
from bs4 import BeautifulSoup
import os
import json


# load env file
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

commands = {
    "updates": "Gets the latest updates about the virus",
    "show/:country": "Shows the stats for a specific country (use 'all' to show all countries)",
    "stats/:option": "Shows the stats for a specific option (cases, deaths, recovered)",
}

URL = os.getenv("URL")


@app.route("/")
def home():
    # return the commands
    return json.dumps(commands)


def run():
    return BeautifulSoup(requests.get(URL).content, features="html.parser")


@app.route("/updates")
def get_updates():
    soup = run()
    infect_count = soup.find_all("div", {"class": "maincounter-number"})
    infect_count = [i.find("span").findAll(text=True)[0].strip() for i in infect_count]
    return json.dumps(
        {
            "Infected": infect_count[0],
            "Deaths": infect_count[1],
            "Recovered": infect_count[2],
        }
    )


def get_info_table():
    soup = run()
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

    # Loop through the temp list and make a dict with every 9 items
    for _ in range(len(tmp) // len(keys)):
        d = dict(zip(keys, tmp[s:e]))
        if d:
            entries.append(d)
        s += len(keys)
        e += len(keys)
    return entries


@app.route("/show/<country>")
def get_country(country):
    entries = get_info_table()
    if country == "all":
        return json.dumps(entries)
    else:
        for entry in entries:
            if entry["Country"] == country.lower():
                return json.dumps(entry)
        return json.dumps({"error": f"Country not found: {country}"})


# Run the app
if __name__ == "__main__":
    app.run(debug=True)
