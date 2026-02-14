from typing import Dict, List

 
class Talent:
  def __init__(self):
    self.base = 0
    self.silver = 0
    self.gold = ''
    self.gold_pic = ''
    self.full = ''
    self.merge = []
  
  def from_dict(cls, data: Dict):
    return cls(
      base = data.get('base', ''),
      silver = data.get('silver', ''),
      gold = data.get('gold', ''),
      gold_pic = data.get('gold_pic', ''),
      full = data.get('full', ''),
      merge = data.get('merge', [])
    )

  def to_dict(self) -> Dict:
    return {
      'base': self.base,
      'silver': self.silver,
      'gold': self.gold,
      'gold_pic': self.gold_pic,
      'full': self.full,
      'merge': self.merge
    }

class FileClass:
  def __init__(self):
    self.drive = None
    self.wiki = None

  def from_dict(cls, data: Dict):
    return cls(
      drive = data.get('drive', None),
      wiki = data.get('wiki', None)
    )
  
  def to_dict(self) -> Dict:
    return {
      'drive': self.drive,
      'wiki': self.wiki
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
    self.file = FileClass()
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
    self.talents.gold_pic = data[header.index('Gold Talent Pic')]
    self.talents.full = data[header.index('Full Talent')] if data[header.index('Full Talent')] != '' else None
    talents_start = header.index('Talents')
    talents_end = self._get_last_index(header, 'Talents') + 1
    for i in range(talents_start, talents_end):
      self.talents.merge.append(data[i])
    
  def _get_last_index(self, list, element):
    for i in range(len(list) - 1, -1, -1):
      if list[i] == element:
        return i
    self.logger.error(f'{element} not in header, please check data and run again')

def match_images_with_pets(ctx, images: List[Dict], attribute: str):
  """ Match image list with extracted pets objects """
  for image in images:
    cleaned_image_name = image.get('name').split('.png')[0][3:]
    found_pet = next((pet for pet in ctx.pets if cleaned_image_name == pet.signature[0]), None)
    if found_pet:
      setattr(found_pet.file, attribute, image)
    else:
      cleaned_image_name = image.get('name').split('.png')[0].split('_Portrait')[0].replace('0', '').replace('_',' ')
      found_pet = next((pet for pet in ctx.pets if cleaned_image_name == pet.name), None)
      if found_pet:
        setattr(found_pet.file, attribute, image)
      else:
        found_pet = next((pet for pet in ctx.pets if cleaned_image_name == pet.special_art_id), None)
        if found_pet:
          setattr(found_pet.file, attribute, image)