from typing import Any, List
from math import ceil

from classes.hero import Hero, Leader, Display
from classes.heroclass import Heroclass
from classes.talent import Talent
from classes.pet import Pet
from classes.map import Map
from classes.grid import Grid
from utils.language import Language
from utils.logger import Logger


class DisplayAttributes:
  def __init__(self, logger: Logger, elements_templates, language: Language, all_languages: List[Language], all_heroes: List[Hero], all_pets: List[Pet]):
    self.logger = logger
    self.elements_templates = elements_templates
    self.language = language
    self.template_processor = None
    self.all_languages = all_languages
    self.all_heroes = all_heroes
    self.all_pets = all_pets
  
  def init_template_processor(self, template_processor):
    self.template_processor = template_processor

  """ entry point to calc display data """
  def prepare_display_data(self, entity: Hero|Heroclass):
    if isinstance(entity, Hero):
      return self._prepare_hero_display_data(hero=entity)
    if isinstance(entity, Heroclass):
      return self._prepare_heroclass_display_data(heroclass=entity)
    if isinstance(entity, Talent):
      return self._prepare_talent_display_data(talent=entity)
    if isinstance(entity, Pet):
      return self._prepare_pet_display_data(pet=entity)
    if isinstance(entity, Map):
      return self._prepare_map_display_data(map=entity)
    return entity
    

  def _prepare_hero_display_data(self, hero: Hero):
    """ Prepare hero custom data with formatted values """
    self.logger.debug(f'Calculate custom data for {hero.name}')
    self._prepare_hero_attack_pattern_and_type(hero)
    self._prepare_hero_image(hero)
    self._prepare_hero_stats(hero)
    self._prepare_hero_talents(hero)
    self._prepare_hero_gear(hero)
    self._prepare_hero_stars(hero)
    self._prepare_hero_leader_data(hero)
    self._prepare_hero_talent_categories(hero)
    return hero

  def _prepare_hero_attack_pattern_and_type(self, hero: Hero):
    """ Prepare attack pattern and attack type """
    match hero.heroclass:
      case 'Assassin' | 'Druid' | 'Gladiator' | 'Guardian' | 'Knight' | 'Warrior' | 'Paladin' | 'Pirate':
        attack_type = 'Melee'
        attack_pattern = 'Cross'
      case 'Princess' | 'Barbarian' | 'Monk' | 'Rogue':
        attack_type = 'Melee'
        attack_pattern = 'Star'
      case 'Javelineer' | 'Archer' | 'Hunter':
        attack_type = 'Ranged'
        attack_pattern = 'Cross'
      case 'Ranger' | 'Bard':
        attack_type = 'Ranged'
        attack_pattern = 'Star'
      case 'Healer' | 'Witch' | 'Warlock' | 'Mage':
        attack_type = 'Magic'
        attack_pattern = 'Cross'
      case 'Elementalist':
        attack_type = 'Magic'
        attack_pattern = 'Star'
    setattr(hero.display, 'attack_type', attack_type)
    setattr(hero.display, 'attack_pattern', attack_pattern)

  def _prepare_hero_image(self, hero: Hero):
    """ Prepare image filename """
    image_name = f'{hero.name.replace(' \'', '_\'')}_Portrait.png'
    self._setattr_nested(hero.display, 'image', image_name)
  
  def _prepare_hero_stats(self, hero: Hero):
    """ Prepare attack and health stats """
    for ascend in ['A0', 'A1', 'A2', 'A3']:
      att_gear = ceil(int(getattr(hero.attack, ascend)) * 5 / 100 * sum(1 for g in getattr(hero.gear, ascend)[:3] if g))
      att_merge = ceil(int(getattr(hero.attack, ascend)) * 15 / 100)
      self._setattr_nested(hero.display, f'attack.{ascend}.gear', att_gear)
      self._setattr_nested(hero.display, f'attack.{ascend}.merge', att_merge)
      self._setattr_nested(hero.display, f'attack.{ascend}.total_base_gear', int(getattr(hero.attack, ascend)) + att_gear)
      self._setattr_nested(hero.display, f'attack.{ascend}.total_base_gear_merge', int(getattr(hero.attack, ascend)) + att_gear + att_merge)

      health_gear = ceil(int(getattr(hero.health, ascend)) * 5 / 100 * sum(1 for g in getattr(hero.gear, ascend)[3:] if g))
      health_merge = ceil(int(getattr(hero.health, ascend)) * 15 / 100)
      self._setattr_nested(hero.display, f'health.{ascend}.gear', health_gear)
      self._setattr_nested(hero.display, f'health.{ascend}.merge', health_merge)
      self._setattr_nested(hero.display, f'health.{ascend}.total_base_gear', int(getattr(hero.health, ascend)) + health_gear)
      self._setattr_nested(hero.display, f'health.{ascend}.total_base_gear_merge', int(getattr(hero.health, ascend)) + health_gear + health_merge)
    
    for attr in ['attack', 'health']:
      self._setattr_nested(hero.display, f'{attr}.max.base', max([int(self._getattr_nested(hero, f'{attr}.A0')), int(self._getattr_nested(hero, f'{attr}.A1')), int(self._getattr_nested(hero, f'{attr}.A2')), int(self._getattr_nested(hero, f'{attr}.A3'))]))
      self._setattr_nested(hero.display, f'{attr}.max.gear', max([int(self._getattr_nested(hero.display, f'{attr}.A0.gear')), int(self._getattr_nested(hero.display, f'{attr}.A1.gear')), int(self._getattr_nested(hero.display, f'{attr}.A2.gear')), int(self._getattr_nested(hero.display, f'{attr}.A3.gear'))]))
      self._setattr_nested(hero.display, f'{attr}.max.merge', max([int(self._getattr_nested(hero.display, f'{attr}.A0.merge')), int(self._getattr_nested(hero.display, f'{attr}.A1.merge')), int(self._getattr_nested(hero.display, f'{attr}.A2.merge')), int(self._getattr_nested(hero.display, f'{attr}.A3.merge'))]))
      self._setattr_nested(hero.display, f'{attr}.max.total', int(self._getattr_nested(hero.display, f'{attr}.max.base')) + int(self._getattr_nested(hero.display, f'{attr}.max.gear')) + int(self._getattr_nested(hero.display, f'{attr}.max.merge')))
      self._setattr_nested(hero.display, f'{attr}.A3_gain', f'{((int(self._getattr_nested(hero.display, f'{attr}.max.total')) - int(self._getattr_nested(hero.display, f'{attr}.A2.total_base_gear_merge'))) / int(self._getattr_nested(hero.display, f'{attr}.A2.total_base_gear_merge')) * 100):.1f}%')

    self._setattr_nested(hero.display, 'max_level', max([int(hero.levelmax.A0), int(hero.levelmax.A1), int(hero.levelmax.A2), int(hero.levelmax.A3)]))
  
  def _prepare_hero_talents(self, hero: Hero):
    """ Prepare formatted talents """
    traits_to_process = [{'attr': 'base', 'traits': [self.template_processor.transform_attribute_to_element(attribute=t, which_template= 'trait.translated_template', language=self.language) for t in hero.talents.base]}]
    traits_to_process.append({'attr': 'A1', 'traits': self.template_processor.transform_attribute_to_element(attribute=hero.talents.A1, which_template= 'trait.translated_template', language=self.language)})
    traits_to_process.append({'attr': 'A2', 'traits': self.template_processor.transform_attribute_to_element(attribute=hero.talents.A2, which_template= 'trait.translated_template', language=self.language)})
    traits_to_process.append({'attr': 'A3', 'traits': self.template_processor.transform_attribute_to_element(attribute=hero.talents.A3, which_template= 'trait.translated_template', language=self.language)})
    ascend_talents = [hero.talents.A1, hero.talents.A2, hero.talents.A3]
    traits_to_process.append({'attr': 'ascend', 'traits': [self.template_processor.transform_attribute_to_element(attribute=t, which_template= 'trait.translated_template', language=self.language) for t in ascend_talents]})
    traits_to_process.append({'attr': 'merge', 'traits': [self.template_processor.transform_attribute_to_element(attribute=t, which_template= 'trait.translated_template', language=self.language) for t in hero.talents.merge]})
    for traits in traits_to_process:
      if isinstance(traits.get('traits'), list):
        if len(traits.get('traits')) > 0:
          self._setattr_nested(hero.display, f'talents.{traits.get('attr')}.raw_list', '<br />'.join(traits.get('traits')))
          self._setattr_nested(hero.display, f'talents.{traits.get('attr')}.bullet_list', '<br />&nbsp;&nbsp;'.join([''] + traits.get('traits')))
        else:
          self._setattr_nested(hero.display, f'talents.{traits.get('attr')}.raw_list', '')
          self._setattr_nested(hero.display, f'talents.{traits.get('attr')}.bullet_list', '')
      else:
        self._setattr_nested(hero.display, f'talents.{traits.get('attr')}.raw_list', traits.get('traits'))

    self._setattr_nested(hero.display, f'talents.base.raw_list_picless', '<br />'.join(hero.talents.base))
    self._setattr_nested(hero.display, f'talents.merge.raw_list_picless', '<br />'.join(hero.talents.merge))
    
    traits_to_process = [{'attr': 'base', 'traits': [self.template_processor.transform_attribute_to_element(attribute=t, which_template= 'trait.no_text_template', language=self.language) for t in hero.talents.base]}]
    traits_to_process.append({'attr': 'ascend', 'traits': [self.template_processor.transform_attribute_to_element(attribute=t, which_template= 'trait.no_text_template', language=self.language) for t in ascend_talents]})
    traits_to_process.append({'attr': 'merge', 'traits': [self.template_processor.transform_attribute_to_element(attribute=t, which_template= 'trait.no_text_template', language=self.language) for t in hero.talents.merge]})
    for traits in traits_to_process:
      if len(traits.get('traits')) > 0:
        self._setattr_nested(hero.display, f'talents.{traits.get('attr')}.raw_list_no_text', ''.join(traits.get('traits')))
      else:
        self._setattr_nested(hero.display, f'talents.{traits.get('attr')}.raw_list_no_text', '')

    self._setattr_nested(hero.display, 'talents.A3.with_link', self.template_processor.transform_attribute_to_element(attribute=hero.talents.A3, which_template= 'trait.translated_linked_template', language=self.language))
  
  def _prepare_hero_gear(self, hero: Hero):   
    """ Prepare formatted gear """
    for ascend in ['A0', 'A1', 'A2', 'A3']:
      translated_gear_without_empty_gear = [self.language.translate(g) for g in getattr(hero.gear, ascend) if g != '']
      translated_gear_with_empty_gear = [self.language.translate(g) if g != '' else '' for g in getattr(hero.gear, ascend)]
      self._setattr_nested(hero.display, f'gear.{ascend}.raw_list', '<br />'.join([''] + translated_gear_without_empty_gear))
      self._setattr_nested(hero.display, f'gear.{ascend}.bullet_list', '<br />&nbsp;&nbsp;'.join([''] + translated_gear_without_empty_gear))
      self._setattr_nested(hero.display, f'gear.{ascend}.table_list', '||'.join(translated_gear_with_empty_gear))
    self._setattr_nested(hero.display, f'gear.A3.amulet', self.language.translate(hero.gear.A2[0]))
  
  def _prepare_hero_stars(self, hero: Hero):
    """ Prepare stars """
    self._setattr_nested(hero.display, 'stars', '&#11088; ' * int(hero.stars))
  
  def _prepare_hero_leader_data(self,  hero: Hero):
    """ Prepare formatted leader data """
    self._setattr_nested(hero.display, f'leadA.no_text', self._format_leader_bonus(leader=hero.leaderA, template_type='no_text_template'))
    self._setattr_nested(hero.display, f'leadB.no_text', self._format_leader_bonus(leader=hero.leaderB, template_type='no_text_template'))
    self._setattr_nested(hero.display, f'leadA.with_text', f'{self._format_leader_bonus(leader=hero.leaderA, template_type='template')} {self.language.translate('Heroes')}')
    self._setattr_nested(hero.display, f'leadB.with_text', f'{self._format_leader_bonus(leader=hero.leaderB, template_type='template')} {self.language.translate('Heroes')}')
  
  def _format_leader_bonus(self, leader: Leader, template_type: str) -> str:
    """ Format leader data into str """
    lead = ''   
    if leader.attack and leader.defense:
      lead = f'x{float(leader.attack):.2f} att {self.language.translate('and')} {float(leader.defense):.2f} def'
    elif leader.attack:
      lead = f'x{float(leader.attack):.2f} att'
    elif leader.defense:
      lead = f'x{float(leader.defense):.2f} def'
    elif leader.talent:
      lead = self.template_processor.transform_attribute_to_element(attribute=leader.talent, which_template=f'trait.{template_type}', language=self.language)
    if lead != '':
      lead += f' {self.language.translate('for')} '
      if leader.color:
        lead += self.template_processor.transform_attribute_to_element(attribute=leader.color, which_template=f'color.{template_type}', language=self.language)
      if leader.species:
        lead += self.template_processor.transform_attribute_to_element(attribute=leader.species, which_template=f'species.{template_type}', language=self.language)
      if leader.extra:
        lead += f' {self.language.translate('or')} {self.template_processor.transform_attribute_to_element(attribute=leader.extra, which_template=f'trait.{template_type}', language=self.language)}'
    return lead
  
  def _prepare_hero_talent_categories(self, hero: Hero):
    unique_talents = sorted(set(hero.talents.base) | set(hero.talents.merge) | {hero.talents.A1, hero.talents.A2, hero.talents.A3})
    talent_categories = ''
    for t in unique_talents:
      talent_categories += self.template_processor.transform_attribute_to_element(attribute=t, which_template='category.talent_template', language=self.language)
    setattr(hero.display, 'talent_categories', talent_categories)


  
  def _prepare_heroclass_display_data(self, heroclass: Heroclass):
    """ Prepare heroclass data with formatted values """
    setattr(heroclass.display, 'header', '!!'.join([self.template_processor.transform_attribute_to_element(attribute=c, which_template= 'heroclass.no_text_template', language=self.language) for c in heroclass.classes]))
    
    table_output = '|-\n'
    table_output += f'|- style="background-color: {heroclass.color_hex}"\n'

    for i in range(len(heroclass.table)):
      if i == 0:
        table_output += f'|{self.template_processor.transform_attribute_to_element(attribute=heroclass.name, which_template='color.no_text_template', language=self.language)}'
      else:
        table_output += f'|{self.template_processor.transform_attribute_to_element(attribute=heroclass.name, which_template='color.no_text_small_template', language=self.language)}'
        table_output += f' {self.template_processor.transform_attribute_to_element(attribute=heroclass.name, which_template=f'stars.template_{i}', language=self.language)}'
      table_output += '||'.join([''] + [str(h) for h in heroclass.table[i]])
      table_output += f'\n|-\n'
    setattr(heroclass.display, 'table_output', table_output)
    
    footer = f'|- style="background-color: #d3d3d3"\n'
    footer += f'|{self.language.translate('Totals')}'
    footer += '||'.join([''] + [str(h) for h in heroclass.totals])
    setattr(heroclass.display, 'footer', footer)
    
    return heroclass
  


  def _prepare_pet_display_data(self, pet: Pet):
    """ Prepare pet data with formatted values """
    self._prepare_pet_image(pet=pet)
    self._prepare_signature_heroes(pet=pet)
    self._prepare_pet_talents(pet=pet)
    setattr(pet.display, 'stars', '&#11088; ' * int(pet.stars))
    self._prepare_pet_stats(pet=pet)
    self._prepare_pet_manacost(pet=pet)
    return pet
  
  def _prepare_pet_image(self, pet: Pet):
    pet_image = pet.special_art_id if pet.special_art_id else pet.name
    setattr(pet.display, 'image', f'{pet_image}_Portrait.png')

  def _prepare_signature_heroes(self, pet: Pet):
    setattr(pet.display, 'signature', pet.signature[0])
    setattr(pet.display, 'signature_translated', self.language.translate(pet.signature[0]))
    signature_hero = next((h for h in self.all_heroes if h.name == pet.signature[0]), None)
    signature = self.template_processor.transform_attribute_to_element(attribute=signature_hero, which_template='portrait.translated_small_size_template', language=self.language) if signature_hero else ''
    setattr(pet.display, 'signature_template', signature)
    single_list = signature
    with_title = f"'''{self.language.translate('Signature Hero')} :''' {signature}"
    if len(pet.signature) > 1:
      setattr(pet.display, 'signature_bis', pet.signature[1])
      setattr(pet.display, 'signature_bis_translated', self.language.translate(pet.signature[1]))
      signature_bis_hero = next((h for h in self.all_heroes if h.name == pet.signature[1]), None)
      signature_bis = self.template_processor.transform_attribute_to_element(attribute=signature_bis_hero, which_template='portrait.translated_small_size_template', language=self.language) if signature_bis_hero else ''
      setattr(pet.display, 'signature_bis_template', signature_bis)
      single_list += f' {self.language.translate('and')} {signature_bis}'
      with_title += f"<br />\n'''{self.language.translate('Alternate Signature Hero')} :''' {signature_bis}"
    else:
      setattr(pet.display, 'signature_bis', '')
      setattr(pet.display, 'signature_bis_translated', '')
      setattr(pet.display, 'signature_bis_template', '')
    setattr(pet.display, 'signature_heroes_single_list', single_list)
    setattr(pet.display, 'signature_heroes_with_title', with_title)
    heroes_matching = [h for h in self.all_heroes if h.color == pet.color and h.heroclass == pet.petclass]
    if len(pet.signature) > 1:
      heroes_matching.append(signature_bis_hero)
    passive_matching_heroes = '<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'.join([self.template_processor.transform_attribute_to_element(attribute=h, which_template='portrait.translated_small_size_template', language=self.language) for h in sorted(heroes_matching, key=lambda x: x.name)])
    setattr(pet.display, 'passive_matching_heroes', passive_matching_heroes)
  
  def _prepare_pet_talents(self, pet: Pet):
    gold = self.template_processor.transform_attribute_to_element(attribute=pet.talents.gold, which_template=f'trait.template', language=self.language)
    gold = f'{gold.split('}}')[0]}|ForcePic={pet.talents.gold_pic}' + '}}'
    setattr(pet.display, 'gold_talent', gold)
    if pet.talents.full:
      full = self.template_processor.transform_attribute_to_element(attribute=pet.talents.full, which_template=f'trait.template', language=self.language)
    else:
      full = ''
    setattr(pet.display, 'full_talent', full)
    merge_with_text = []
    merge_no_text = []
    for index, m in enumerate(pet.talents.merge):
      merge_with_text.append(f'Merge{str(index + 1)}={self.template_processor.transform_attribute_to_element(attribute=m, which_template=f'trait.template', language=self.language)}')
      merge_no_text.append(self.template_processor.transform_attribute_to_element(attribute=m, which_template=f'trait.template', language=self.language))
    merge_talents = '|'.join(merge_with_text)
    self._setattr_nested(pet.display, 'merge_talents.table_list', merge_talents)
    merge_talents = '<br />&nbsp;&nbsp;'.join(merge_no_text)
    self._setattr_nested(pet.display, 'merge_talents.row_list', merge_talents)

  def _prepare_pet_stats(self, pet: Pet):
    talents_stats = int(pet.talents.base) + (int(pet.talents.silver) * 2)
    merge_stats = len([t for t in pet.talents.merge if 'Attack' in t])
    base_stats = int(pet.attack) - talents_stats - merge_stats
    stats_details = f'({self.language.translate('Base')} {str(base_stats)}% + {self.language.translate('Talents')} {str(talents_stats)}%'
    if merge_stats > 0:
      stats_details += f' + {self.language.translate('Merge')} {str(merge_stats)}%)'
    else:
      stats_details += ')'
    setattr(pet.display, 'stats_details', stats_details)

  def _prepare_pet_manacost(self, pet: Pet):
    merge_manacost = len([t for t in pet.talents.merge if 'Efficiency' in t])
    active_manacost = 25 - merge_manacost - int(pet.manacost)
    mana_capacity = len([t for t in pet.talents.merge if 'Capacity' in t])
    mana_reserves = len([t for t in pet.talents.merge if 'Reserves' in t])
    manacost = f'<br />&nbsp;&nbsp;{self.language.translate('Base')} : 25<br />&nbsp;&nbsp;{self.language.translate('Active')} : {str(active_manacost)}<br />&nbsp;&nbsp;{self.language.translate('Full merge')} : {str(pet.manacost)}<br />\n'
    if mana_capacity > 0:
      manacost += f"'''{self.language.translate('Mana Capacity')} :''' +{str(mana_capacity)} {self.language.translate('maximum Mana')}<br />\n"
    if mana_reserves > 0:
      manacost += f"'''{self.language.translate('Mana Reserves')} :''' +{str(mana_reserves)} {self.language.translate('Mana in the beginning of battle')}<br />\n"
    setattr(pet.display, 'manacost_details', manacost)


  def _prepare_talent_display_data(self, talent: Talent):
    """ Prepare talent data with formatted values """
    heroes = []
    for hero in talent.heroes:
      hero_output = f'[[{hero.get('name')}]] ('
      if len(hero.get('position')) > 1:
        hero_output += f'x{len(hero.get('position'))} : '
      hero_output += f'{', '.join(hero.get('position'))})'
      heroes.append(hero_output)
    setattr(talent.display, 'heroes_list', ', '.join(heroes))
    return talent
  
  def _prepare_map_display_data(self, map: Map):
    if len(map.images) > 1:
      pics = ''
      for i in range(1, len(map.images)):
        map_name = map.images[i]['filename'].split('Spire')[1].replace('_', ' ')
        pics += f'\'\'\'{map_name}\'\'\'\n[[File:{map.images[i]['filename']}.png|Frameless]]\n\n'
    else:
      pics = f'[[File:{map.images[0]['filename']}.png|Frameless]]'
    setattr(map.display, 'pics', pics)
    return map
    
  
  def _setattr_nested(self, obj, attribute_path: str, value) -> Any:
    """ Set multiple nested attributes which don't exist initially
      Args:
        obj: object with initial existing attribute (ex: hero.display)
        attribute_path: str with new attributes to create (ex: talents.base.raw_list)
      Returns:
        updated obj with new attribute (ex: hero.display.talents.base.raw_list)
    """
    attrs = attribute_path.split('.')
    for attr in attrs[:-1]:
      if not hasattr(obj, attr):
        setattr(obj, attr, Display())
      obj = getattr(obj, attr)
    setattr(obj, attrs[-1], value)

  def _getattr_nested(self, obj: Any, attribute_path: str) -> Any:
    """ Get the value of a nested attribute with multiple nestings handler
      Args:
        obj: object with initial existing attribute (ex: hero.display)
        attribute_path: str with attributes to get (ex: talents.base.raw_list)
      Returns:
        value of the obj (ex: hero.display.talents.base.raw_list.value)
    """
    try:
      current = obj
      for attr in attribute_path.split('.'):
        current = getattr(current, attr, None)
        if current is None:
          return None
      return current
    except (AttributeError, TypeError):
      return None