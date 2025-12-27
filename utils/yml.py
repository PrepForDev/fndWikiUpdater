import os
import yaml

class UnitySafeLoader(yaml.SafeLoader):
    pass

def unity_multi_constructor(loader, tag_prefix, node):
    return loader.construct_mapping(node)

UnitySafeLoader.add_multi_constructor('tag:unity3d.com,2011:', unity_multi_constructor)

class Yml:
  def __init__(self, logger):
    self.logger = logger

  def load(self, file=None, raw_data=None, data_dir=None):
    try:
      if raw_data:
        return yaml.load(raw_data, Loader=UnitySafeLoader)
      if data_dir:
        full_file_path = os.path.join(data_dir, file)
      else:
        full_file_path = file
      with open(full_file_path, 'r', encoding='utf-8') as f:
        return yaml.load(f, Loader=UnitySafeLoader)
    except FileNotFoundError as e:
      self.logger.error(f'File {file} not found in /{data_dir}')
      return False