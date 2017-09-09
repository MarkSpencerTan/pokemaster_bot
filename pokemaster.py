######################################################
#   Pokemaster Discord Bot
#   Developer: Mark Spencer Tan
#   Version: 01.00.00
######################################################

from discord.ext.commands import Bot
from discord import Client
from discord.ext.commands.cooldowns import BucketType
from discord.embeds import Embed
from random import randint
import discord.ext.commands as commands
import threading
import traceback

import sys
sys.path.append(".")

import database
import settings
import emojis
import tiers    


pokemaster_bot = Bot(command_prefix="!")

@pokemaster_bot.event
async def on_command_error(ctx, error):
    try:
        user = str(error.message.author).split("#")[0]
        message = "Oak: **{}** keep your pokeballs calm, and wait {} seconds."
        await pokemaster_bot.send_message(error.message.channel, message.format(user, int(ctx.retry_after)))
    except:
        tb = "\n".join(traceback.format_tb(error.original.__traceback__))
        print("{}: {}\n{}".format(error.original.__class__.__name__, str(error), str(tb)))


@commands.cooldown(1, 20, type=BucketType.user)
@pokemaster_bot.command(pass_context=True)
async def poke(ctx, *args):
    message = ctx.message
    command = args[0]
    if command == 'battle':
        return await battle(message)
    elif command == 'members':
        return await get_members()
    elif command == 'catch':
        return await catch(message)
    await pokemaster_bot.say("Invalid Command")


@commands.cooldown(1, 4, type=BucketType.user)
@pokemaster_bot.command(pass_context=True)
async def storage(ctx, *args):
    message = ctx.message
    box = 1
    rarity = None
    sorted = False
    for arg in args:
        if arg in ('common', 'rare', 'uncommon', 'ultra', 'legendary', 'eevee'):
            rarity = arg
        elif arg == 'sorted':
            sorted = True
        elif int(arg) in list(range(9999)):
            box = int(arg)
    if rarity == 'eevee':
        return await show_eevees(message, box=box, is_sorted=sorted)
    if rarity is not None:
        return await show_storage_by_rarity(message, rarity, box=box, is_sorted=sorted)
    return await show_storage(message, box=box, is_sorted=sorted)


@commands.cooldown(1, 2, type=BucketType.user)
@pokemaster_bot.command(pass_context=True)
async def party(ctx, *args):
    author = ctx.message.author
    operation = None
    pkmn_id = None
    result = True
    for arg in args:
        if arg in ('add', 'remove', 'release'):
            operation = arg
        elif int(arg) in list(range(721)):
            pkmn_id = int(arg)
    if operation == 'add':
        result = database.add_to_party(author, pkmn_id)
    if operation == 'remove':
        result = database.remove_from_party(author, pkmn_id)
    if operation == 'release':
        result == database.release_from_party(author, pkmn_id)
        await pokemaster_bot.say("Oak: Don't worry I'll take care of {} ;)".format(database.get_pokemon_name(pkmn_id)))
    if not result:
        return await pokemaster_bot.say("**Oak**: Make sure you actually have that pokemon or if your party is not full ya scrub.")

    return await show_party(author)


@commands.cooldown(1, 5, type=BucketType.user)
@pokemaster_bot.command(pass_context=True)
async def pokedex(ctx, *args):
    if len(args) > 0:
        # gets the pokedex entry if passed a pokemon id
        return await get_pokedex(ctx.message.author, args[0])
    else:
        # gets the total number of unique pokemon caught
        author = str(ctx.message.author).split("#")[0]
        total_caught = database.get_total_caught(ctx.message.author)
        message = "Oak: Congratulations **{}**, you caught {}/718 pokemon"
        return await pokemaster_bot.say(message.format(author, total_caught))


async def get_members():
    members = pokemaster_bot.get_all_members()
    response = ""
    for member in members:
        response += str(member) + "\n"
    return await pokemaster_bot.say(response)


