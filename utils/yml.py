import os
import yaml

class Yml:
  def __init__(self, logger):
    self.logger = logger

  def load(self, file, data_dir=None):
    try:
      if data_dir is not None:
        full_file_path = os.path.join(data_dir, f'{file}.yml')
      else:
        full_file_path = file
      with open(full_file_path, 'r', encoding='utf-8') as f:
        return yaml.load(f, Loader=yaml.SafeLoader)
    except FileNotFoundError as e:
      self.logger.error(f'File {file}.yml not found in /{data_dir}')
      return False