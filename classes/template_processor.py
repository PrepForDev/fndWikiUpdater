import re
from typing import Dict, List, Any

from classes.display_attributes import DisplayAttributes
from utils.language import Language


class TemplateProcessor:
  def __init__(self, logger, elements_templates, pages_templates, all_languages, all_pets, all_heroes):
    self.logger = logger
    self.elements_templates = elements_templates
    self.pages_templates = pages_templates
    self.all_languages = all_languages
    self.all_pets = all_pets
    self.all_heroes = all_heroes
  
  def process_all_templates(self, entities: List[Dict], language: Language) -> List[Dict]:
    """ Entry point to process all templates
      Args:
        entities: List[Dict] of type {'object': object_name.lower(), 'list': list of objects (Hero, Heroclass ...)}
        language: Language instance (for translation)
      Returns:
        List[Dict] with processed template -> {'title': 'XX', 'content': 'XX'}
    """
    results = []
    
    for entity_dict in entities:
      processed_entities = []
      for entity in entity_dict.get('list'):
        display = DisplayAttributes(logger=self.logger, elements_templates=self.elements_templates, language=language, all_languages=self.all_languages, all_heroes=self.all_heroes, all_pets=self.all_pets)
        display.init_template_processor(template_processor=self)
        processed_entities.append(display.prepare_display_data(entity=entity))

      for template_name, template_config in self.pages_templates.items():
        if template_config.get('base object') == entity_dict.get('object'):
          self.logger.info(f'Processing {template_name} template')
          processed = None
          template_type = template_config.get('type')
          
          if template_type == 'single':
            processed = self._process_single_templates(template_name, template_config, processed_entities, language)
            if processed:
              results.extend(processed)
          elif template_type == 'full list':
            processed = self._process_full_list_template(template_name, template_config, processed_entities, language)
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
        full_content = self._build_full_content(template_data.get('template_title'), template_config, processed_content, base_object, language)
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
      template_title = template_data.get('template_title')
      if '//' in template_title:
        template_title = self._replace_direct_values(content=template_title, base_object=base_object, language=language)
      full_content = self._build_full_content(template_data.get('template_title'), template_config, combined_content, base_object, language)
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
  
  def _build_full_content(self, template_title: str, template_config: Dict, main_content: str, base_object: Any, language: Language) -> str:
    """ Adds header and footer to page content """
    header = template_config.get('header', '')
    footer = template_config.get('footer', '')
    parts = []
    if header:
      processed_header = self._process_template_content(header, base_object, language)
      parts.append(processed_header)
    parts.append(main_content)
    if footer:
      processed_footer = self._process_template_content(footer, base_object, language)
      parts.append(processed_footer)
    for l in self.all_languages:
      if l != language:
        translated_title = self._replace_direct_values(content=template_title, base_object=base_object, language=l)
        parts.append(f'[[{l.code}:{translated_title}]]')
    return '\n'.join(parts)
  
  def _get_base_object(self, object, base_object_path: str):
      """ Get base object for template processing with multiple nestings handler """
      if '.' not in base_object_path:
        return object
      else:
        obj = object
        for attr in base_object_path.split('.'):
          obj = getattr(obj, attr, None)
          if obj is None:
            break
        return obj
      
  def transform_attribute_to_element(self, attribute: str, which_template: str, language: Language) -> str:
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
          
  
  """ class utils (private methods to get nested attributes in an object and get nested values in a dict) """

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