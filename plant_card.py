from PIL import Image, ImageChops, ImageDraw, ImageFont
from functools import lru_cache

import datetime
import json

class PlantCard:
  def __init__(self, data):
    self.droplet, self.leaf = PlantCard.__get_base_icons()
    self.data = data

  @staticmethod
  @lru_cache(maxsize=None)
  def __get_config():
    config = None

    with open('config', 'r') as __config:
      config = json.loads(__config.read())

    return config

  @staticmethod
  @lru_cache(maxsize=None)
  def __get_base_font(size=30):
    return ImageFont.truetype('fonts/SourceSansPro-Bold.ttf', size)

  @staticmethod
  @lru_cache(maxsize=None)
  def __get_base_icons():
    droplet = Image.open("images/droplet.png")
    droplet.thumbnail((100, 20), Image.ANTIALIAS)

    leaf = Image.open("images/leaf.png")
    leaf.thumbnail((100, 20), Image.ANTIALIAS)

    return (droplet, leaf)

  @staticmethod
  def __trim(image):
    background = Image.new(image.mode, image.size, image.getpixel((0,0)))
    difference = ImageChops.difference(image, background)
    difference = ImageChops.add(difference, difference, 2.0, -100)
    bbox = difference.getbbox()
    
    if bbox:
      return image.crop(bbox)

  def generate_fertilizer_cycle(self):
    config = PlantCard.__get_config()
    epoch = config.get("epoch")

    month, day, year = [int(x) for x in epoch.split("/")]
    epoch = datetime.date(year, month, day)
    todays_date = datetime.date.today()

    delta = (todays_date - epoch).days
    cycle = int(self.data.get("fertilizer_cycle"))
    days_until_fertilize = cycle - (delta % cycle)

    canvas = Image.new('1', (350, 20))
    canvas.paste(self.leaf, (0, 0))

    draw_context = ImageDraw.Draw(canvas)
    draw_context.text((25, -10), str(days_until_fertilize), font=PlantCard.__get_base_font(), fill=255)

    return PlantCard.__trim(canvas)

  def generate_water_cycle(self):
    config = PlantCard.__get_config()
    epoch = config.get("epoch")

    month, day, year = [int(x) for x in epoch.split("/")]
    epoch = datetime.date(year, month, day)
    todays_date = datetime.date.today()

    delta = (todays_date - epoch).days
    cycle = int(self.data.get("water_cycle"))
    days_until_water = cycle - (delta % cycle)

    canvas = Image.new('1', (350, 20))
    canvas.paste(self.droplet, (0, 0))

    draw_context = ImageDraw.Draw(canvas)
    draw_context.text((25, -10), str(days_until_water), font=PlantCard.__get_base_font(), fill=255)

    return PlantCard.__trim(canvas)


  # Cache for 30 minutes in the future
  def generate_image(self, font):
    base_card = Image.new('1', (170, 250))
    
    # Generate days until next watering, days until next fertilizing
    water_date = self.generate_water_cycle()
    fertilize_date = self.generate_fertilizer_cycle()

    # Calculate fertilizing timer position based on width
    fertilize_x_pos = (base_card.size[0] - fertilize_date.size[0]) - 10

    # Place watering timer, fertilizer timer
    base_card.paste(water_date, (10, 220))
    base_card.paste(fertilize_date, (fertilize_x_pos, 220))

    # Center and draw ID
    draw_context = ImageDraw.Draw(base_card)
    
    id_text_width, id_text_height = draw_context.textsize(self.data.get("ID"), font)
    id_x_pos = (base_card.size[0] / 2) - (id_text_width / 2)

    draw_context.text((id_x_pos, 25), self.data.get("ID"), font=font, fill=255)

    # Center and draw name
    name_text_width, name_text_height = draw_context.textsize(self.data.get("name"), PlantCard.__get_base_font(15))
    name_x_pos = (base_card.size[0] / 2) - (name_text_width / 2)
    name_y_pos = id_text_height + 10 + 25
    draw_context.text((name_x_pos, name_y_pos), self.data.get("name"), font=PlantCard.__get_base_font(15), fill=255)

    return base_card


  def __repr__(self):
    return "<PlantCard {}.{}>".format(
      self.data.get("ID"),
      self.data.get("name")
    )