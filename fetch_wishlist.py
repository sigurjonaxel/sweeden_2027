#!/usr/bin/env python3
"""
Sækir gögn úr Airbnb óskalista og vistar sem JSON.
"""

import urllib.request
import urllib.parse
import json
import base64
import sys

API_KEY = "d306zoyjsyarp7ifhu67rjxn52tv0t20"
OP_ID = "5f6b671df39f7e5c9ffc249e202d303d71ae50ed46992749740e465c9890801a"
OP_NAME = "WishlistDetailPageDataQuery"

DEFAULT_LIST_ID = "2132333760"
DEFAULT_SHARE_TOKEN = "cdff32ff-1dc0-4e36-9132-29b438634208"

def fetch_wishlist(list_id=DEFAULT_LIST_ID, share_token=DEFAULT_SHARE_TOKEN, currency="EUR"):
    url = f"https://www.airbnb.com/api/v3/{OP_NAME}/{OP_ID}"
    gid = base64.b64encode(f"Wishlist:{list_id}".encode("utf-8")).decode("utf-8")
    
    variables = {"wishlistID": gid}
    params = urllib.parse.urlencode({
        "operationName": OP_NAME,
        "locale": "en",
        "currency": currency,
        "variables": json.dumps(variables),
        "extensions": json.dumps({
            "persistedQuery": {
                "version": 1,
                "sha256Hash": OP_ID
            }
        }),
        "principal_token": share_token
    })
    
    req = urllib.request.Request(
        f"{url}?{params}",
        headers={
            "X-Airbnb-API-Key": API_KEY,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    )
    
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

if __name__ == "__main__":
    print("Sæki gögn úr Airbnb óskalista...")
    data = fetch_wishlist()
    with open("wishlist_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Gögn vistuð í wishlist_data.json!")
