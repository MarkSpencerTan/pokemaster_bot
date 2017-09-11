######################################################
#   Pokemaster Discord Bot
#   Developer: Mark Spencer Tan
#   Version: 01.01.00
######################################################

from discord.ext.commands import Bot
from discord.ext.commands.cooldowns import BucketType
from discord.embeds import Embed
from random import randint
import discord.ext.commands as commands
from pprint import pprint
import traceback
import random

import sys
sys.path.append(".")

import database
import settings
import emojis
import tiers
import effectiveness


pokemaster_bot = Bot(command_prefix="!")


# @pokemaster_bot.event
# async def on_command_error(ctx, error):
#     try:
#         user = str(error.message.author).split("#")[0]
#         message = "Oak: **{}** keep your pokeballs calm, and wait {} seconds."
#         await pokemaster_bot.send_message(error.message.channel, message.format(user, int(ctx.retry_after)))
#     except:
#         tb = "\n".join(traceback.format_tb(error.original.__traceback__))
#         print("{}: {}\n{}".format(error.original.__class__.__name__, str(error), str(tb)))


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
        if arg in ('add', 'remove', 'release', 'removeall'):
            operation = arg
        elif int(arg) in list(range(721)):
            pkmn_id = int(arg)
    if operation == 'add':
        result = database.add_to_party(author, pkmn_id)
    elif operation == 'remove':
        result = database.remove_from_party(author, pkmn_id)
    elif operation == 'removeall':
        result = database.remove_all_party(author)
    elif operation == 'release':
        result = database.release_from_party(author, pkmn_id)
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
        return await get_trainer_info(ctx.message.author)


@commands.cooldown(1, 150, type=BucketType.user)
@pokemaster_bot.command(pass_context=True)
async def pokecenter(ctx, *args):
    author = ctx.message.author
    database.add_pokedollars(author, -150)
    database.heal_party(author)

    embed = Embed(color=0xB80800, description="**{}** Welcome to the Pokemon Center!".format(author))
    embed.set_author(name="Nurse Joy", icon_url="https://i.pinimg.com/originals/ed/47/7c/ed477c99f4776886de48d5789f25776d.jpg")
    embed.add_field(name="Your Pokemon are healed!", value="Thanks for coming in. Please Come again ;)", inline=False)
    embed.set_footer(text="Nurse Joy charged you ₱150 for her services. She ain't messin with no broke broke.")
    embed.set_image(url="https://cdn.bulbagarden.net/upload/thumb/9/9f/Nurse_Joy_anime_SM.png/250px-Nurse_Joy_anime_SM.png")
    return await pokemaster_bot.say(embed=embed)


@commands.cooldown(1, 2, type=BucketType.user)
@pokemaster_bot.command(pass_context=True)
async def pokedollar(ctx, *args):
    author = ctx.message.author
    balance = database.get_pokedollars(author)
    return await pokemaster_bot.say(":dollar: | **{} you have ₱{}**".format(author, balance))


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
    pkmn_name_stripped = pkmn_name.lower().split("-")[0]

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
        embed.set_image(url="http://www.pkparaiso.com/imagenes/xy/sprites/animados-shiny/{}.gif".format(pkmn_name_stripped))
    else:
        embed.set_image(url="http://www.pkparaiso.com/imagenes/xy/sprites/animados/{}.gif".format(pkmn_name_stripped))

    embed.add_field(name='Name', value="{}[{}]".format(pkmn_name, pkmn_id))
    embed.add_field(name="Types", value=type_str)
    embed.set_thumbnail(url="http://marktan.us/pokemon/img/icons/{}.png".format(pkmn_id))

    # add the pokemon to the user db
    database.add_pokemon(message.author, pkmn, shiny=shiny)
    await pokemaster_bot.say(embed=embed)


async def battle(message):
    author = message.author
    wild_pkmn = database.get_random_pokemon(type="battle")
    wild_pkmn_id = wild_pkmn["national_id"]
    wild_pkmn["health"] = wild_pkmn["hp"]
    wild_pkmn_name = wild_pkmn["name"]
    wild_pkmn_name_stripped = wild_pkmn_name.lower().split("-")[0]

    tier = _get_tier(int(wild_pkmn_id))
    prize_money = _get_money_earned(tier)

    party = database.get_party(author)
    fainted = []
    winner = None
    fought_pkmn = []
    for my_pkmn in party:
        if my_pkmn["health"] <= 0:
            last_pkmn = my_pkmn
            continue
        wild_pkmn["health"] = _fight_wild(author, my_pkmn, wild_pkmn)
        fought_pkmn.append(my_pkmn)
        last_pkmn = my_pkmn
        if wild_pkmn["health"] <= 0:
            winner = my_pkmn
            last_pkmn = my_pkmn
            break
        else:
            fainted.append(my_pkmn["name"])
    if len(fought_pkmn) == 0:
        return await pokemaster_bot.say("Oak: Are you trying to fight the pokemon with your fist? Add some pokemon to your party first.")

    color = _get_tier_color(wild_pkmn_id)
    embed = Embed(color=color, description="**{}** you encountered **{}**".format(message.author, wild_pkmn_name_stripped))
    embed.set_thumbnail(url="http://marktan.us/pokemon/img/icons/{}.png".format(last_pkmn["national_id"]))
    # embed.add_field(name="Fainted Pokemon", value=", ".join(fainted))
    embed.set_image(
        url="http://www.pkparaiso.com/imagenes/xy/sprites/animados/{}.gif".format(wild_pkmn_name.lower()))

    if winner is None:
        # do losing message here
        embed.add_field(name="Oak", value="Your party pokemon was wiped out. Get rekt m8")
        # deduct money
        database.add_pokedollars(author, prize_money * -1)
    else:
        # do winning embed here
        winner_name = winner["name"]
        health_remaining = int((winner["health"]/winner["hp"]) * 100)
        text1 = "has {}% health remaining after the fight".format(health_remaining)
        embed.add_field(name="{} won the fight!".format(winner_name), value=text1, inline=False)
        embed.add_field(name="Pokedollars Earned", value="₱{}".format(prize_money))
        # add prize money
        database.add_pokedollars(author, prize_money)
    return await pokemaster_bot.say(embed=embed)



