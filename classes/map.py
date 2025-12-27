from typing import Dict, List
from utils.map import MapRenderer

""" Empty Display class to be filled by display_attributes.py """
class Display():
  pass

class Map:
  def __init__(self, ctx):
    self.logger = ctx.logger
  
    self.name = None
    self.playsome_name = None
    self.width = None
    self.height = None
    self.has_water_or_lava = False
    self.always_same_start = False
    self.rooms = []
    self.images = []
    self.display = Display()
  
  def to_dict(self) -> Dict:
    return {
      'name': self.name,
      'playsome_name': self.playsome_name,
      'width': self.width,
      'height': self.height,
      'has_water_or_lava': self.has_water_or_lava,
      'always_same_start': self.always_same_start,
      'rooms': self.rooms
    }

  def create_map(self, data):
    raw_data = data['MonoBehaviour']
    raw_name = raw_data['m_Name'].split('Spire')[1]
    if raw_name[0] == '_':
      raw_name = raw_name[1:]
    self.playsome_name = f'Spire_{raw_name}'
    self.name = self.playsome_name.split('Spire')[1].replace('_',' ').strip()
    self.width = int(raw_data['width'])
    self.height = int(raw_data['height'])
    rooms = [room['layout'].split('\n') for room in raw_data['rooms']][:3]
    for room in rooms:
      r = []
      for line in room:
        l = []
        for char in line:
          match char:
            case '#': c = 'wall'
            case '^': c = 'rubble'
            case '~': 
              c = 'water'
              self.has_water_or_lava = True
            case ',': c = 'empty_tile'
            case '1'|'2'|'3'|'4'|'5'|'6': c = int(char)
            case _: c = 'tile'
          l.append(c)
        r.append(l)
      self.rooms.append(r)
      if all(room == rooms[0] for room in rooms[1:]):
        self.always_same_start = True
    return self
  
def create_all_maps(ctx, files: List[str]):
  """ Match .asset file list with extracted heroes objects """
  for file in files:
    map = Map(ctx)
    game_map = map.create_map(data=file)
    renderer = MapRenderer(logger=ctx.logger)
    renderer.render(game_map)
    ctx.maps.append(game_map)
  ctx.maps.sort(key=lambda m: (not m.always_same_start, m.height, m.has_water_or_lava, m.name))

def match_images_with_maps(ctx, images: List[str], attribute: str):
  """ Match image list with extracted maps objects """
  wiki_files = set(images)
  for map_obj in ctx.maps:
    for image_dict in map_obj.images:
      if attribute not in image_dict:
        image_dict[attribute] = False
      if image_dict['filename'] in wiki_files:
        image_dict[attribute] = True