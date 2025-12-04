# main.py
import json

import requests
from requests.auth import HTTPBasicAuth
from dotenv import dotenv_values


# def hello():
#     print("hello world")


# if __name__ == "__main__":
#     hello()

config = dotenv_values(".env")
# print(config)
ID = 184287513
url = f"https://{config['DOMAIN']}/wiki/api/v2/folders/{ID}"

auth = HTTPBasicAuth(config["EMAIL"], config["API_TOKEN"])

headers = {"Accept": "application/json"}

params = {"include-direct-children": "true"}

response = requests.request(
    "GET", url, headers=headers, auth=auth, params=params, timeout=1000
)

print(
    json.dumps(
        json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")
    )
)