def _fight_wild(author, pkmn, enemy):
    """
    Your pkmn vs wild pkmn. saves the state of the user's pkmn to the
    user's database at the end of the fight
    :return: The remaining health of the enemy
    """
    while True:
        if pkmn["speed"] > enemy["speed"]:
            # you go first
            enemy["health"] = _attack(pkmn, enemy)
            if enemy["health"] <= 0:
                break
            pkmn["health"] = _attack(enemy, pkmn)
            if pkmn["health"] <= 0:
                break
        else:
            # enemy goes first
            pkmn["health"] = _attack(enemy, pkmn)
            if pkmn["health"] <= 0:
                break
            enemy["health"] = _attack(pkmn, enemy)
            if enemy["health"] <= 0:
                break
    # round the health to nearest int
    pkmn["health"] = int(pkmn["health"])
    database.save_party_pkmn_state(author, pkmn)
    return enemy["health"]


def _attack(pkmn1, pkmn2) -> int:
    """
    pkmn1 attacks pkmn2
    :return: Return pkmn2's health after the battle
    """
    pkmn1_obj = database.get_pokemon(pkmn1["national_id"])
    pkmn2_obj = database.get_pokemon(pkmn2["national_id"])

    eff = _get_effectiveness(pkmn1_obj["types"], pkmn2_obj["types"])
    r = random.uniform(0.8, 1.2)
    power = (pkmn1["attack"] + pkmn1["sp_atk"])/2 * eff * 30
    power /= (pkmn2["defense"] + pkmn2["sp_def"])/2
    # print("effectiveness: %s rand: %s power: %d" % (eff, r, power))
    pkmn2["health"] -= power

    if pkmn2["health"] <= 0:
        return 0
    return pkmn2["health"]


def _get_effectiveness(types1: list, types2: list):
    """
    :param types1, types2 are list of {'name': 'poison', 'resource_uri': ...}
    :return: ratio of effectiveness of types1 to types2
    """
    ratio = 1.0
    for type1 in types1:
        for type2 in types2:
            try:
                ratio = ratio * effectiveness.chart[type1["name"]][type2["name"]]
            except KeyError:
                continue
    return ratio


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
        pkmn_string = "Hp:[{}/{}]\t Candies:{}".format(pkmn["health"], pkmn["hp"], pkmn["candies"])
        embed.add_field(name="**{}**[{}]".format(pkmn["name"], str(pkmn["national_id"])), value=pkmn_string, inline=False)
    await pokemaster_bot.say(embed=embed)


async def get_pokedex(author, pkmn_id):
    color = _get_tier_color(int(pkmn_id))
    embed = Embed(color=color, description="**{}**'s Pokedex".format(author))

    if database.is_caught(author, pkmn_id):
        pkmn = database.get_pokemon(pkmn_id)
        pkmn_id = pkmn["national_id"]
        pkmn_name = pkmn["name"]
        pkmn_name_stripped = pkmn_name.lower().split("-")[0]

        types = _get_types_string(pkmn["types"])

        description = database.get_random_description(pkmn["descriptions"])

        embed.add_field(name='Name', value="{} [{}]".format(pkmn_name, pkmn_id))
        embed.add_field(name="Types", value=types, inline=True)
        embed.add_field(name='Description', value=description, inline=False)
        embed.add_field(name='Hp', value=pkmn["hp"], inline=True)
        embed.add_field(name='Attack', value=pkmn["attack"], inline=True)
        embed.add_field(name='Defense', value=pkmn["defense"], inline=True)
        embed.add_field(name='Speed', value=pkmn["speed"], inline=True)
        embed.set_image(url="http://www.pkparaiso.com/imagenes/xy/sprites/animados/{}.gif".format(pkmn_name_stripped))
        embed.set_thumbnail(url="http://marktan.us/pokemon/img/icons/{}.png".format(pkmn_id))
        return await pokemaster_bot.say(embed=embed)
    else:
        return await pokemaster_bot.say("Oak: You can't see what you don't have.")


async def get_trainer_info(author):
    total_caught = database.get_total_caught(author)
    total_caught = "{}/718".format(total_caught)
    pokedollars = "₱{}".format(database.get_pokedollars(author))

    embed = Embed(color=0xB80800)
    embed.set_author(name="{}'s Trainer Profile".format(author),
        icon_url="https://vignette3.wikia.nocookie.net/pkmnshuffle/images/b/b1/Pikachu_%28Winking%29.png/revision/latest?cb=20170410234514")
    embed.add_field(name='Pokedex Entries', value=total_caught)
    embed.add_field(name='Money', value=pokedollars)
    embed.set_thumbnail(url="http://rs1240.pbsrc.com/albums/gg495/iKyle10/Pokemon%20Trainer/avatar514181_1_zpsfxp46su9.gif~c200")
    embed.set_image(url="https://archives.bulbagarden.net/media/upload/a/a0/Spr_B2W2_Hilbert.png")
    return await pokemaster_bot.say(embed=embed)


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