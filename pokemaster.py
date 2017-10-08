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
from discord import Game
from pprint import pprint
import traceback
import random
import sys
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import tempfile
import os
import math
sys.path.append(".")

import database
import settings
import emojis
import tiers
import effectiveness

pokemaster_bot = Bot(command_prefix=settings.BOT_PREFIX)
battles = {}

@pokemaster_bot.event
async def on_command_error(ctx, error):
    try:
        user = str(error.message.author).split("#")[0]
        message = "Oak: **{}** keep your pokeballs calm, and wait {} seconds."
        await pokemaster_bot.send_message(error.message.channel, message.format(user, int(ctx.retry_after)))
    except:
        tb = "\n".join(traceback.format_tb(error.original.__traceback__))
        print("{}: {}\n{}".format(error.original.__class__.__name__, str(error), str(tb)))


@commands.cooldown(1, 1, type=BucketType.user)
@pokemaster_bot.group(pass_context=True)
async def admin(ctx):
    """
    Commands for the bot admin
    """
    if ctx.invoked_subcommand is None:
        await pokemaster_bot.say("Invalid Command")


@admin.command(pass_context=True)
async def deposit(ctx, money:int):
    """
    Puts money in account
    """
    author = ctx.message.author
    if str(author) in settings.BOT_ADMIN:
        database.add_pokedollars(author, money)
        await pokemaster_bot.say("funds deposited")
    else:
        await pokemaster_bot.say("You are not the bot admin. Go awai.")
    

@commands.cooldown(1, 20, type=BucketType.user)
@pokemaster_bot.group(pass_context=True)
async def poke(ctx):
    """
    Commands related to interacting with wild pokemon.
    """
    await pokemaster_bot.change_presence(game=Game(name='!help for command info'))
    if ctx.invoked_subcommand is None:
        await pokemaster_bot.say("Invalid Command")


@poke.command(pass_context=True)
async def catch(ctx):
    """
    - Catches a wild pokemon.

    Pokemon Rarity
    Black = Common
    Red = Uncommon
    Blue = Rare
    Gold = Ultra
    Purple = Legendary
    """
    return await catch(ctx.message)


@poke.command(pass_context=True)
async def battle(ctx):
    """
    - Battles a wild pokemon and earns you money based on it's rarity.
    """
    return await battle(ctx.message)


@commands.cooldown(1, 4, type=BucketType.user)
@pokemaster_bot.command(pass_context=True)
async def battle(ctx, enemy, bet: int):
    """
    Battle another opponent with your party pokemon.

    You challenge another trainer with the @username shortcut.
    The initiator's bet will be the one that is used for the battle.

    To accept someone's battle request, send a battle request back to them.
    """
    author = ctx.message.author
    enemy = str(ctx.message.mentions[0])
    for member in get_members():
        if str(enemy) in str(member):
            enemy = member
    return await battle_trainer(str(author), enemy, bet)


@commands.cooldown(1, 4, type=BucketType.user)
@pokemaster_bot.command(pass_context=True)
async def storage(ctx, *args):
    """
    Shows your pokemon storage box.

    Switch boxes with
    !storage <box#>

    Sort by rarity
    !storage <rarity>
        - rarities: 'common', 'rare', 'uncommon', 'ultra', 'legendary'

    Sort by alphabetical order in the box
    !storage sorted

    View your eevee collection
    !storage eevee
    """
    author = ctx.message.author
    box = 1
    rarity = None
    sorted = False
    for arg in args:
        if arg in ('common', 'rare', 'uncommon', 'ultra', 'legendary', 'eevee'):
            rarity = arg
        elif arg == 'sorted':
            sorted = True
        elif arg.isdigit():
            box = int(arg)
    if rarity == 'eevee':
        return await show_storage(author, box=box, is_sorted=sorted, category="eevee")
    if rarity is not None:
        return await show_storage(author, category=rarity, box=box, is_sorted=sorted)
    return await show_storage(author, box=box, is_sorted=sorted)


@commands.cooldown(1, 2, type=BucketType.user)
@pokemaster_bot.group(pass_context=True)
async def party(ctx):
    """
    Shows the pokemon in your party
    """
    if ctx.invoked_subcommand is None:
        return await show_party(ctx.message.author)


