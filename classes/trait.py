from typing import Dict, List


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


""" Trait class """
class Trait:
  def __init__(self, ctx):
    self.logger = ctx.logger
    self.elements_templates = ctx.elements_templates

    self.name = None
    self.special_art_id = None
    self.file = FileClass()
    self.formatted_name = None
    self.type = None
    self.sub_type = None
    self.description = None

  def to_dict(self) -> Dict:
    return {
      'name': self.name,
      'special_art_id': self.special_art_id,
      'formatted_name': self.formatted_name,
      'type': self.type,
      'sub_type': self.sub_type,
      'description': self.description
    }
  
  """ class method to transform sheets data into trait object """
  def create_trait(self, data, header):
    """ Create Trait object
      Args:
        data: line from sheets representing a trait
        header: Trait's sheet header row
      Returns:
        trait object (self)
    """
    self.name = data[header.index('Name')]
    self.special_art_id = data[header.index('Special_Art_ID')] if data[0][header.index('Special_Art_ID')] != '' else None
    self.formatted_name = data[header.index('Formatted')]
    self.type = data[header.index('type')]
    self.sub_type = data[header.index('sub_type')]
    self.description = data[header.index('description')]
    return self

def match_images_with_traits(ctx, images: List[Dict], attribute: str):
  """ Match image list with extracted traits objects """
  for image in images:
    cleaned_image_name = image.get('name').split('.png')[0][5:]
    print(f'name : {image.get('name')} | cleaned : {cleaned_image_name}')
    found_trait = next((trait for trait in ctx.traits if cleaned_image_name.lower() == trait.name.replace(' ','').lower()), None)
    if found_trait:
      setattr(found_trait.file, attribute, image)
      print(f' -> found for {found_trait.name}')
    else:
      found_trait = next((trait for trait in ctx.traits if cleaned_image_name.lower() == trait.special_art_id.lower()), None)
      if found_trait:
        setattr(found_trait.file, attribute, image)
        print(f' -> found for {found_trait.name}')