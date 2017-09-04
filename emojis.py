EMOJIS = {
	"water": ":ocean:",
	"fire": ":fire:",
	"grass": ":leaves:",
	"rock": ":full_moon:",
	"electric": ":thunder_cloud_rain:",
	"ghost":":ghost:",
	"ground":":poop:",
	"fairy":":sparkles:",
	"bug":":bug:",
	"poison": ":imp:",
	"wind": ":wind_blowing_face:",
	"fighting": ":punch:",
	"normal": ":mouse:",
	"ice": ":snowflake:"
}

def get_emoji(type):
	if type in EMOJIS.keys():
		return EMOJIS[type]
	return ""