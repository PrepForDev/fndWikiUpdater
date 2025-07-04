from typing import Any, List
from math import ceil

from classes.hero import Hero, Leader, Display
from utils.language import Language
from utils.logger import Logger


class DisplayAttributes:
  def __init__(self, logger: Logger, elements_templates, language: Language, all_languages: List[Language]):
    self.logger = logger
    self.elements_templates = elements_templates
    self.language = language
    self.template_processor = None
    self.all_languages = all_languages
  
  def init_template_processor(self, template_processor):
    self.template_processor = template_processor

  """ class method to calc display data (by language or not)"""
  def prepare_hero_display_data(self, hero: Hero):
    """ Prepare hero custom data with formatted values """
    self.logger.debug(f'Calculate custom data for {hero.name}')
    self._prepare_attack_pattern_and_type(hero)
    self._prepare_image(hero)
    self._prepare_stats(hero)
    self._prepare_talents(hero)
    self._prepare_gear(hero)
    self._prepare_stars(hero)
    self._prepare_leader_data(hero)
    self._prepare_talent_categories(hero)
    return hero

  def _prepare_attack_pattern_and_type(self, hero: Hero):
    """ Prepare attack pattern and attack type """
    match hero.heroclass:
      case 'Assassin' | 'Druid' | 'Guardian' | 'Knight' | 'Warrior' | 'Paladin' | 'Pirate':
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

  def _prepare_image(self, hero: Hero):
    """ Prepare image filename """
    image_name = f'{hero.name.replace(' \'', '_\'')}_Portrait.png'
    self._setattr_nested(hero.display, 'image', image_name)
  
  def _prepare_stats(self, hero: Hero):
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
  
  def _prepare_talents(self, hero: Hero):
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
  
  def _prepare_gear(self, hero: Hero):   
    """ Prepare formatted gear """
    for ascend in ['A0', 'A1', 'A2', 'A3']:
      translated_gear_without_empty_gear = [self.language.translate(g) for g in getattr(hero.gear, ascend) if g != '']
      translated_gear_with_empty_gear = [self.language.translate(g) if g != '' else '' for g in getattr(hero.gear, ascend)]
      self._setattr_nested(hero.display, f'gear.{ascend}.raw_list', '<br />'.join([''] + translated_gear_without_empty_gear))
      self._setattr_nested(hero.display, f'gear.{ascend}.bullet_list', '<br />&nbsp;&nbsp;'.join([''] + translated_gear_without_empty_gear))
      self._setattr_nested(hero.display, f'gear.{ascend}.table_list', '||'.join(translated_gear_with_empty_gear))
    self._setattr_nested(hero.display, f'gear.A3.amulet', self.language.translate(hero.gear.A2[0]))
  
  def _prepare_stars(self, hero: Hero):
    """ Prepare stars """
    self._setattr_nested(hero.display, 'stars', '&#11088; ' * int(hero.stars))
  
  def _prepare_leader_data(self,  hero: Hero):
    """ Prepare formatted leader data """
    self._setattr_nested(hero.display, f'leadA.no_text', self._format_leader_bonus(leader=hero.leaderA, template_type='no_text_template'))
    self._setattr_nested(hero.display, f'leadB.no_text', self._format_leader_bonus(leader=hero.leaderB, template_type='no_text_template'))
    self._setattr_nested(hero.display, f'leadA.with_text', f'{self._format_leader_bonus(leader=hero.leaderA, template_type='template')} {self.language.translate('Heroes')}')
    self._setattr_nested(hero.display, f'leadB.with_text', f'{self._format_leader_bonus(leader=hero.leaderB, template_type='template')} {self.language.translate('Heroes')}')
  
  def _format_leader_bonus(self, leader: Leader, template_type: str) -> str:
    """ Format leader data into str """
    lead = ''   
    if leader.attack and leader.defense:
      lead = f'x{float(leader.attack):.2f} att {self.language.translate('and')} {float(leader.attack):.2f} def'
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
  
  def _prepare_talent_categories(self, hero: Hero):
    unique_talents = set(hero.talents.base) | set(hero.talents.merge) | {hero.talents.A1, hero.talents.A2, hero.talents.A3}
    talent_categories = ''
    for t in unique_talents:
      talent_categories += self.template_processor.transform_attribute_to_element(attribute=t, which_template='category.talent_template', language=self.language)
    setattr(hero.display, 'talent_categories', talent_categories)
  
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