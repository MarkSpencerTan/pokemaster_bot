EMOJIS = {
	"water": ":ocean:",
	"fire": ":fire:",
	"grass": ":leaves:",
	"rock": ":full_moon:",
	"electric": ":zap: ",
	"ghost":":ghost:",
	"ground":":poop:",
	"fairy":":sparkles:",
	"bug":":bug:",
	"poison": ":skull_crossbones:",
	"wind": ":cloud_tornado:",
	"fighting": ":boxing_glove:",
	"normal": ":mouse:",
	"ice": ":snowflake:",
	"dark": ":spy:",
	"steel": ":robot:",
	"psychic": ":alien:",
	"flying":":dove:",
	"dragon":":dragon_face:"
}

def get_emoji(type):
	if type in EMOJIS.keys():
		return EMOJIS[type]
	return ""