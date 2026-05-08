import json, os

def load_prices():
    path = os.path.join(os.path.dirname(__file__), "prices.json")
    with open(path) as f:
        return json.load(f)

def get_meta():
    return load_prices()["_meta"]