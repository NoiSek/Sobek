from PIL import Image, ImageDraw, ImageChops, ImageFont
from textwrap import TextWrapper
from functools import lru_cache
from utils import load_config

import urllib.request
import time
import json

class WeatherState:
  """Handle and return current Weather state, provide
  corresponding weather icons.
  """
  def __init__(self):
    try:
      self.config = self.__get_config()
      self.api_key = self.config['wunderground_key']
      self.state = {}
    except IndexError:
      print("Wunderground API key missing from config.")

      import sys
      sys.exit()

    self.api_string = "http://api.wunderground.com/api/{}/conditions/forecast/q/{}/{}.json".format(
      self.api_key,
      self.config.get('wunderground_state'),
      self.config.get('wunderground_city').replace(" ", "_")
    )

    # Revise this in the future
    self.__get_fonts()

  def __get_fonts(self):
    self.fonts = {
      "base": ImageFont.truetype('fonts/OpenSans-Bold.ttf', 18),
      "temperature": ImageFont.truetype('fonts/OpenSans-BoldItalic.ttf', 30),
      "temperature_feels_like": ImageFont.truetype('fonts/OpenSans-BoldItalic.ttf', 18),
      "time": ImageFont.truetype('fonts/OpenSans-Bold.ttf', 30),
      "date": ImageFont.truetype('fonts/OpenSans-Bold.ttf', 24),
      "forecast_description": ImageFont.truetype('fonts/OpenSans-Bold.ttf', 12)
    }

  def __get_config(self):
    return load_config()

  def generate_forecasts(self):
    verbose_forecasts = self.state['forecast']['txt_forecast']['forecastday']
    verbose_forecasts = list(filter(lambda x: x['period'] % 2 == 0, verbose_forecasts))
    verbose_forecasts = [x['fcttext'].split(".")[0] for x in verbose_forecasts]

    forecasts = self.state['forecast']['simpleforecast']['forecastday']
    forecast_images = []
    
    for i, forecast in enumerate(forecasts):
      # Base plate
      base = Image.new('1', (135, 238), 0)
      
      # Paste forecast
      icon = self.get_icon(forecast['icon'])
      base.paste(icon, (3, 0))

      # Draw Day
      draw_context = ImageDraw.Draw(base)
      day = "{}".format(forecast['date']['weekday_short'])
      draw_context.text(
        xy=(3, 128 + 15),
        text=day,
        font=self.fonts.get("base"),
        fill=255
      )

      # Right align and draw Temperature
      windspeed = "{}° / {}°".format(
        forecast['high']['fahrenheit'],
        forecast['low']['fahrenheit']
      )
      windspeed_width, windspeed_height = draw_context.textsize(
        windspeed, self.fonts.get("base")
      )
      draw_context.text(
        xy=((135 - windspeed_width) - 10, 128 + 15),
        text=windspeed,
        font=self.fonts.get("base"),
        fill=255
      )

      forecast_string = verbose_forecasts[i]
      wrapper = TextWrapper(width=20)
      forecast_string = "\n".join(wrapper.wrap(forecast_string)) + "."

      draw_context.text(
        xy=(3, 128 + 15 + 25), 
        text=forecast_string,
        font=self.fonts.get("forecast_description"),
        fill=255
      )

      forecast_images.append(base)

    return forecast_images

  def generate_image(self):
    self.update()

    ## Initialize background plate
    background = Image.new('1', (1024, 278), 0)
    draw_context = ImageDraw.Draw(background)
    
    ## Paste current conditions
    current_weather = self.get_icon(self.state['current_observation']['icon'])
    background.paste(current_weather, (35, 30))

    ## Draw temperature
    temperature = "{}° F".format(str(round(self.state['current_observation']['temp_f'])))
    draw_context.text(
      xy=(35 + 128 + 30, 50), 
      text=temperature,
      font=self.fonts.get("temperature"), 
      fill=255
    )

    ## Draw 'feels like' temperature, calculate heights to align text.
    temperature_feels_like = "Feels like {}° F".format(str(round(float(self.state['current_observation']['feelslike_f']))))
    
    temperature_width, temperature_height = draw_context.textsize(
      temperature, self.fonts.get("temperature")
    )
    
    temperature_feels_like_width, temperature_feels_like_height = draw_context.textsize(
      temperature_feels_like, self.fonts.get("temperature_feels_like")
    )
    
    feels_x_pos = (430 - temperature_feels_like_width)
    feels_y_pos = (50 + temperature_height) - temperature_feels_like_height

    draw_context.text(
      xy=(feels_x_pos, feels_y_pos), 
      text=temperature_feels_like,
      font=self.fonts.get("temperature_feels_like"), 
      fill=255
    )

    ## Draw conditions description and wind speed.
    description_and_wind = "{}.\n{} winds at {} / {} MPH.".format(
      self.state['current_observation']['weather'].split(".")[0],
      self.state['current_observation']['wind_dir'],
      self.state['current_observation']['wind_mph'],
      self.state['current_observation']['wind_gust_mph']
    )
    draw_context.text(
      xy=(35 + 128 + 30, 50 + temperature_height + 30),
      text=description_and_wind,
      font=self.fonts.get("base"),
      fill=255
    )

    # Align and draw text representation of day
    hour = str(int(time.strftime("%I")))
    _time = time.strftime(":%M%p")
    _time = "{}{}".format(hour, _time)

    day = time.strftime(", %A,")
    time_width, time_height = draw_context.textsize(_time, self.fonts.get("time"))
    day_width, day_height = draw_context.textsize("Align", self.fonts.get("date"))

    day_x_pos = (35 + time_width + 2)
    day_y_pos = (205 + time_height) - day_height

    draw_context.text(
      xy=(day_x_pos, day_y_pos),
      text=day,
      font=self.fonts.get("date"),
      fill=255
    )

    # Align and draw day and month
    day = int(time.strftime("%d"))
    month = time.strftime("%B")
    
    if 4 <= day <= 20 or 24 <= day <= 30:
      suffix = "th"
    else:
      suffix = ["st", "nd", "rd"][day % 10 - 1]

    day_and_month = "The {}{} of {}".format(day, suffix, month)
    day_and_month_x_pos = 35
    day_and_month_y_pos = 200 + time_height

    draw_context.text(
      xy=(day_and_month_x_pos, day_and_month_y_pos),
      text=day_and_month,
      font=self.fonts.get("date"),
      fill=255
    )

    ## Draw forecasts
    # Draw divisor line
    draw_context.rectangle(xy=[(460, 20), (462, 255)], fill=255, outline=255)
    forecasts = self.generate_forecasts()

    for i, forecast in enumerate(forecasts):
      background.paste(forecast, (444 + (i * 135) + 40, 30))

    return background

  @lru_cache(maxsize=None)
  def get_icon(self, icon_name):
    icon_set_path = "images/weather/{}".format(self.config.get("wunderground_icon_set"))
    icon = Image.open("{}/{}.png".format(
        icon_set_path,
        icon_name
      )
    )

    return ImageChops.invert(icon)

  def update(self):
    #response = urllib.request.urlopen(self.api_string)

    #if response.getcode() == 200:
    #  self.state = json.loads(response.read().decode('utf-8'))
    with open('blank.json', 'r') as f:
      self.state = json.loads(f.read())

  def __repr__(self):
    return("<WeatherState {},{}>".format(
      self.config.get('wunderground_city'),
      self.config.get('wunderground_state')
    ))