@commands.cooldown(1, 2, type=BucketType.user)
@party.command(pass_context=True)
async def add(ctx, pkmn_id: int):
    """
    Adds a pokemon from your storage to the party
    """
    res = database.add_to_party(ctx.message.author, pkmn_id)
    if not res:
        pokemaster_bot.say("**Oak**: Make sure you actually have that pokemon or if your party is not full ya scrub.")
    return await show_party(ctx.message.author)


@commands.cooldown(1, 2, type=BucketType.user)
@party.command(pass_context=True)
async def remove(ctx, pkmn_id: int):
    """
    Removes a pokemon from your party
    """
    res = database.remove_from_party(ctx.message.author, pkmn_id)
    if not res:
        pokemaster_bot.say("**Oak**: Make sure you actually have that pokemon or if your party is not full ya scrub.")
    return await show_party(ctx.message.author)

@commands.cooldown(1, 2, type=BucketType.user)
@party.command(pass_context=True)
async def removeall(ctx, pkmn_id: int):
    """
    Removes all your pokemon from the party
    """
    res = database.remove_all_party(ctx.message.author)
    if not res:
        pokemaster_bot.say("**Oak**: Make sure you actually have that pokemon or if your party is not full ya scrub.")
    return await show_party(ctx.message.author)

@commands.cooldown(1, 2, type=BucketType.user)
@party.command(pass_context=True)
async def release(ctx, pkmn_id: int):
    """
    Release a pokemon from your party for money.
    Pokemon trafficking is a thing.
    """
    res = database.release_from_party(ctx.message.author, pkmn_id)
    if res:
        tier = _get_tier(int(pkmn_id))
        money = int(_get_money_earned(tier)/3)
        message = "Oak: Don't worry I'll take care of {} ;) \nHere's ₱{}, buy yourself something nice."\
            .format(database.get_pokemon_name(pkmn_id), money)
        database.add_pokedollars(ctx.message.author, money)
    else:
        message = "**Oak**: Make sure you actually have that pokemon or if your party is not full ya scrub."
    await pokemaster_bot.say(message)


@commands.cooldown(1, 5, type=BucketType.user)
@pokemaster_bot.command(pass_context=True)
async def pokedex(ctx, pokemon_id: int):
    """
    Shows a pokemon in more detail.
    You are only able to view pokemon you've already caught
    """
    return await get_pokedex(ctx.message.author, pokemon_id)


@commands.cooldown(1, 5, type=BucketType.user)
@pokemaster_bot.command(pass_context=True)
async def trainer(ctx, trainer=None):
    """
    View information about a trainer in the server
    """
    # gets the total number of unique pokemon caught
    if trainer:
        trainer = str(ctx.message.mentions[0])
    else:
        trainer = ctx.message.author
    return await get_trainer_info(trainer)


@commands.cooldown(1, 60, type=BucketType.user)
@pokemaster_bot.command(pass_context=True)
async def pokecenter(ctx, *args):
    """
    Heals your whole party pokemon for ₱150
    """
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
    """
    Shows your current balance.
    """
    author = ctx.message.author
    balance = database.get_pokedollars(author)
    return await pokemaster_bot.say(":dollar: | **{} you have ₱{}**".format(author, balance))


def get_members():
    members = pokemaster_bot.get_all_members()
    member_list = []
    for member in members:
        member_list.append(str(member))
    return member_list


def get_member(name):
    members = pokemaster_bot.get_all_members()
    for member in members:
        if name in str(member):
            return member


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


