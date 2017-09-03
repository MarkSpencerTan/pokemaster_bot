from discord.ext.commands import Bot
from discord import Client

import database
import settings


pokemaster_bot = Bot(command_prefix="!")

@pokemaster_bot.event
async def on_read():
	print("Hello New Pokemon Trainer!")


@pokemaster_bot.command(pass_context=True)
async def poke(ctx, *args):
	message = ctx.message
	command = args[0]
	if command == 'hello':
		return await hello(args[1:])
	elif command == 'members':
		return await get_members()
	elif command == 'catch':
		return await get_random(message)
	return await pokemaster_bot.say("Hello trainer")


async def hello(args):
	response = ""
	for text in args:
		response += text + " "
	return await pokemaster_bot.say(response)


async def get_members():
	members = pokemaster_bot.get_all_members()
	response = ""
	for member in members:
		response += str(member) + "\n"
	return await pokemaster_bot.say(response)


async def get_random(message):
	pkmn = database.get_random_pokemon()
	await pokemaster_bot.say("{} you caught {}!".format(message.author, pkmn['name']))
	await pokemaster_bot.say("http://pokeapi.co/media/img/{}.png".format(pkmn['national_id']))

pokemaster_bot.run(settings.BOT_TOKEN)
