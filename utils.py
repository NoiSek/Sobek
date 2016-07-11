from PIL import Image, ImageChops

import datetime
import struct
import json
import os

def bytes_slice(e, n):
  """Split data set into slices of 'n'.
  May be necessary for converting from other image formats,
  but does not appear to be necessary for PNG files 
  as this model of e-ink panel stated in the specification.
  """

  summation = []

  for i, e in enumerate(e):
    if (i + 1) % n == 0:
      yield summation

      summation = []

    summation.append(e)

def clean_output_dir():
  config = load_config()

  output_dir = config.get("output_dir")
  output_path = os.path.join(config.get("output_dir"), "out.epd")

  if os.path.exists(output_dir):  
    if os.path.exists(output_path):
      os.remove(output_path)

  else:
    raise Exception("Output directory path does not exist or is not accessible.")

def generate_config():
  defaults = {
    "epoch": datetime.datetime.today().strftime("%m/%d/%Y"),
    "output_dir": "output",
    "plant_update_interval_hours": "1",
    "wunderground_key": "",
    "wunderground_icon_set": "flat",
    "wunderground_city": "Seattle",
    "wunderground_state": "WA"
  }

  if os.path.exists('config.json'):
    return True

  else:
    with open('config.json', 'w') as config:
      config.write(json.dumps(defaults))

def load_config():
  generate_config()

  with open('config.json', 'r') as __config:
    config = json.loads(__config.read())

  return config

def trim(image):
  background = Image.new(image.mode, image.size, image.getpixel((0,0)))
  difference = ImageChops.difference(image, background)
  difference = ImageChops.add(difference, difference, 2.0, -100)
  bbox = difference.getbbox()
  
  if bbox:
    return image.crop(bbox)

def write_image(image):
  """Writes a 1024x1280 PIL.Image object to EPD format."""
  config = load_config()
  clean_output_dir()
  output_path = os.path.join(config.get("output_dir"), "out.epd")

  panel_header_data = [
    0x3D,    # panel_type
    0x0400,  # x_res
    0x0500,  # y_res
    0x01,    # color_depth
    0x00     # pixel_data_format_type
  ]

  panel_header_data_reserved_filler = 0x00 # RFU - 9 bits

  with open(output_path, "bw") as epdfile:
    bits = panel_header_data + [panel_header_data_reserved_filler for i in range(9)]
    header = struct.pack(
      'b h h b b b b b b b b b b b', *bits 
    )

    payload = header + image.tobytes()

    try:
      epdfile.write(payload)
      ImageChops.invert(image).save(os.path.join("output", "preview.png"))

    except (IOError, OSError):
      print("Error writing output image to epd file.")
      raise