async def battle_trainer(author, enemy, bet=None):
    # check if have enough money for bet
    if bet:
        if database.get_pokedollars(author) < bet:
            return await pokemaster_bot.say("Oak: You're too broke to bet that amount.")
    # check battles if enemy already challenged you
    if author in battles.keys() and enemy in battles[author].keys():
        pass
    elif enemy not in battles.keys():
        battles[enemy] = {author: bet}
        print(battles)
        return await pokemaster_bot.say("waiting for %s's response" % enemy)
    elif author not in battles[enemy].keys():
        battles[enemy][author] = bet
        print(battles)
        return await pokemaster_bot.say("waiting for %s's response" % enemy)
    # remove from your pending battles and start battle
    bet = battles[author][enemy]
    battles[author].pop(enemy)

    party1 = database.get_party(author)
    party2 = database.get_party(enemy)
    fainted1 = []
    fainted2 = []

    pkmn1 = party1.pop()
    pkmn2 = party2.pop()
    while len(fainted1) < 6 and len(fainted2) < 6:
        try:
            # check if pokemon is not already fainted
            while pkmn1["health"] <= 0:
                fainted1.append(pkmn1)
                pkmn1 = party1.pop()
            while pkmn2["health"] <= 0:
                fainted2.append(pkmn2)
                pkmn2 = party2.pop()

            result = _fight_trainer(author, enemy, pkmn1, pkmn2)
            if result:
                fainted2.append(pkmn2)
                pkmn2 = party2.pop()
            else:
                fainted1.append(pkmn1)
                pkmn1 = party1.pop()
        except IndexError:
            break

    if len(fainted1) > len(fainted2):
        winner = enemy
        loser = author
    elif len(fainted2) > len(fainted1):
        winner = author
        loser = enemy
    else:
        winner = None

    color = 0xff0000
    embed = Embed(color=color, description="**{}** VS **{}**".format(author, enemy))
    embed.set_thumbnail(url="https://i0.wp.com/alphadigits.com/wp-content/uploads/2014/01/pokebuilder-icon.png?fit=300%2C300")
    embed.set_image(url="https://archives.bulbagarden.net/media/upload/a/a0/Spr_B2W2_Hilbert.png")

    if winner is None:
        embed.add_field(name="Oak", value="The battle was a tie. How disappointing...")
    else:
        # do winning embed here
        embed.add_field(name="Winner:".format(winner), value=winner, inline=False)
        embed.add_field(name="Pokedollars Earned", value="₱{}".format(bet))
        # add prize money
        database.add_pokedollars(winner, bet)
        database.add_pokedollars(loser, bet * -1)
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


def _fight_trainer(trainer1, trainer2, pkmn1, pkmn2) -> bool:
    """
    Your pkmn vs enemy trainer pkmn. saves the state of the user's pkmn to the
    user's database at the end of the fight
    :return: True if pkmn wins
    """
    win = False
    while True:
        if pkmn1["speed"] > pkmn2["speed"]:
            # you go first
            pkmn2["health"] = _attack(pkmn1, pkmn2)
            if pkmn2["health"] <= 0:
                win = True
                break
            pkmn1["health"] = _attack(pkmn2, pkmn1)
            if pkmn1["health"] <= 0:
                break
        else:
            # enemy goes first
            pkmn1["health"] = _attack(pkmn2, pkmn1)
            if pkmn1["health"] <= 0:
                break
            pkmn2["health"] = _attack(pkmn1, pkmn2)
            if pkmn2["health"] <= 0:
                win = True
                break
    # round the health to nearest int
    pkmn1["health"] = int(pkmn1["health"])
    pkmn2["health"] = int(pkmn2["health"])
    database.save_party_pkmn_state(trainer1, pkmn1)
    database.save_party_pkmn_state(trainer2, pkmn2)

    return win


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


