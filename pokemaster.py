from discord.ext.commands import Bot

import settings

pokemaster_bot = Bot(command_prefix="!")

@pokemaster_bot.event
async def on_read():
	print("Hello New Pokemon Trainer!")


@pokemaster_bot.command()
async def poke(*args):
	command = args[0]
	if command == 'hello':
		return await hello(args[1:])
	elif command == 'members':
		return await get_members()
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

pokemaster_bot.run(settings.BOT_TOKEN)
