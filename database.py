import pymongo
from bson.objectid import ObjectId
import requests
import settings
import json
from pprint import pprint
from random import randint

client = pymongo.MongoClient(settings.MONGO_URI)

pokemon_db = client.pokemaster.pokemon
users_db = client.pokemaster.users
moves_db = client.pokemaster.moves

pokeapi_url = "https://pokeapi.co/api/v1"

def mongo_get(database, id):
	"""
	Calls MongoDB and returns the object specified by its id
	"""
	if database.name == 'pokemon':
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
	id = randint(1,718)
	return get_pokemon(id)
