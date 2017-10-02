import requests

r = requests.get("https://api.heroku.com/apps//config-vars").json()

CLIENT_ID = r["CLIENT_ID"]
CLIENT_SECRET = r["CLIENT_SECRET"]
BOT_TOKEN = r["BOT_TOKEN"]
MONGO_URI = r["MONGO_URI"]

SHINY_RATE = .02
BOT_ADMIN = ["Marko Spencer#0713"]
BOT_PREFIX = "!"
