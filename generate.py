from PIL import Image, ImageChops, ImageFont
from plant_card import PlantCard

import struct
import json

panel_header_data = [
  0x3D,    # panel_type
  0x0400,  # x_res
  0x0500,  # y_res
  0x01,    # color_depth
  0x00     # pixel_data_format_type
]

panel_header_data_reserved_filler = 0x00 # RFU - 9 bits

def bytes_slice(e):
  summation = []

  for i, e in enumerate(e):
    if (i + 1) % 8 == 0:
      yield summation

      summation = []

    summation.append(e)

with open("test_file.epd", "bw") as epdfile:
  plants = None
  plants_objects = []

  with open('plants.json', 'r') as __plants:
    plants = json.loads(__plants.read()).get("plants")

  header = struct.pack(
    'b h h b b b b b b b b b b b', *panel_header_data, *[panel_header_data_reserved_filler for i in range(9)]
  )

  image_content = b''
  
  #all_white = struct.pack('b', 0)
  #all_black = struct.pack('b', 1)
  #for section in bytes_slice(img.tobytes()):
  #  if section == [255, 255, 255, 255, 255, 255, 255, 255]:
  #    image_content += all_white
  #  elif section == [0, 0, 0, 0, 0, 0, 0, 0]:
  #    image_content += all_black
  #  else:
  #    joined = "".join(['0' if x < 255 else '1' for x in section])
  #    average = int(joined, 2) - 128
  #    image_content += struct.pack('b', average)

  # 2 pixel buffer on left and right sides

  image = Image.new('1', (1024, 1280), 1)
  font = ImageFont.truetype('fonts/Black_Rose.ttf', 100)
  
  plant_cards = [PlantCard(plant).generate_image(font) for plant in plants]

  row = 1
  for i, card in enumerate(plant_cards):

    if (i % 6 == 0) and (i != 0):
      row += 1

    if (i % 6 == 0):
      x_pos = 2
    else:
      x_pos = (170 * (i % 6))
    
    y_pos = (250 * row) - 250

    if row % 2 == 0:
      if i % 2 == 0:
        card = ImageChops.invert(card)
    else:
      if i % 2 != 0:
        card = ImageChops.invert(card)

    image.paste(card, (x_pos, y_pos))

  image.save('test_out.png')
  image = ImageChops.invert(image)

  payload = header + image.tobytes()
  epdfile.write(payload)