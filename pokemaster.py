from discord.ext.commands import Bot
from discord import Client
from discord.ext.commands.cooldowns import BucketType
from discord.embeds import Embed
from random import randint
import discord.ext.commands as commands
import threading

import database
import settings
import emojis
import tiers	


pokemaster_bot = Bot(command_prefix="!")

@pokemaster_bot.event
async def on_read():
	print("Hello New Pokemon Trainer!")


@commands.cooldown(1, 15, type=BucketType.user)
@pokemaster_bot.command(pass_context=True)
async def poke(ctx, *args):
	message = ctx.message
	command = args[0]
	if command == 'hello':
		return await hello(args[1:])
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
		if arg in ('common', 'rare', 'uncommon', 'ultra', 'legendary'):
			rarity = arg
		elif arg == 'sorted':
			sorted = True
		elif int(arg) in list(range(9999)):
			box = int(arg)
		

	if rarity is not None:
		return await show_storage_by_rarity(message, rarity, box=box, is_sorted=sorted)
	return await show_storage(message, box=box, is_sorted=sorted)


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

	# appends an emoji that matches the type
	type_str = ""
	types = pkmn['types']
	for type in types:
		type_str += "{} {} ".format(emojis.get_emoji(type['name']), type['name'])

	# color the border by rarity tier
	if pkmn_id in tiers.TIERS["0"]:
		color = 0x000000
	elif pkmn_id in tiers.TIERS["1"]:
		color = 0xB80800
	elif pkmn_id in tiers.TIERS["2"]:
		color = 0x0009C4
	elif pkmn_id in tiers.TIERS["3"]:
		color = 0xF7AB09
	else:
		color = 0x9909F7

	# random generator if shiny
	shiny_chance = randint(1,100)
	if shiny_chance > 50:
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
	embed.add_field(name='Hp', value=pkmn["hp"])
	embed.add_field(name='Attack', value=pkmn["attack"])
	embed.add_field(name='Defense', value=pkmn["defense"])
	embed.add_field(name='Speed', value=pkmn["speed"])
	embed.set_thumbnail(url="http://marktan.us/pokemon/img/icons/{}.png".format(pkmn_id))

	# add the pokemon to the user db
	database.add_pokemon(message.author, pkmn, shiny=shiny)
	await pokemaster_bot.say(embed=embed)


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
		return await pokemaster_bot.say("Oak: There's nothing in that box because you haven't caught enough pokemon m8. Git gud.")

	if is_sorted:
		storage_list = storage_list.split("\t")
		storage_list = sorted(storage_list)
		storage_list = "\t".join(storage_list)

	embed.add_field(name="Storage [**{}**/{}]".format(box, len(boxes)), value=storage_list, inline=True)
	return await pokemaster_bot.say(embed=embed)

# run the bot
pokemaster_bot.run(settings.BOT_TOKEN)
