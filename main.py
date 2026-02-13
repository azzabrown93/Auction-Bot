import requests
import time
import os

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

MIN_PROFIT = 40      # Auctions need bigger margins
MAX_PRICE = 300     # Avoid expensive traps
SCAN_DELAY = 420    # 7 minutes (human behaviour)

SEARCH_TERMS = [

    # Cameras / lenses (ELITE)
    "canon lens auction",
    "sony lens auction",
    "nikon lens auction",
    "sigma lens auction",

    # Power tools
    "dewalt drill auction",
    "milwaukee tool auction",
    "makita drill auction",

    # Bundles / chaos listings
    "camera bundle auction",
    "tool bundle auction",
    "job lot electronics auction",
    "lego job lot auction",

    # Audio / music
    "dj equipment auction",
    "guitar bundle auction",
    "focusrite auction"
]


############################################

def send_discord(msg):

    requests.post(
        DISCORD_WEBHOOK,
        json={"content": msg}
    )

############################################

def get_ebay_results(query):

    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"

    headers = {
        "Authorization": f"Bearer {EBAY_TOKEN}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_GB"
    }

    params = {
        "q": query,
        "filter": "buyingOptions:{AUCTION}",
        "sort": "newlyListed",
        "limit": 25
    }

    r = requests.get(url, headers=headers, params=params)

    return r.json().get("itemSummaries", [])

############################################

def get_ebay_token():

    import base64

    creds = f"{os.getenv('EBAY_CLIENT_ID')}:{os.getenv('EBAY_CLIENT_SECRET')}"
    encoded = base64.b64encode(creds.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded}",
        "Content-Type":"application/x-www-form-urlencoded"
    }

    data = {
        "grant_type":"client_credentials",
        "scope":"https://api.ebay.com/oauth/api_scope"
    }

    r = requests.post(
        "https://api.ebay.com/identity/v1/oauth2/token",
        headers=headers,
        data=data
    )

    return r.json()["access_token"]

############################################

def estimate_resale(title):

    # simple resale check
    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"

    headers = {
        "Authorization": f"Bearer {EBAY_TOKEN}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_GB"
    }

    params = {
        "q": title,
        "filter": "soldItemsOnly:true",
        "limit": 15
    }

    r = requests.get(url, headers=headers, params=params)

    items = r.json().get("itemSummaries", [])

    prices = []

    for i in items:
        try:
            prices.append(float(i["price"]["value"]))
        except:
            pass

    if len(prices) < 5:
        return None

    return sum(prices)/len(prices)

############################################

print("🚀 AUCTION INTELLIGENCE BOT LIVE")

EBAY_TOKEN = get_ebay_token()
LAST_REFRESH = time.time()

SEEN = set()

while True:

    try:

        # refresh token
        if time.time() - LAST_REFRESH > 7000:
            EBAY_TOKEN = get_ebay_token()
            LAST_REFRESH = time.time()

        for term in SEARCH_TERMS:

            print("Scanning:", term)

            items = get_ebay_results(term)

            for item in items:

                title = item["title"]
                link = item["itemWebUrl"]

                if link in SEEN:
                    continue

                price = float(item["price"]["value"])

                if price > MAX_PRICE:
                    continue

                resale = estimate_resale(title)

                if not resale:
                    continue

                profit = resale - price

                if profit >= MIN_PROFIT:

                    msg = f"""
🚨 **AUCTION SNIPER HIT**

{title}

Current Bid: £{price}
Est Resale: £{round(resale,2)}

🔥 Profit: £{round(profit,2)}

{link}
"""

                    send_discord(msg)

                    print("SNIPED:", title)

                    SEEN.add(link)

        print("Sleeping...\n")
        time.sleep(SCAN_DELAY)

    except Exception as e:

        print("ERROR:", e)
        EBAY_TOKEN = get_ebay_token()
        time.sleep(120)
