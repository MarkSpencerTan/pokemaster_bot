import requests

r = requests.get("https://api.heroku.com/apps/pokemasterbot/config-vars").json()
print(r)

CLIENT_ID = r.get("CLIENT_ID")
CLIENT_SECRET = r.get("CLIENT_SECRET")
BOT_TOKEN = r.get("BOT_TOKEN")
MONGO_URI = r.get("MONGO_URI")

SHINY_RATE = .02
BOT_ADMIN = ["Marko Spencer#0713"]
BOT_PREFIX = "!"
