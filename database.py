import pymongo
from bson.objectid import ObjectId
import requests
import settings
import json
from pprint import pprint
from random import randint
from numpy.random import choice
import tiers

client = pymongo.MongoClient(settings.MONGO_URI)

pokemon_db = client.pokemaster.pokemon
users_db = client.pokemaster.users
moves_db = client.pokemaster.moves

pokeapi_url = "https://pokeapi.co/api/v1"

def mongo_get(database, id=None, user=None):
	"""
	Calls MongoDB and returns the pokemon object specified by its id
	"""
	if database.name in ('pokemon', 'users'):
		return database.find_one({'national_id': id})


def api_get(type, id):
	"""
	Calls the api and returns the object specified by its id
	"""
	if type == 'pokemon':
		return json.loads(requests.get('{}/pokemon/{}'.format(pokeapi_url, id)).text)


def get_pokemon(id):
	# check mongo for pokemon
	pkmn = mongo_get(pokemon_db, id)
	if (pkmn is None):
		# if not in mongo, request the pokemon from pokeapi and save in database
		print("calling api")
		pkmn = api_get('pokemon', id)
		pokemon_db.insert_one(pkmn)
	print(pkmn['name'])
	return pkmn


def get_random_pokemon():
	rarity = choice(5, 1, p=[0.45, 0.25, .15, .10, .05])
	print(rarity[0])
	id_list = tiers.TIERS[str(rarity[0])]
	id = id_list[randint(0, len(id_list) - 1)]
	return get_pokemon(id)


def add_pokemon(user, pokemon, shiny=False):
	users_db[user]["storage"].insert_one({
		"national_id": pokemon["national_id"],
		"name": pokemon["name"],
		"candies": 1,
		"evolution": pokemon["evolutions"],
		"shiny": shiny
	})


def get_storage(user):
	"""
	Retrieves a list of pokemon dicts from a user's storage
	[{"name": "pikachu", "id": 99} ... ] 
	"""
	storage = users_db[user]["storage"].find({})
	pkmn_list = []
	for pkmn in storage:
		if "shiny" in pkmn.keys() and pkmn["shiny"]:
			pkmn_list.append({"name": "✪" + pkmn["name"], "id":pkmn["national_id"]})
		else:
			pkmn_list.append({"name": pkmn["name"], "id":pkmn["national_id"]})
	return pkmn_list


def add_to_party(user, pkmn_id):
	# check if exists on storage
	if users_db[user]["storage"].find_one({"national_id": pkmn_id}):
		return

	# remove from storage

	# add to party
