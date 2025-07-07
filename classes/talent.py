from typing import List, Dict
from collections import defaultdict

from classes.hero import Hero, Display


class Talent:
  def __init__(self, name: str, heroes: List[Dict]):
    self.name = name
    self.heroes = heroes
    self.display = Display()
  
  def to_dict(self) -> Dict:
    return {
      'name': self.name,
      'heroes': self.heroes
    }


def create_talents(heroes: List[Hero]) -> List[Talent]:
  """ Extract unique talents
    Args:
      heroes: list[Hero] to analyze
    Returns:
      list[Talent] with all unique talents and its associated heroes
  """
  talents_data = defaultdict(list)
  for hero in heroes:
    hero_talent_positions = get_hero_talent_positions(hero.talents)
    for talent_name, positions in hero_talent_positions.items():
      talents_data[talent_name].append({'name': hero.name, 'position': positions})
  talents = []
  for talent_name, heroes_data in talents_data.items():
    talents.append(Talent(talent_name, heroes_data))
  return sorted(talents, key=lambda t: t.name)
  
def get_hero_talent_positions(hero_talents) -> Dict[str, List[str]]:
  """ Gets positions for each talent of a Hero """
  talent_positions = defaultdict(list)
  if hero_talents.base:
    for i, talent in enumerate(hero_talents.base):
      talent_positions[talent].append(f'base {i + 1}')
  for attr in ['A1', 'A2', 'A3']:
    talent = getattr(hero_talents, attr)
    talent_positions[talent].append(f'ascend {attr[-1]}')
  if hero_talents.merge:
    for i, talent in enumerate(hero_talents.merge):
      talent_positions[talent].append(f'merge {i + 1}')
  return dict(talent_positions)