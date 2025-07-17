from typing import Dict, List

 
class Talent:
  def __init__(self):
    self.base = 0
    self.silver = 0
    self.gold = ''
    self.full = ''
    self.merge = []
  
  def from_dict(cls, data: Dict):
    return cls(
      base = data.get('base', ''),
      silver = data.get('silver', ''),
      gold = data.get('gold', ''),
      full = data.get('full', ''),
      merge = data.get('merge', [])
    )

  def to_dict(self) -> Dict:
    return {
      'base': self.base,
      'silver': self.silver,
      'gold': self.gold,
      'full': self.full,
      'merge': self.merge
    }
  
  
""" Empty Display class to be filled by display_attributes.py """
class Display():
  pass


""" Pet class """
class Pet:
  def __init__(self, ctx):
    self.logger = ctx.logger
    self.elements_templates = ctx.elements_templates

    self.name = None
    self.special_art_id = None
    self.petclass = None
    self.color = None
    self.stars = None
    self.attack = None
    self.health = None
    self.manacost = None
    self.signature = None
    self.talents = Talent()
    self.display = Display()

  def to_dict(self) -> Dict:
    return {
      'name': self.name,
      'special_art_id': self.special_art_id,
      'petclass': self.petclass,
      'color': self.color,
      'stars': self.stars,
      'attack': self.attack,
      'health': self.health,
      'manacost': self.manacost,
      'signature': self.signature,
      'talents': self.talents.to_dict(),
    }
  
  """ class method to transform sheets data into pet object """
  def create_pet(self, data, header):
    """ Create Pet object
      Args:
        data: line from sheets representing a pet
        header: Pet's sheet header row
      Returns:
        pet object (self)
    """
    self.name = data[header.index('Name')]
    self.special_art_id = data[header.index('Special_Art_ID')] if data[0][header.index('Special_Art_ID')] != '' else None
    self.petclass = data[header.index('Class')]
    self.color = data[header.index('Color')]
    self.stars = data[header.index('Stars')]
    self.attack = data[header.index('Attack Cap')]
    self.health = data[header.index('Health Cap')]
    self.manacost = data[header.index('Mana Cost')]
    self._get_signature_heroes(data=data, header=header)
    self._get_talents(data=data, header=header)
    return self
  
  """ class private methods for sheets data parsing """
  def _get_signature_heroes(self, data, header):
    signature_start = header.index('Signature')
    self.signature = [data[s] for s in range(signature_start, signature_start + 2) if data[s] != '']
    
  
  def _get_talents(self, data, header):
    self.talents.base = data[header.index('Base Talents')]
    self.talents.silver = data[header.index('Silver Talents')]
    self.talents.gold = data[header.index('Gold Talent')]
    self.talents.full = data[header.index('Full Talent')] if data[header.index('Full Talent')] != '' else None
    talents_start = header.index('Talents')
    talents_end = self._get_last_index(header, 'Talents')
    for i in range(talents_start, talents_end):
      self.talents.merge.append(data[i])
    
  def _get_last_index(self, list, element):
    for i in range(len(list) - 1, -1, -1):
      if list[i] == element:
        return i
    self.logger.error(f'{element} not in header, please check data and run again')