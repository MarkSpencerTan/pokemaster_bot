import pymongo
import requests
import settings
import json
from pprint import pprint
from random import randint
from numpy.random import choice
import tiers
import effectiveness

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
    elif type == 'uri':
        return json.loads(requests.get("https://pokeapi.co" + id).text)


def get_pokemon(id):
    # check mongo for pokemon
    pkmn = mongo_get(pokemon_db, id)
    if pkmn is None:
        # if not in mongo, request the pokemon from pokeapi and save in database
        print("calling api")
        pkmn = api_get('pokemon', id)
        pokemon_db.insert_one(pkmn)
    return pkmn


def get_pokemon_name(id):
    # returns pokemon name from their id
    pkmn = mongo_get(pokemon_db, id)
    return pkmn["name"]


def get_random_pokemon(type=None):
    if type is None:
        # the base rate
        rarity = choice(5, 1, p=[0.50, 0.27, .18, .04, .01])
    elif type == "great":
        rarity = choice(5, 1, p=[0.20, 0.40, .30, .08, .02])
    elif type == "ultra":
        rarity = choice(5, 1, p=[0.10, 0.30, .30, .26, .04])
    elif type == "master":
        rarity = choice(5, 1, p=[0, 0, 0, 0, 1])
    elif type == "battle":
        rarity = choice(5, 1, p=[0.35, 0.30, .20, .10, .05])
    id_list = tiers.TIERS[str(rarity[0])]
    id = id_list[randint(0, len(id_list) - 1)]
    return get_pokemon(int(id))


def get_random_description(desc_list):
    """
    desc_list : a list of description objects returned from the pokemon["description"]
    They have a resource_uri that we will use as an api uri to get the actual description
    This will retrieve a random description from that list.
    """
    rand = randint(0, len(desc_list)-1)
    desc_uri = desc_list[rand]["resource_uri"]
    description = api_get("uri", desc_uri)["description"]
    return description


def add_pokemon(user, pokemon, shiny=False):
    users_db[user]["storage"].insert_one({
        "national_id": pokemon["national_id"],
        "name": pokemon["name"],
        "health": pokemon["hp"],
        "hp": pokemon["hp"],
        "attack": pokemon["attack"],
        "defense": pokemon["defense"],
        "sp_atk": pokemon["sp_atk"],
        "sp_def": pokemon["sp_def"],
        "speed": pokemon["speed"],
        "candies": 1,
        "evolutions": pokemon["evolutions"],
        "shiny": shiny,
        "friendship": 0,
        "item": None
    })


def get_storage(user):
    """
    Retrieves a list of pokemon dicts from a user's storage
    [{"name": "pikachu", "id": 99} ... ] 
    """
    storage = users_db[user]["storage"].find({})
    pkmn_list = []
    for pkmn in storage:
        icons = ""
        if pkmn["health"] <= 0:
            icons += ":skull:"
        if "shiny" in pkmn.keys() and pkmn["shiny"]:
            icons += "✪"
        pkmn_list.append({"name": icons + pkmn["name"], "id":pkmn["national_id"]})
    return pkmn_list


def get_party(user) -> list:
    """
    Retrieves a list of pokemon dicts from a user's party
    [{"name": "pikachu", "nationa_id": 99} ... ]
    """
    return users_db[user]["party"].find({})


def add_to_party(user, pkmn_id):
    # check if exists on storage
    pkmn = users_db[user]["storage"].find_one({"national_id": pkmn_id})
    if pkmn:
        # check if there's space on party
        party = users_db[user]["party"].find({})
        if party.count() < 6:
            # remove from storage
            users_db[user]["storage"].delete_one(pkmn)
            # add to party
            users_db[user]["party"].insert_one(pkmn)
            return True
        else:
            return False
    return False


def remove_from_party(user, pkmn_id):
    # check if exists on party
    pkmn = users_db[user]["party"].find_one({"national_id": pkmn_id})
    if pkmn:
        # remove from storage
        users_db[user]["party"].delete_one(pkmn)
        # add to party
        users_db[user]["storage"].insert_one(pkmn)
        return True
    return False


def remove_all_party(user):
    for pkmn in get_party(user):
        remove_from_party(user, pkmn["national_id"])
    return True


def release_from_party(user, pkmn_id):
    # check if exists on party
    pkmn = users_db[user]["party"].find_one({"national_id": pkmn_id})
    if pkmn is not None:
        # remove from storage
        users_db[user]["party"].delete_one(pkmn)
        return True
    return False


def save_party_pkmn_state(user, pkmn):
    """
    Saves the state of the party pokemon to the database
    """
    users_db[user]["party"].update({'_id': pkmn["_id"]}, {"$set": pkmn}, upsert=False)
    return True


def heal_party(user):
    """
    Restores all the HP of party pokemon back to full
    """
    party = get_party(user)
    for pkmn in party:
        pkmn["health"] = pkmn["hp"]
        users_db[user]["party"].update({'_id': pkmn["_id"]}, {"$set": pkmn}, upsert=False)


def is_caught(user, pkmn_id):
    pkmn_id = int(pkmn_id)
    if users_db[user]["party"].find_one({"national_id": pkmn_id}) is not None:
        return True
    elif users_db[user]["storage"].find_one({"national_id": pkmn_id}) is not None:
        return True
    else:
        return False


def get_total_caught(user):
    """
    Gets the total number of UNIQUE pokemon caught
    """
    unique_storage = users_db[user]["storage"].distinct("national_id")
    unique_party = users_db[user]["party"].distinct("national_id")
    unique_caught = unique_party + list(set(unique_storage) - set(unique_party))
    return len(unique_caught)


def get_pokedollars(user):
    query = users_db[user].find_one({"pokedollars": {'$exists': True}})
    if query is None:
        users_db[user].insert_one({
            "pokedollars": 0
        })
        return 0
    else:
        return query["pokedollars"]


def add_pokedollars(user, amount):
    query = users_db[user].find_one({"pokedollars": {'$exists': True}})
    if query is None:
        users_db[user].insert_one({
            "pokedollars": amount
        })
        return True
    else:
        if query["pokedollars"] <= 0:
            query["pokedollars"] = 0
        else:
            query["pokedollars"] = query["pokedollars"] + amount
        users_db[user].update({'_id': query["_id"]}, {"$set": query}, upsert=False)
        return True


