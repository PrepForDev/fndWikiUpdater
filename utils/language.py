from typing import Dict


class Language:
  def __init__(self, logger):
    self.logger = logger
    self.code = None
    self.name = None
    self.translations = None

  def to_dict(self) -> Dict:
    return {
      'name': self.name,
      'code': self.code,
      'translations': self.translations
    }

  def load_language(self, data):
    if any([not data.get('Name'), not data.get('Code'), not data.get('Translations')]):
      self.logger.error('Language missing required data')
      return False
    self.code = data.get('Code')
    self.name = data.get('Name')
    self.translations = {}
    sections = ['Heroes', 'Classes', 'AI', 'Colors', 'Species', 'Talents', 'Gear', 'General', 'Pets']
    for section_name in sections:
      section_data = data['Translations'][section_name]
      for key, value in section_data.items():
        if key in self.translations:
          self.logger.warning(f'Key "{key}" already exists, overwriting from section {section_name}')
        self.translations[key] = value
    
    self.logger.info(f'Language {self.name} loaded')
    return self

  def translate(self, word: str) -> str:
    if self.translations.get(word) is not None:
      return self.translations[word]
    else:
      self.logger.warning(f'{word} translation cannot be found, please update language_{self.code}')
      return word