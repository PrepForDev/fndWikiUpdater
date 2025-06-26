import re
from typing import Dict, List, Any
from math import ceil

from classes.hero import Hero, Leader
from utils.language import Language

class DynamicObject:
  """ Empty class to create objects with dynamic attributes """
  pass


class TemplateProcessor:
  def __init__(self, logger, elements_templates, pages_templates):
    self.logger = logger
    self.elements_templates = elements_templates
    self.pages_templates = pages_templates
  
  def process_all_templates(self, entities: List[Any], language: Language) -> List[Dict]:
    """ Entry point to process all templates
      Args:
        entities: List of objects with print attribute (Hero, etc.)
        language: Language instance (for translation)
      Returns:
        List[Dict] with processed template -> {'title': 'XX', 'content': 'XX'}
    """
    results = []
    processed_entities = []
    for entity in entities:
      processed_entities.append(self._prepare_print_data(entity=entity, language=language))
    for template_name, template_config in self.pages_templates.items():
      self.logger.info(f'Processing {template_name} template')
      processed = None
      template_type = template_config.get('type')
      if template_type == 'single':
        processed = self._process_single_templates(template_name, template_config, entities, language)
        if processed:
          results.extend(processed)
      elif template_type == 'full list':
        processed = self._process_full_list_template(template_name, template_config, entities, language)
        if processed:
          results.append(processed)
      else:
        self.logger.error(f'type missing in {template_name}, please check pages_templates.yml and run again')
    return results
  

  """ class private methods for template processing """

  def _process_single_templates(self, template_name: str, template_config: Dict, entities: List[Any], language: Language) -> List[Dict[str, str]]:
    """ Process template for all heroes one by one -> returns one page by hero """
    results = []
    template_data = self._check_template_data(template_name=template_name, template_config=template_config, language=language)
    if template_data:
      for entity in entities:
        base_object = self._get_base_object(entity, template_data.get('base_object_path'))
        processed_content = self._process_template_content(template_data.get('template_content'), base_object, language)
        template_title = template_data.get('template_title')
        if '//' in template_title:
          template_title = self._replace_direct_values(content=template_title, base_object=base_object, language=language)
        full_content = self._build_full_content(template_config, processed_content)
        results.append({'title': template_title, 'content': full_content})
      return results
    return None
  
  def _process_full_list_template(self, template_name: str, template_config: Dict, entities: List[Any], language: Language) -> Dict[str, str]:
    """ Process template for all heroes all at once -> return an unique page for all heroes """
    template_data = self._check_template_data(template_name=template_name, template_config=template_config, language=language)
    if template_data:
      all_rows = []
      for entity in entities:
        base_object = self._get_base_object(entity, template_data.get('base_object_path'))
        processed_row = self._process_template_content(template_data.get('template_content'), base_object, language)
        all_rows.append(processed_row)
      combined_content = '\n'.join(all_rows)
      full_content = self._build_full_content(template_config, combined_content)
      template_title = template_data.get('template_title')
      if '//' in template_title:
        template_title = self._replace_direct_values(content=template_title, base_object=base_object, language=language)
      return {'title': template_title, 'content': full_content}
    
  def _check_template_data(self, template_name: str, template_config: Dict, language: Language) -> Dict|None:
    """ Checks for template integrity (mandatory elements) """
    base_object_path = template_config.get('base object', 'hero')
    if not base_object_path:
      self.logger.error(f'base object missing in {template_name}, please check pages_templates.yml and run again')
      return None
    template_content = template_config.get('template')
    if not template_content:
      self.logger.error(f'template missing in {template_name}, please check pages_templates.yml and run again')
      return None
    template_title = template_config.get('title')
    if not template_title:
      self.logger.error(f'title missing in {template_name}, please check pages_templates.yml and run again')
      return None
    return {'base_object_path': base_object_path, 'template_content': template_content, 'template_title': template_title}
  
  def _build_full_content(self, template_config: Dict, main_content: str) -> str:
    """ Adds header and footer to page content """
    header = template_config.get('header', '')
    footer = template_config.get('footer', '')
    parts = []
    if header:
      parts.append(header)
    parts.append(main_content)
    if footer:
      parts.append(footer)
    return '\n'.join(parts)
  
  def _get_base_object(self, object, base_object_path: str):
      """ Get base object for template processing with multiple nestings handler """
      if base_object_path == 'hero':
        return object
      else:
        obj = object
        for attr in base_object_path.split('.'):
          obj = getattr(obj, attr, None)
          if obj is None:
            break
        return obj
      
  def _transform_attribute_to_element(self, attribute: str, which_template: str, language: Language) -> str:
    """ Transforms an attribute into the template which_template, taken from elements_templates.yml
    Args: 
      attribute: value to integrate in template
      which_template: key_path find in elements_templates.yml, splitted with dots
      language: the language to translate into
    Returns:
      template str filled with attribute and translated attribute if needed
      """
    template = self._getitem_nested(data=self.elements_templates, key_path=which_template).replace('\n', '').replace('<br />', '').replace('<br>', '').strip()
    if not template:
      self.logger.error(f'No template {which_template} found in elements_templates.yml')
      return ''
    return self._process_template_content(template=template, base_object=attribute, language=language)
  
  def _process_template_content(self, template: str, base_object: Any, language: Language) -> str:
    """ Process template content by replacing tags with elements or values """
    processed = template
    processed = self._replace_element_templates(processed, base_object, language)
    processed = self._replace_direct_values(processed, base_object, language)
    return processed
  
  def _replace_element_templates(self, content: str, base_object: Any, language: Language) -> str:
    """ Replace **template_name** patterns with elements_templates """
    pattern = r'\*\*([^*]+)\*\*'
    
    def replace_element_template(match):
      template_path = match.group(1)
      parts = template_path.split('.')
      if len(parts) != 2:
        self.logger.error(f'template error: too much nesting in {template_path}')
        return match.group(0)
      element_name, template_type = parts
      if element_name not in self.elements_templates:
        self.logger.error(f'template error: {element_name} not in elements_templates.yml')
        return match.group(0)
      element_config = self.elements_templates[element_name]
      element_template = element_config.get(template_type, '')
      if not element_template:
        self.logger.error(f'template error: no {element_template} in {element_name} template')
        return match.group(0)
      return self._process_template_content(element_template, base_object, language)
    
    return re.sub(pattern, replace_element_template, content)
  
  def _replace_direct_values(self, content: str, base_object: Any, language: Language) -> str:
    """ Replace //attribute// patterns with values """
    pattern = r'//([^/]+)//'
    
    def replace_value(match):
      attribute_path = match.group(1)
      try:
        if attribute_path.startswith('translated.'):
          attr_name = attribute_path.replace('translated.', '')
          if (attr_name.startswith("'") and attr_name.endswith("'")) or (attr_name.startswith('"') and attr_name.endswith('"')):
            return language.translate(attr_name[1:-1])
          else:
            if hasattr(base_object, '__dict__'):
              value = self._getattr_nested(base_object, attr_name)
            else:
              value = base_object
            if value:
              return language.translate(value)
            self.logger.error(f'attribute error: no {attribute_path} found')
            return match.group(0)
        else:
          if hasattr(base_object, '__dict__'):
            value = self._getattr_nested(base_object, attribute_path)
          else:
            value = base_object
          if value is not None:
            return str(value)
          self.logger.error(f'attribute error: no {attribute_path} found')
          return match.group(0)
      except Exception:
        self.logger.error(f'attribute error: no {attribute_path} found')
        return match.group(0)
    
    return re.sub(pattern, replace_value, content)
  

  """ class private methods to create hero's missing attributes in Playsome's sheet """

  def _prepare_print_data(self, entity, language: Language):
    """ Entry point for custom attributes calculation (in prevision for pets and/or traits) """
    if isinstance(entity, Hero):
      entity = self._prepare_hero_print_data(hero=entity, language=language)
    return entity
        
  def _prepare_hero_print_data(self, hero: Hero, language: Language):
    """ Prepare hero custom data with formatted values """
    self.logger.debug(f'Calculate custom data for {hero.name}')
    self._prepare_hero_attack_pattern_and_type(hero)
    self._prepare_image(hero)
    self._prepare_hero_stats(hero)
    self._prepare_hero_talents(hero, language)
    self._prepare_hero_gear(hero, language)
    self._prepare_stars(hero)
    self._prepare_hero_leader_data(hero, language)
    return hero

  def _prepare_hero_attack_pattern_and_type(self, hero: Hero):
    """ Prepare hero attack pattern and attack type """
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

  def _prepare_image(self, object: Any):
    """ Prepare image filename """
    image_name = f'{object.name.replace(' \'', '_\'')}_Portrait.png'
    self._setattr_nested(object.display, 'image', image_name)
  
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
    
    self._setattr_nested(hero.display, 'attack.max.base', max([int(hero.attack.A0), int(hero.attack.A1), int(hero.attack.A2), int(hero.attack.A3)]))
    self._setattr_nested(hero.display, 'attack.max.gear', max([int(hero.display.attack.A0.gear), int(hero.display.attack.A1.gear), int(hero.display.attack.A2.gear), int(hero.display.attack.A3.gear)]))
    self._setattr_nested(hero.display, 'attack.max.merge', max([int(hero.display.attack.A0.merge), int(hero.display.attack.A1.merge), int(hero.display.attack.A2.merge), int(hero.display.attack.A3.merge)]))
    self._setattr_nested(hero.display, 'attack.max.total', int(hero.display.attack.max.base) + int(hero.display.attack.max.gear) + int(hero.display.attack.max.merge))

    self._setattr_nested(hero.display, 'health.max.base', max([int(hero.health.A0), int(hero.health.A1), int(hero.health.A2), int(hero.health.A3)]))
    self._setattr_nested(hero.display, 'health.max.gear', max([int(hero.display.health.A0.gear), int(hero.display.health.A1.gear), int(hero.display.health.A2.gear), int(hero.display.health.A3.gear)]))
    self._setattr_nested(hero.display, 'health.max.merge', max([int(hero.display.health.A0.merge), int(hero.display.health.A1.merge), int(hero.display.health.A2.merge), int(hero.display.health.A3.merge)]))
    self._setattr_nested(hero.display, 'health.max.total', int(hero.display.health.max.base) + int(hero.display.health.max.gear) + int(hero.display.health.max.merge))

    self._setattr_nested(hero.display, 'max_level', max([int(hero.levelmax.A0), int(hero.levelmax.A1) ,int(hero.levelmax.A2) ,int(hero.levelmax.A3)]))
  
  def _prepare_hero_talents(self, hero: Hero, language: Language):
    """ Prepare formatted talents """
    traits_to_process = [{'attr': 'base', 'traits': [self._transform_attribute_to_element(attribute=t, which_template= 'trait.translated_template', language=language) for t in hero.talents.base]}]
    traits_to_process.append({'attr': 'A1', 'traits': self._transform_attribute_to_element(attribute=hero.talents.A1, which_template= 'trait.translated_template', language=language)})
    traits_to_process.append({'attr': 'A2', 'traits': self._transform_attribute_to_element(attribute=hero.talents.A2, which_template= 'trait.translated_template', language=language)})
    traits_to_process.append({'attr': 'A3', 'traits': self._transform_attribute_to_element(attribute=hero.talents.A3, which_template= 'trait.translated_template', language=language)})
    ascend_talents = [hero.talents.A1, hero.talents.A2, hero.talents.A3]
    traits_to_process.append({'attr': 'ascend', 'traits': [self._transform_attribute_to_element(attribute=t, which_template= 'trait.translated_template', language=language) for t in ascend_talents]})
    traits_to_process.append({'attr': 'merge', 'traits': [self._transform_attribute_to_element(attribute=t, which_template= 'trait.translated_template', language=language) for t in hero.talents.merge]})
    for traits in traits_to_process:
      if isinstance(traits.get('traits'), list):
        if len(traits.get('traits')) > 0:
          self._setattr_nested(hero.display, f'talents.{traits.get('attr')}.raw_list', '<br />'.join([''] + traits.get('traits')))
          self._setattr_nested(hero.display, f'talents.{traits.get('attr')}.bullet_list', '<br />&nbsp;&nbsp;'.join([''] + traits.get('traits')))
        else:
          self._setattr_nested(hero.display, f'talents.{traits.get('attr')}.raw_list', '')
          self._setattr_nested(hero.display, f'talents.{traits.get('attr')}.bullet_list', '')
      else:
        self._setattr_nested(hero.display, f'talents.{traits.get('attr')}.raw_list', traits.get('traits'))
  
  def _prepare_hero_gear(self, hero: Hero, language: Language):   
    """ Prepare formatted gear """
    for ascend in ['A0', 'A1', 'A2', 'A3']:
      translated_gear = [language.translate(g) for g in getattr(hero.gear, ascend) if g != '']
      self._setattr_nested(hero.display, f'gear.{ascend}.raw_list', '<br />'.join([''] + translated_gear))
      self._setattr_nested(hero.display, f'gear.{ascend}.bullet_list', '<br />&nbsp;&nbsp;'.join([''] + translated_gear))
  
  def _prepare_stars(self, hero: Hero):
    """ Prepare stars """
    self._setattr_nested(hero.display, 'stars', '&#11088; ' * int(hero.stars))
  
  def _prepare_hero_leader_data(self, hero, language: Language):
    """ Prepare formatted leader data """
    self._setattr_nested(hero.display, f'leadA.no_text', self._format_leader_bonus(leader=hero.leaderA, template_type='no_text_template', language=language))
    self._setattr_nested(hero.display, f'leadB.no_text', self._format_leader_bonus(leader=hero.leaderB, template_type='no_text_template', language=language))
    self._setattr_nested(hero.display, f'leadA.with_text', self._format_leader_bonus(leader=hero.leaderA, template_type='template', language=language))
    self._setattr_nested(hero.display, f'leadB.with_text', self._format_leader_bonus(leader=hero.leaderB, template_type='template', language=language))
  
  def _format_leader_bonus(self, leader: Leader, template_type: str, language: Language) -> str:
    """ Format leader data into str """
    lead = ''   
    if leader.attack and leader.defense:
      lead = f'x{float(leader.attack):.2f} att and {float(leader.attack):.2f} def'
    elif leader.attack:
      lead = f'x{float(leader.attack):.2f} att'
    elif leader.defense:
      lead = f'x{float(leader.defense):.2f} def'
    elif leader.talent:
      lead = self._transform_attribute_to_element(attribute=leader.talent, which_template=f'trait.{template_type}', language=language)
    if lead != '':
      lead += ' for '
      if leader.color:
        lead += self._transform_attribute_to_element(attribute=leader.color, which_template=f'color.{template_type}', language=language)
      if leader.species:
        lead += self._transform_attribute_to_element(attribute=leader.species, which_template=f'species.{template_type}', language=language)
      if leader.extra:
        lead += f' or {self._transform_attribute_to_element(attribute=leader.extra, which_template=f'trait.{template_type}', language=language)}'
    return lead
   

  """ class utils (private methods to get/set nested attributes in an object and get nested values in a dict) """

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
        setattr(obj, attr, DynamicObject())
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
    
  def _getitem_nested(self, data: dict, key_path: str) -> Any:
    """Get the value of a nested key with multiple nestings handler
      Args:
        data: dictionary with initial data (ex: self.elements_templates)
        key_path: str with keys to get separated by dots (ex: 'trait.template')
      Returns:
        value from the nested dictionary (ex: self.elements_templates['trait']['template'])
    """
    try:
      current = data
      for key in key_path.split('.'):
        if isinstance(current, dict) and key in current:
          current = current[key]
        else:
          return None
      return current
    except (KeyError, TypeError, AttributeError):
        return None