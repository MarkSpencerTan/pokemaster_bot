import requests
from pprint import pprint
r = requests.get("http://pokeapi.co/api/v2/pokedex/1")
#pprint(r.json()["pokemon_entries"])

regpath = "regular/"
shinypath = "shiny/"

import os
for pkmn in r.json()["pokemon_entries"]:
	id = str(pkmn["entry_number"])
	name = pkmn["pokemon_species"]["name"]
	for file in os.listdir(regpath):
		if file.split(".")[0] == name:
			os.rename(os.path.join(regpath, file), os.path.join(regpath, file.replace(name, id)))
			os.rename(os.path.join(shinypath, file), os.path.join(shinypath, file.replace(name, id)))
			break