async def show_storage(author, is_sorted=False, box=1, category=None):
    categories = {
        "common": [10, 11, 13, 14, 16, 17, 19, 20, 21, 22, 23, 24, 27, 28, 29, 30, 32, 33, 39, 41, 42, 43, 44, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 60, 66, 67, 69, 70, 72, 73, 74, 75, 79, 80, 81, 82, 84, 85, 86, 87, 88, 90, 91, 92, 95, 96, 97, 98, 99, 100, 101, 102, 104, 109, 111, 114, 116, 118, 119, 120, 121, 129, 161, 162, 163, 164, 165, 167, 168, 170, 177, 179, 180, 183, 187, 188, 189, 191, 194, 195, 203, 206, 209, 216, 218, 220, 234, 261, 263, 264, 265, 266, 268, 270, 273, 274, 276, 278, 280, 283, 285, 287, 290, 293, 296, 300, 302, 303, 304, 307, 309, 311, 312, 313, 314, 315, 316, 318, 319, 320, 322, 324, 325, 327, 331, 339, 341, 353, 355, 366, 396, 399, 401, 403, 406, 412, 415, 417, 418, 420, 422, 425, 427, 431, 433, 434, 436, 449, 453, 456, 459, 504, 505, 506, 507, 509, 510, 519, 522, 524, 527, 529, 531, 532, 533, 535, 540, 541, 543, 546, 547, 548, 549, 550, 551, 557, 559, 560, 562, 568, 572, 573, 574, 575, 577, 578, 580, 581, 582, 583, 585, 587, 588, 590, 591, 592, 595, 596, 597, 598, 599, 600, 602, 605, 607, 618, 619, 629, 630, 659, 660, 661, 662, 664, 665, 667, 669, 670, 672,  674, 676, 677, 678, 679, 682, 684, 686, 687, 688, 690, 692, 694, 703],
        "uncommon": [12, 15, 18, 25, 35, 37, 40, 45, 58, 61, 63, 68, 76, 77, 89, 93, 103, 105, 106, 107, 108, 110, 112, 117, 166, 171, 178, 182, 184, 185, 186, 190, 192, 193, 198, 200, 202, 204, 207, 210, 211, 215, 217, 219, 221, 222, 223, 224, 227, 228, 231, 235, 236, 237, 238, 239, 240, 241, 262, 267, 269, 271, 275, 277, 279, 281, 284, 286, 288, 291, 294, 297, 298, 299, 301, 305, 308, 310, 317, 321, 323, 326, 328, 332, 335, 336, 337, 338, 340, 342, 343, 352, 354, 356, 357, 361, 363, 367, 368, 369, 370, 397, 400, 402, 404, 407, 408, 410, 413, 414, 416, 419, 421, 423, 426, 428, 432, 435, 437, 441, 446, 447, 450, 451, 454, 455, 457, 460, 508, 511, 512, 513, 514, 515, 516, 517, 520, 521, 523, 525, 528, 530, 534, 536, 538, 539, 542, 544, 552, 554, 556, 558, 561, 563, 564, 566, 569, 576, 579, 584, 586, 589, 593, 594, 601, 603, 606, 608, 609, 613, 616, 617, 620, 627, 628, 632, 636, 637, 663, 666, 668, 671, 673, 675, 680, 683, 685, 689, 691, 693, 695, 701, 702, 707, 708, 710],
        "rare": [1, 4, 7, 26, 31, 36, 38, 62, 64, 65, 71, 78, 94, 113, 122, 123, 124, 125, 126, 127, 128, 133, 134, 135, 136, 137, 138, 139, 140, 141, 152, 155, 158, 169, 172, 173, 174, 175, 181, 199, 201, 205, 208, 214, 225, 226, 229, 232, 233, 246, 247, 252, 253, 255, 256, 258, 259, 272, 282, 289, 292, 295, 306, 329, 333, 344, 345, 346, 347, 348, 349, 351, 358, 359, 360, 362, 364, 365, 371, 372, 374, 375, 387, 388, 390, 391, 393, 394, 398, 405, 409, 411, 424, 429, 430, 438, 439, 440, 443, 444, 448, 452, 458, 461, 470, 471, 476, 478, 495, 496, 498, 499, 501, 502, 518, 526, 537, 545, 553, 555, 565, 567, 570, 604, 610, 611, 614, 615, 622, 623, 624, 625, 626, 631, 633, 634, 650, 651, 653, 654, 656, 657, 681, 696, 698, 700, 704, 705, 709, 711, 712, 714],
        "ultra": [2, 3, 5, 6, 8, 9, 34, 59, 83, 115, 130, 131, 132, 142, 143, 147, 148, 149, 153, 154, 156, 157, 159, 160, 176, 196, 197, 212, 230, 242, 248, 254, 257, 260, 330, 334, 350, 373, 376, 389, 392, 395, 442, 445, 462, 463, 464, 465, 466, 467, 468, 469, 472, 473, 474, 475, 477, 479, 497, 500, 503, 571, 612, 621, 635, 652, 655, 658, 697, 699, 706, 713, 715, 720],
        "legendary": [144, 145, 146, 150, 151, 213, 243, 244, 245, 249, 250, 251, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386,480, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490, 491, 492, 493, 494, 638, 639, 640, 641, 642, 643, 644, 645, 646, 647, 648, 649, 716, 717, 718, 719, 721],
        "eevee": [133, 134, 135, 136, 470, 197, 471, 700, 196, 471]
    }

    storage_list = database.get_storage(author)
    if is_sorted:
        storage_list = sorted(storage_list, key=lambda p: p['name']) 

    if category is None:
        storage = Image.open("img/storage/common.png")
    else:
        storage = Image.open("img/storage/{}.png".format(category))

    x1 = 0
    y1 = 34
    x2 = 40
    y2 = 64

    # for text drawing
    font = ImageFont.truetype("fonts/8bit.ttf", 10)
    draw = ImageDraw.Draw(storage)

    current_box = 1
    pokemon_count = 0
    for i, pkmn in enumerate(storage_list):
        id = pkmn["national_id"]
        if (category is None) or ( id in categories[category]):
            pokemon_count += 1
        elif id not in categories[category]:
            continue
        if current_box == box:
            shiny = pkmn["shiny"]
            
            area = (x1, y1, x2, y2)
            name = pkmn["name"].lower()

            # paste the pokemon image
            if shiny:
                image = Image.open("img/pokemon/shiny/{}.png".format(id))
            else:
                image = Image.open("img/pokemon/regular/{}.png".format(id))

            if pkmn["health"] == 0:
                image = image.convert('L')

            storage.paste(image, area, image)
            
            id = "[{}]".format(pkmn["national_id"])
            # draw pokemon info
            draw.text((x1 + 11, y1 + 31), id, (0, 0, 0), font=font)
            draw.text((x1 + 10, y1 + 30), id, (255, 255, 255), font=font)
        
            if pokemon_count % 6 == 0:
                # new row
                y1 += 34
                y2 += 34
                x1 = 0
                x2 = 40
            else:
                x1 += 32
                x2 += 32
        if pokemon_count % 30 == 0:
                current_box += 1

    total_pages = math.ceil(pokemon_count / 30)
    x1 = 0
    y1 = 34
    x2 = 40
    y2 = 64
    draw.text((x1 + 31 , y1 - 9), str(author) + " - {}/{}".format(box, total_pages), (0, 0, 0), font=font)
    draw.text((x1 + 30 , y1 - 10), str(author) + " - {}/{}".format(box, total_pages), (255, 255, 255), font=font)

    # create a temp file for the upload
    file, filename = tempfile.mkstemp(".png")
    # save the compiled image
    storage.save(filename)
    # upload with bot
    await pokemaster_bot.upload(filename)
    os.close(file)


