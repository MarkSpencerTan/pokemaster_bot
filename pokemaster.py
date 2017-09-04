from discord.ext.commands import Bot
from discord import Client
from discord.ext.commands.cooldowns import BucketType
from discord.embeds import Embed
import discord.ext.commands as commands
import threading

import database
import settings
import emojis	


pokemaster_bot = Bot(command_prefix="!")

@pokemaster_bot.event
async def on_read():
	print("Hello New Pokemon Trainer!")


@commands.cooldown(1, 1, type=BucketType.user)
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


@commands.cooldown(1, 2, type=BucketType.user)
@pokemaster_bot.command(pass_context=True)
async def storage(ctx, *args):
	return await show_storage(ctx.message)


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
	type_str = ""
	types = pkmn['types']
	for type in types:
		type_str += "{}{} ".format(emojis.get_emoji(type['name']), type['name'])

	description = "**{}** You have caught *{}*".format(message.author, pkmn_name)
	embed = Embed(color=0xff0000, description=description)
	# embed.set_author(name="Trainer {}".format(message.author))
	embed.set_image(url="http://pokeapi.co/media/img/{}.png".format(pkmn_id))
	embed.add_field(name='Name', value="{}[{}]".format(pkmn_name, pkmn_id))
	embed.add_field(name="Types", value=type_str)
	embed.add_field(name='Hp', value=pkmn["hp"])
	embed.add_field(name='Attack', value=pkmn["attack"])
	embed.add_field(name='Defense', value=pkmn["defense"])
	embed.add_field(name='Speed', value=pkmn["speed"])
	embed.set_thumbnail(url="http://marktan.us/pokemon/img/icons/{}.png".format(pkmn_id))
	# add the pokemon to the user db
	database.add_pokemon(message.author, pkmn)
	await pokemaster_bot.say(embed=embed)


async def show_storage(message, sorted=False, box=0):
	embed = Embed(color=0x000000, description="**{}**'s Pkmn at Professor Oak's Slavehouse".format(message.author))
	# embed.set_author(name="Trainer {}".format(message.author))
	if sorted:
		pkmn_ids = sorted(database.get_storage(message.author))
	else:
		pkmn_ids = database.get_storage(message.author)
	
	boxes = []
	storage_list = ""
	count = 0
	for pkmn in pkmn_ids:
		count += 1
		storage_list += pkmn + "\t"
		if count == 30:
			boxes.append(storage_list)
			storage_list = ""
			count = 0
	boxes.append(storage_list)
	storage_list = boxes[box]
	embed.add_field(name="Storage", value=storage_list, inline=True)
	await pokemaster_bot.say(embed=embed)

pokemaster_bot.run(settings.BOT_TOKEN)
