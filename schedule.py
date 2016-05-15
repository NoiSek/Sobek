import datetime
import json

def generate_schedule():
  config = None
  plants = None

  with open('config.json', 'r') as __config:
    with open('plants.json', 'r') as __plants:
      config = json.loads(__config.read())
      plants = json.loads(__plants.read()).get("plants")

  epoch = config.get("epoch")
  month, day, year = [int(x) for x in epoch.split("/")]
  epoch = datetime.date(year, month, day)

  todays_date = datetime.date.today()
  
  water_today = []
  water_tomorrow = []
  water_soon = []

  for plant in plants:
    delta = (todays_date - epoch).days
    cycle = int(plant.get("water_cycle"))
    print(delta % cycle)

    if (delta % cycle) == 0:
      water_today.append(plant)
      print("{}: {} needs to be watered today.".format(
          plant.get("ID"),
          plant.get("name")
        )
      )

    if (delta % cycle) == (cycle - 1):
      water_tomorrow.append(plant)
      print("{}: {} needs to be watered tomorrow.".format(
          plant.get("ID"),
          plant.get("name")
        )
      )

    if (delta % cycle) == (cycle - 2):
      water_soon.append(plant)
      print("{}: {} needs to be watered soon.".format(
          plant.get("ID"),
          plant.get("name")
        )
      )
  
if __name__ == "__main__":
  generate_schedule()