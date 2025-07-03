from typing import Dict, List


""" Hero sub-classes """
class StatsByAscend:
  def __init__(self):
    self.A0 = None
    self.A1 = None
    self.A2 = None
    self.A3 = None

  def from_dict(cls, data: Dict):
    return cls(
      A0 = data.get('A0', None),
      A1 = data.get('A0', None),
      A2 = data.get('A0', None),
      A3 = data.get('A0', None)
    )

  def to_dict(self) -> Dict:
    return {
      'A0': self.A0,
      'A1': self.A1,
      'A2': self.A2,
      'A3': self.A3
    }

class Leader:
  def __init__(self):
    self.attack = None
    self.defense = None
    self.color = None
    self.species = None
    self.talent = None
    self.extra = None

  def from_dict(cls, data: Dict):
    return cls(
      attack = data.get('attack', None),
      defense = data.get('defense', None),
      color = data.get('color', None),
      species = data.get('species', None),
      talent = data.get('talent', None),
      extra = data.get('extra', None)
    )

  def to_dict(self) -> Dict:
    return {
      'attack': self.attack,
      'defense': self.defense,
      'color': self.color,
      'species': self.species,
      'talent': self.talent,
      'extra': self.extra
    }
  
class Talent:
  def __init__(self):
    self.base = []
    self.A1 = None
    self.A2 = None
    self.A3 = None
    self.merge = []
  
  def from_dict(cls, data: Dict):
    return cls(
      base = data.get('attack', []),
      A1 = data.get('A1', ''),
      A2 = data.get('A2', ''),
      A3 = data.get('A3', ''),
      merge = data.get('merge', [])
    )

  def to_dict(self) -> Dict:
    return {
      'base': self.base,
      'A1': self.A1,
      'A2': self.A2,
      'A3': self.A3,
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
  
  
""" Empty Display class to be filled by prepare_display_data """
class Display():
  pass


""" Hero class """
class Hero:
  def __init__(self, ctx):
    self.logger = ctx.logger
    self.playsome_data = ctx.playsome_data
    self.elements_templates = ctx.elements_templates

    self.name = None
    self.playsome_name = None
    self.playsome_art_id = None
    self.file = FileClass()
    self.portrait = None
    self.heroclass = None
    self.stars = None
    self.levelmax = StatsByAscend()
    self.AI = None
    self.AI_speed = None
    self.attack = StatsByAscend()
    self.health = StatsByAscend()
    self.color = None
    self.species = None
    self.talents = Talent()
    self.gear = StatsByAscend()
    self.exclusivity = None
    self.leaderA = Leader()
    self.leaderB = Leader()
    self.display = Display()

  def to_dict(self) -> Dict:
    return {
      'name': self.name,
      'playsome_name': self.playsome_name,
      'playsome_art_id': self.playsome_art_id,
      'heroclass': self.heroclass,
      'stars': self.stars,
      'levelmax': self.levelmax.to_dict(),
      'AI': self.AI,
      'AI_speed': self.AI_speed,
      'attack': self.attack.to_dict(),
      'health': self.health.to_dict(),
      'color': self.color,
      'species': self.species,
      'talent' : self.talents.to_dict(),
      'gear': self.gear.to_dict(),
      'exclusivity': self.exclusivity,
      'leaderA': self.leaderA.to_dict(),
      'leaderB': self.leaderB.to_dict()
    }
  
  """ class method to transform sheets data into hero object """
  def create_hero(self, data, header):
    """ Create Hero object
      Args:
        data: list of lines (group) with same hero name
        header: Playsome's sheet header row
      Returns:
        hero object (self)
    """
    self.playsome_name = data[0][header.index('Name')]
    self.name = self._recolor_hero(self.playsome_name)
    self.playsome_art_id = data[0][header.index('Art ID')].replace('0', '')
    self.heroclass = data[0][header.index('Class')]
    self.stars = data[0][header.index('Stars')]
    self.AI = str.capitalize(data[0][header.index('AI')][:-3])
    if self.AI == 'Support':
      self.AI = 'Supporter'
    self.AI_speed = str(data[0][header.index('Speed')])
    self.color = data[0][header.index('Color')]
    self.species = data[0][header.index('Species')]
    self.exclusivity = self.playsome_data['Events'][data[0][header.index('Exclusivity')]] if data[0][header.index('Exclusivity')] != '' else ''
    for line in data:
      ascend = f'A{line[header.index('Ascension')]}'
      setattr(self.levelmax, ascend, line[header.index('LevelCap')])
      setattr(self.attack, ascend, line[header.index('Attack Cap')])
      setattr(self.health, ascend, line[header.index('Health Cap')])
      setattr(self.gear, ascend, self._get_gear(line, header))
    self._get_talents(data=data, header=header)
    self._get_leader(line=line[:-1], header=header)
    return self
  
  """ class private methods for sheets data parsing """
  def _get_gear(self, line, header):
    to_return = []
    for i, case in enumerate(header):
      if case == 'Gear':
        to_return.append(line[i])
    return to_return
  
  def _get_talents(self, data, header):
    talents_start = header.index('Talents')
    talents_end = self._get_last_index(header, 'Talents')
    for i in range(talents_start, talents_end):
      if data[0][i] == '':
        ascend_talents_start = i
        break
      self.talents.base.append(data[0][i].replace(' Of ',' of '))
    self.talents.A1 = data[1][ascend_talents_start].replace(' Of ',' of ')
    self.talents.A2 = data[2][ascend_talents_start + 1].replace(' Of ',' of ')
    self.talents.A3 = data[3][ascend_talents_start + 2].replace(' Of ',' of ')

    merge_talents_start = header.index('Mastery Talents')
    self.talents.merge = [data[0][mt].replace(' Of ',' of ') for mt in range(merge_talents_start, merge_talents_start + 3) if data[0][merge_talents_start] != '']

  def _get_last_index(self, list, element):
    for i in range(len(list) - 1, -1, -1):
      if list[i] == element:
        return i
    self.logger.error(f'{element} not in header, please check data and run again')

  def _get_leader(self, line, header) -> Leader:
    match line[header.index('LeaderBuffA')]:
      case 'ExtraTime':
        self.leaderA.talent = self._add_spaces_to_talent(line[header.index('LeaderBuffA')])
        self.leaderA.color = line[header.index('Req A')]
      case 'LeaderAttack':
        self.leaderA.color = line[header.index('Req A')]
        self.leaderA.attack = line[header.index('LeaderAtkMultiplier')]
        self.leaderB.species = line[header.index('Req B')]
        self.leaderB.defense = line[header.index('LeaderDefMultiplier')]
        if line[header.index('LeaderRequirement Operator')] == 'OR':
          self.leaderA.extra = self.playsome_data['Events'][line[header.index('Req A2')]]
      case _:
        self.leaderA.color = line[header.index('Req A')]
        match line[header.index('LeaderRequirement Operator')]:
          case 'AND':
            self.leaderA.species = line[header.index('Req A2')]
          case 'OR':
            self.leaderA.extra = self.playsome_data['Events'][line[header.index('Req A2')]]
        self.leaderA.attack = line[header.index('LeaderAtkMultiplier')]
        self.leaderA.defense = line[header.index('LeaderDefMultiplier')]
        self.leaderB.species = line[header.index('Req B')]
        if line[header.index('LeaderBuffB')].startswith('Bard'):
          self.leaderB.talent = self._bard_talent_special_case(line[header.index('LeaderBuffB')])
        else:
          self.leaderB.talent = self._add_spaces_to_talent(line[header.index('LeaderBuffB')])

  def _bard_talent_special_case(self, talent):
    try:
      return self.playsome_data['Talents'][talent]
    except:
      self.logger.error(f'{talent} not in Talents\' section of playsome_data.yml, please add it and run again')

  def _add_spaces_to_talent(self, talent):
    if not talent:
      return talent
    to_return = talent[0]
    for char in talent[1:]:
      if char.isupper():
        to_return += ' ' + char
      else:
        to_return += char
    return to_return
  
  def _recolor_hero(self, name: str):
    try:
      if name[-1] == 'S':
        return self.playsome_data['Heroes'][name]
      else:
        return name
    except:
      self.logger.error(f'{name} not in Heroes\' section of playsome_data.yml, please add it and run again')


def match_images_with_heroes(ctx, images: List[str], attribute: str):
  """ Match image list with extracted heroes objects """
  for image in images:
    cleaned_image_name = image.get('name').split('.png')[0].split('_Portrait')[0].replace('0', '').replace('_',' ')
    found_hero = next((hero for hero in ctx.heroes if cleaned_image_name == hero.playsome_art_id), None)
    if found_hero:
      setattr(found_hero.file, attribute, image)
    else:
      found_hero = next((hero for hero in ctx.heroes if cleaned_image_name == hero.name), None)
      if found_hero:
        setattr(found_hero.file, attribute, image)