async def show_party(author):    
    party_list = database.get_party(author)

    party = Image.open("img/partyarea2.png")

    x1 = 2
    y1 = 35
    x2 = 42
    y2 = 65

    # for text drawing
    font = ImageFont.truetype("fonts/8bit.ttf", 12)
    draw = ImageDraw.Draw(party)

    draw.text((x1 + 10 , y1 - 25), str(author) + "'s Party", (255, 255, 255), font=font)

    for pkmn in party_list:
        shiny = pkmn["shiny"]
        health_ratio = float(float(pkmn["health"]) / float(pkmn["hp"]))
        pkmn_id = pkmn["national_id"]
        area = (x1, y1, x2, y2)
        name = pkmn["name"].upper()

        # paste the pokemon image
        if shiny:  
            image = Image.open("img/pokemon/shiny/{}.png".format(pkmn_id))
        else:
            image = Image.open("img/pokemon/regular/{}.png".format(pkmn_id))
        if health_ratio == 0:
            image = image.convert('L')

        party.paste(image, area, image)
        
        name = "[{}] {}".format(pkmn["national_id"], name)
        # draw pokemon info
        if shiny:
            draw.text((x1 + 45, y1 + 5), name, (255,165,0), font=font)
            draw.text((x1 + 45, y1 + 5), name, (255,165,0), font=font)
        else:
            draw.text((x1 + 45, y1 + 5), name, (0, 0, 0), font=font)
        # draw health bars
        draw.rectangle([x1+ 45, y1+ 20, x1 + 145, y1+ 30], fill=(0,0,0))
        fill = (34,139,34)
        if  .25 <= health_ratio < .50:
            fill = (255,140,0)
        elif health_ratio < .25:
            fill = (255, 0, 0) 
        draw.rectangle([x1+ 45, y1+ 20, x1 + 45 + (health_ratio * 100), y1 + 30], fill=fill)
        health_txt = "{}/{}".format(pkmn["health"], pkmn["hp"])
        draw.text((x1 + 80, y1 + 20), health_txt, (255, 255, 255), font=font)
        y1 += 37
        y2 += 37

    # create a temp file for the upload
    file, filename = tempfile.mkstemp(".png")
    # save the compiled image
    party.save(filename)
    print(filename)
    # upload with bot
    await pokemaster_bot.upload(filename)
    os.close(file)


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
pokemaster_bot.run(settings.BOT_TOKEN)
# while True:
#     try:
#         pokemaster_bot.run(settings.BOT_TOKEN)
#     except KeyboardInterrupt:
#         print('Closing Bot')
#         exit(-1)
#     except:
#         pass
