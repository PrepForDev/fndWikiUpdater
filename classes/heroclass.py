from typing import Dict, List

from classes.hero import Hero, Display

""" Empty Heroclass class to be filled by display_attributes.py """
class Heroclass:
  def __init__(self, name, color_hex, classes, table, totals):
    self.name = name
    self.color_hex = color_hex
    self.classes = classes
    self.table = table
    self.totals = totals
    self.display = Display()


def create_heroclasses(heroes: List[Hero]) -> List[Dict]:
  """ Function to transform heroes data into list of color dictionaries """
  color_configs = [
      {'name': 'Blue', 'hex': '#d0e7f9'},
      {'name': 'Dark', 'hex': '#e6d5f7'},
      {'name': 'Green', 'hex': '#d4edda'},
      {'name': 'Light', 'hex': '#fff3cd'},
      {'name': 'Red', 'hex': '#f8d7da'},
  ]

  different_heroclasses = set()
  for hero in heroes:
    different_heroclasses.add(hero.heroclass)
  different_heroclasses = sorted(different_heroclasses)

  to_return = []
  general_totals = [0] * (len(different_heroclasses) + 1)
  for color_config in color_configs:
    table = []
    total_row = [0] * (len(different_heroclasses) + 1)
    star_rows = []
    for star_level in range(1, 6):
      star_rows.append([0] * (len(different_heroclasses) + 1))
    
    for hero in heroes:
      if hero.color == color_config.get('name'):
        class_index = different_heroclasses.index(hero.heroclass)         
        total_row[class_index] += 1
        star_rows[int(hero.stars) - 1][class_index] += 1
    
    for i in range(len(different_heroclasses)):
      total_row[len(different_heroclasses)] += total_row[i]
      for star in range(5):
        star_rows[star][len(different_heroclasses)] += star_rows[star][i]
      general_totals[i] += total_row[i]

    general_totals[len(different_heroclasses)] += total_row[len(different_heroclasses)]
    
    table.append(total_row)
    table.extend(star_rows)

    to_return.append(Heroclass(name=color_config.get('name'), color_hex=color_config.get('hex'), classes=different_heroclasses, table=table, totals=general_totals))
  return to_return