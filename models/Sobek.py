from PIL import Image, ImageChops, ImageDraw, ImageFont
from .WeatherState import WeatherState
from .PlantCard import PlantCard
from threading import Timer

import utils
import time
import json

class Sobek():
  """Sobek app container. Maintains application state
  and regulates rendered image.
  """
  def __init__(self, events):
    self.events = events
    self.config = utils.load_config()
    self.plants = self.load_plants()
    self.weather = self.load_weather()

    self.font_plants = ImageFont.truetype('fonts/Black_Rose.ttf', 100)
    self.font_time = ImageFont.truetype('fonts/OpenSans-Bold.ttf', 30)

  def __cycle_primary(self):
    self.events.put("{} - Rendered weather and plants.".format(time.strftime("%X")))
    
    self.image = Image.new("1", (1024, 1280), 255)
    self.render_plants(self.image)
    self.render_weather(self.image)
    
    self.alpha_timer = Timer(float(self.config.get("plant_update_interval_hours")) * 3600.0, self.__cycle_primary)
    self.alpha_timer.start()

  def __cycle_secondary(self):
    self._image = self.image.copy()
    draw_context = ImageDraw.Draw(self._image)

    # Draw clock    
    hour = str(int(time.strftime("%I")))
    _time = time.strftime(":%M%p")
    _time = "{}{}".format(hour, _time)

    draw_context.text(
      xy=(35, 1199),
      text=_time,
      font=self.font_time,
      fill=255
    )

    self.generate_image()
    self.beta_timer = Timer(60.0, self.__cycle_secondary)
    self.beta_timer.start()

  def generate_image(self):
    image = ImageChops.invert(self._image)
    utils.write_image(image)

  def load_plants(self):
    with open('plants.json', 'r') as __plants:
      # Greater than 24 plants at one time will cause issues. 
      # Implement a paginating solution for this if the number of plants to be cared for exceeds 24.
      plants = json.loads(__plants.read()).get('plants')

    return [PlantCard(plant) for plant in plants]

  def load_weather(self):
    return WeatherState()

  def render_plants(self, image):
    row = 1
    for i, plant in enumerate(self.plants):
      card = plant.generate_image(self.font_plants)

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

  def render_weather(self, image):
    weather = self.weather.generate_image()
    image.paste(weather, (0, 1002))

  def init(self):
    # Look into fixing this at some point, clock timer is permanently off by however much it is
    # when first initialized. If it runs every 60 seconds starting at 12:00:30, it will
    # always be 30 seconds late updating the time.
    self.__cycle_primary()
    self.__cycle_secondary()

  def force_update(self):
    self.alpha_timer.cancel()
    self.beta_timer.cancel()

    self.init()