async def catch(message):
    pkmn = database.get_random_pokemon()
    pkmn_id = pkmn["national_id"]
    pkmn_name = pkmn["name"]

    color = _get_tier_color(pkmn_id)
    type_str = _get_types_string(pkmn["types"])

    # random generator if shiny
    shiny_chance = randint(1,100)
    if shiny_chance < 2:
        shiny = True
        description = "**{}** You have caught :star2:**{}**".format(message.author, pkmn_name)
    else:
        shiny = False
        description = "**{}** You have caught **{}**".format(message.author, pkmn_name)

    embed = Embed(color=color, description=description)

    if shiny:
        embed.set_image(url="http://www.pkparaiso.com/imagenes/xy/sprites/animados-shiny/{}.gif".format(pkmn_name.lower()))
    else:
        embed.set_image(url="http://www.pkparaiso.com/imagenes/xy/sprites/animados/{}.gif".format(pkmn_name.lower()))

    embed.add_field(name='Name', value="{}[{}]".format(pkmn_name, pkmn_id))
    embed.add_field(name="Types", value=type_str)
    # embed.add_field(name='Hp', value=pkmn["hp"])
    # embed.add_field(name='Attack', value=pkmn["attack"])
    # embed.add_field(name='Defense', value=pkmn["defense"])
    # embed.add_field(name='Speed', value=pkmn["speed"])
    embed.set_thumbnail(url="http://marktan.us/pokemon/img/icons/{}.png".format(pkmn_id))

    # add the pokemon to the user db
    database.add_pokemon(message.author, pkmn, shiny=shiny)
    await pokemaster_bot.say(embed=embed)


async def battle(message):
    author = message.author
    pkmn = database.get_random_pokemon(type="battle")
    pkmn_id = pkmn["national_id"]
    tier = _get_tier(int(pkmn_id))
    pkmn_name = pkmn["name"]

    party = database.get_party(author)
    # for my_pkmn in party:
    #     result = _damage_calc(author, my_pkmn, pkmn)
    #     result = trainer_damage_calc(author1, pkmn1, author2, pkmn2)
    

def _dmg_calc(author, pkmn, enemy):
    """
    Damage calculation for a battle. saves the state of the pkmn to the
    user's database.
    :return: the pkmn object with its state after the battle
    """
    # have to get the full pkmn from the db
    health = pkmn["health"]
    my_stats = database.get_pokemon(pkmn["national_id"])

async def show_storage(message, is_sorted=False, box=1):
    embed = Embed(color=0x000000, description="**{}**'s Pkmn at Professor Oak's Slavehouse".format(message.author))
    
    pkmn_list = database.get_storage(message.author)
    
    boxes = []
    storage_list = ""
    count = 0
    for pkmn in pkmn_list:
        count += 1
        storage_list += "{}[{}]\t".format(pkmn["name"], str(pkmn["id"]))
        if count == 30:
            boxes.append(storage_list)
            storage_list = ""
            count = 0
    boxes.append(storage_list)
    try:
        storage_list = boxes[box-1]
    except IndexError:
        return await pokemaster_bot.say("Oak: There's nothing in that box because you haven't caught enough pokemon m8. Git gud.")

    if is_sorted:
        storage_list = storage_list.split("\t")
        storage_list = sorted(storage_list)
        storage_list = "\t".join(storage_list)

    embed.add_field(name="Storage [**{}**/{}]".format(box, len(boxes)), value=storage_list, inline=True)
    await pokemaster_bot.say(embed=embed)


async def show_eevees(message, is_sorted=True, box=1):
    color = 0xffffff
    description = "**{}**'s Eevee Collection".format(message.author)

    embed = Embed(color=color, description=description)

    pkmn_list = database.get_storage(message.author)

    boxes = []
    storage_list = ""
    count = 0
    for pkmn in pkmn_list:
        id = pkmn["id"]
        if id in tiers.EEVEES:
            count += 1
            storage_list += "{}[{}]\t".format(pkmn["name"], str(pkmn["id"]))
            if count == 30:
                boxes.append(storage_list)
                storage_list = ""
                count = 0
    boxes.append(storage_list)
    try:
        storage_list = boxes[box - 1]
    except IndexError:
        return await pokemaster_bot.say(
            "Oak: There's nothing in that box because you haven't caught enough pokemon m8. Git gud.")

    if is_sorted:
        storage_list = storage_list.split("\t")
        storage_list = sorted(storage_list)
        storage_list = "\t".join(storage_list)

    embed.add_field(name="Storage [**{}**/{}]".format(box, len(boxes)), value=storage_list, inline=True)
    return await pokemaster_bot.say(embed=embed)


