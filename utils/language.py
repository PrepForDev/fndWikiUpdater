class Language:
  def __init__(self, logger):
    self.logger = logger
    
    self.code = None
    self.name = None
    self.translations = None

  def load_language(self, data):
    if any([not data.get('Name'), not data.get('Code'), not data.get('Translations')]):
      self.logger.error('Language missing required data')
      return False
    self.code = data.get('Code')
    self.name = data.get('Name')
    self.translations = {}
    for d in (data['Translations']['Heroes'], data['Translations']['Classes'], data['Translations']['AI'], data['Translations']['Colors'], data['Translations']['Species'], data['Translations']['Talents'], data['Translations']['Gear'], data['Translations']['General']):
      self.translations.update(d)
    self.logger.info(f'Language {self.name} loaded')
    return self

  def translate(self, word: str) -> str:
    if self.translations.get(word) is not None:
      return self.translations[word]
    else:
      self.logger.warning(f'{word} translation cannot be found, please update language_{self.code}')
      return word