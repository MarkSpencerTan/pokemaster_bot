from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import tempfile
import os

party = Image.open("partyarea2.png")

x1 = 2
y1 = 35
x2 = 42
y2 = 65

# for text drawing
font = ImageFont.truetype("arial.ttf", 11)
draw = ImageDraw.Draw(party)

# trainer info
trainer = "Marko Spencer"
draw.text((x1 + 10 , y1 - 25), trainer + "'s Party", (255, 255, 255), font=font)

party_list = ["abomasnow", "charizard", "unown-x", "pikachu", "piplup", "charmander"]
for pokemon in party_list:
    shiny = True
    id = "000"
    health = 100
    health_remaining = 50
    health_ratio = health_remaining / health
    name = pokemon.upper()
    
    area = (x1, y1, x2, y2)
    
    # paste the pokemon image
    if shiny:  
        image = Image.open("shiny/{}.png".format(pokemon))
    else:
        image = Image.open("regular/{}.png".format(pokemon))
    party.paste(image, area, image)
    
    name = "[{}] {}".format(id, name)
    # draw pokemon info
    if shiny:
        draw.text((x1 + 45, y1 + 5), name, (255,165,0), font=font)
        draw.text((x1 + 45, y1 + 5), name, (255,165,0), font=font)
    else:
        draw.text((x1 + 45, y1 + 5), name, (0, 0, 0), font=font)
        
    draw.rectangle([x1+ 45, y1+ 20, x1 + 145, y1+ 30], fill=(0,0,0))
    draw.rectangle([x1+ 45, y1+ 20, x1 + 45 + ((health_ratio)* 100), y1+ 30], fill=(34,139,34))
    health_txt = "{}/{}".format(health_remaining, health)
    draw.text((x1 + 80, y1 + 20), health_txt, (255, 255, 255), font=font)
    y1 += 37
    y2 += 37

# create a temp file for the upload
file, filename = tempfile.mkstemp(".png")
# save the compiled image
party.save(filename)

# upload with bot
party.show()
os.close(file)


