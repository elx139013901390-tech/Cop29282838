import requests

API = "https://open.er-api.com/v6/latest/USD"

def get_rates():
    r = requests.get(API, timeout=10)

    if r.status_code != 200:
        return None

    data = r.json()

    if data["result"] != "success":
        return None

    return data["rates"]