async def show_storage_by_rarity(message, rarity, is_sorted=True, box=1):
    color = 0xB80800
    tier = ""
    print("rarity: {}".format(rarity))
    if rarity == 'common':
        color = 0x000000
        tier = "0"
    if rarity == 'uncommon':
        color = 0xB80800
        tier = "1"
    if rarity == 'rare':
        color = 0x0009C4
        tier = "2"
    if rarity == 'ultra':
        color = 0xF7AB09
        tier = "3"
    if rarity == 'legendary':
        color = 0x9909F7
        tier = "4"
    description = "**{}**'s {} Pokemon".format(message.author, rarity)

    embed = Embed(color=color, description=description)

    pkmn_list = database.get_storage(message.author)
    
    boxes = []
    storage_list = ""
    count = 0
    for pkmn in pkmn_list:
        id = pkmn["id"]
        if id in tiers.TIERS[tier]:
            count += 1
            storage_list += "{}[{}]\t".format(pkmn["name"], str(pkmn["id"]))
            if count == 30:
                boxes.append(storage_list)
                storage_list = ""
                count = 0
    boxes.append(storage_list)
    try:
        storage_list = boxes[box-1]
    except IndexError:
        return await pokemaster_bot.say(
            "Oak: There's nothing in that box because you haven't caught enough pokemon m8. Git gud.")

    if is_sorted:
        storage_list = storage_list.split("\t")
        storage_list = sorted(storage_list)
        storage_list = "\t".join(storage_list)

    embed.add_field(name="Storage [**{}**/{}]".format(box, len(boxes)), value=storage_list, inline=True)
    return await pokemaster_bot.say(embed=embed)


async def show_party(author):
    embed = Embed(color=0xB80800, description="**{}**'s Party Pokemon".format(author))
    
    party_list = database.get_party(author)
    for pkmn in party_list:
        pkmn_string = "Hp:{}\t Candies:{}".format("100%" ,pkmn["candies"])
        embed.add_field(name="**{}**[{}]".format(pkmn["name"], str(pkmn["national_id"])), value=pkmn_string, inline=True)   
    await pokemaster_bot.say(embed=embed)


async def get_pokedex(author, pkmn_id):
    embed = Embed(color=0xB80800, description="**{}**'s Party Pokemon".format(author))

    if database.is_caught(author, pkmn_id):
        pkmn = database.get_pokemon(pkmn_id)
        pkmn_id = pkmn["national_id"]
        pkmn_name = pkmn["name"]

        color = _get_tier_color(pkmn_id)
        types = _get_types_string(pkmn["types"])

        description = database.get_random_description(pkmn["descriptions"])

        embed.add_field(name='Name', value="{} [{}]".format(pkmn_name, pkmn_id))
        embed.add_field(name="Types", value=types, inline=True)
        embed.add_field(name='Description', value=description, inline=False)
        embed.add_field(name='Hp', value=pkmn["hp"], inline=True)
        embed.add_field(name='Attack', value=pkmn["attack"], inline=True)
        embed.add_field(name='Defense', value=pkmn["defense"], inline=True)
        embed.add_field(name='Speed', value=pkmn["speed"], inline=True)
        embed.set_image(url="http://www.pkparaiso.com/imagenes/xy/sprites/animados/{}.gif".format(pkmn_name.lower()))
        embed.set_thumbnail(url="http://marktan.us/pokemon/img/icons/{}.png".format(pkmn_id))
        return await pokemaster_bot.say(embed=embed)
    else:
        return await pokemaster_bot.say("Oak: You can't see what you don't have.")


def _get_types_string(types_list):
    """
    Returns a string formatted with the emojis corresponding to the pokemon types
    """
    type_str = ""
    for type in types_list:
        type_str += "{} {} ".format(emojis.get_emoji(type['name']), type['name'])
    return type_str


def _get_tier_color(pkmn_id):
    """
    Returns the color code of the tier that the pokemon belongs in
    """
    if pkmn_id in tiers.TIERS["0"]:
        return 0x000000
    elif pkmn_id in tiers.TIERS["1"]:
        return 0xB80800
    elif pkmn_id in tiers.TIERS["2"]:
        return 0x0009C4
    elif pkmn_id in tiers.TIERS["3"]:
        return 0xF7AB09
    else:
        return 0x9909F7


def _get_tier(pkmn_id):
    """
    Returns the tier number that the pokemon belongs in
    """
    if pkmn_id in tiers.TIERS["0"]:
        return 0
    elif pkmn_id in tiers.TIERS["1"]:
        return 1
    elif pkmn_id in tiers.TIERS["2"]:
        return 2
    elif pkmn_id in tiers.TIERS["3"]:
        return 3
    else:
        return 4


def _get_money_earned(tier):
    """
    returns the money you get from beating a pokemon based on its tier
    """
    return int(((tier**2) * 10) + 10)


# run the bot forever
while True:
    try:
        pokemaster_bot.run(settings.BOT_TOKEN)
    except KeyboardInterrupt:
        print('Closing Bot')
        break
    except:
        pass