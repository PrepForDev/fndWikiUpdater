import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

class MapRenderer: 
  def __init__(self, logger, temp_path='temp', tiles_path='data/tiles'):
    self.logger = logger
    self.temp_path = temp_path
    self.tiles_path = tiles_path

    self.tile_size = 150
    self.stage_spacing = 30
    self.font_color = (200, 200, 40, 255)
    self.font_outline_color = (0, 0, 0, 255)
    self.header_height = self.tile_size * 2
    
    self.tiles = self._load_tiles()
    self.font = self._load_font()
    self.map_tiles = []
    self.stages_count = 0
    self.image = None

  def render(self, game_map):
    game_map.images = []
    self._render_and_export(game_map, 'water', show_variant=False)
    if game_map.has_water_or_lava:
      for variant in ['water', 'lava']:
        self._render_and_export(game_map, variant, show_variant=True)
    return game_map.images

  def _render_and_export(self, game_map, variant, show_variant=False):
    rooms = self._merge_rooms_if_needed(game_map.rooms)
    self.stages_count = len(rooms)
    self._transform(game_map, rooms, variant)
    self._create_canvas(game_map, rooms, variant, show_variant)
    self._draw_all_stages()
    filename = f'{game_map.playsome_name}_with_{variant}' if show_variant else f'{game_map.playsome_name}'
    filepath = os.path.join(self.temp_path, f'{filename}.png')
    self.image.save(filepath)
    game_map.images.append({'variant': variant, 'image': self.image.copy(), 'filename': filename, 'filepath': filepath})
    self.logger.debug(f'Map variant exported to {filepath}' if show_variant else f'Map exported to {filepath}')

  def _merge_rooms_if_needed(self, rooms):
    if len(rooms) >= 2 and all(room == rooms[0] for room in rooms[1:]):
      return [rooms[0]]
    return rooms

  def _transform(self, game_map, rooms, variant='water'):
    width = game_map.width
    height = game_map.height
    self.map_tiles = []

    for room in rooms:
      stage_grid = []
      for y in range(height):
        row = []
        for x in range(width):
          cell = room[y][x]
          number = None
          base_type = None
          color = None
          if isinstance(cell, int):
            base_type = 'tile'
            number = cell
          elif cell == 'water':
            base_type = variant
          elif cell == 'tile':
            base_type = 'tile'
            if not self._has_adjacent_number(room, x, y, width, height):
              color = 'red'
          elif cell == 'empty_tile':
            base_type = 'tile'
          else:
            base_type = cell
          row.append({'type': base_type, 'color': color, 'number': number, 'x': x, 'y': y})
        stage_grid.append(row)
      self.map_tiles.append(stage_grid)

  def _has_adjacent_number(self, room, x, y, w, h):
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
      nx, ny = x + dx, y + dy
      if 0 <= nx < w and 0 <= ny < h:
        if isinstance(room[ny][nx], int):
          return True
    return False

  def _create_canvas(self, game_map, rooms, variant='water', show_variant=False):
    stage_width = game_map.width * self.tile_size
    stage_height = game_map.height * self.tile_size

    total_width = self.stages_count * stage_width  + (self.stages_count - 1) * self.stage_spacing
    total_height = stage_height + self.header_height

    self.image = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 255))
    self._draw_headers(game_map, rooms, variant)

  def _draw_headers(self, game_map, rooms, variant='water', show_variant=False):
    draw = ImageDraw.Draw(self.image)
    title = f'{game_map.name} ({variant.capitalize()})' if show_variant else game_map.name
    self._draw_centered_text(draw, title, 0, 0, self.image.width, self.tile_size, underline=True)

    header_y = self.tile_size
    if len(rooms) == 1 and len(game_map.rooms) == 3:
      text = 'Stages 1, 2, 3'
      self._draw_centered_text(draw, text, 0, header_y, self.image.width, self.tile_size)
    else:
      for i in range(self.stages_count):
        text = f'Stage {i + 1}'
        x = i * (game_map.width * self.tile_size + self.stage_spacing)
        self._draw_centered_text(draw, text, x, header_y, game_map.width * self.tile_size, self.tile_size)

  def _draw_all_stages(self):
    if self.stages_count == 1:
      center_stage = self.stages_count // 2
      self._draw_stage(0, target_stage=center_stage)
    else:
      for stage in range(self.stages_count):
        self._draw_stage(stage, target_stage=stage)

  def _draw_stage(self, stage, target_stage):
    grid = self.map_tiles[stage]
    offset_x = target_stage * (len(grid[0]) * self.tile_size + self.stage_spacing)
    offset_y = self.header_height

    for row in grid:
      for cell in row:
        self._draw_tile(cell, offset_x, offset_y)

  def _draw_tile(self, cell, ox, oy):
    x = cell['x']
    y = cell['y']
    tile_type = cell['type']
    if tile_type == 'tile':
      tile_type = 'light' if (x + y) % 2 == 0 else 'dark'
    tile = self.tiles[tile_type].resize((self.tile_size, self.tile_size))
    if cell['color'] == 'red':
      tile = self._color_tile(tile)
      tile = self._apply_red_overlay(tile)
    if cell['number'] is not None:
      tile = self._draw_number(tile, str(cell['number']))
    self.image.paste(tile, (ox + x * self.tile_size, oy + y * self.tile_size))
  
  def _apply_red_overlay(self, tile, alpha=60):
    overlay = Image.new('RGBA', tile.size, (180, 40, 40, alpha))
    return Image.alpha_composite(tile, overlay)

  def _draw_number(self, tile, text):
    tile_width, tile_height = tile.size
    draw_layer = Image.new('RGBA', tile.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(draw_layer)

    left, top, right, bottom = draw.textbbox((0, 0), text, font=self.font)
    text_width = right - left
    text_height = bottom - top

    position = ((tile_width - text_width) // 2 - left, (tile_height - text_height) // 2 - top)
    for offset_x, offset_y in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
      draw.text((position[0] + offset_x, position[1] + offset_y), text, fill=self.font_outline_color, font=self.font)
    draw.text(position, text, fill=self.font_color, font=self.font)
    return Image.alpha_composite(tile, draw_layer)
  
  def _draw_centered_text(self, draw, text, x, y, w, h, underline=False, underline_offset=24, underline_padding=10, underline_width=6):
    ascent, descent = self.font.getmetrics()
    left, top, right, bottom = draw.textbbox((0, 0), text, font=self.font)
    text_width = right - left
    text_height = bottom - top
    text_x = x + (w - text_width) // 2
    text_y = y + (h - text_height) // 2 - top
    draw.text((text_x, text_y), text, font=self.font, fill=self.font_color)

    if underline:
      baseline_y = text_y + ascent
      underline_y = baseline_y + underline_offset
      draw.line((text_x - underline_padding, underline_y, text_x + text_width + underline_padding, underline_y), fill=self.font_color, width=underline_width)

  def _color_tile(self, tile):
    r, g, b, a = tile.split()
    r = ImageEnhance.Brightness(r).enhance(1.5)
    g = ImageEnhance.Brightness(g).enhance(0.8)
    b = ImageEnhance.Brightness(b).enhance(0.8)
    return Image.merge('RGBA', (r, g, b, a))

  def _load_tiles(self):
    tiles = {}
    for f in os.listdir(self.tiles_path):
      if f.endswith('.png'):
        key = f.replace('.png', '')
        tiles[key] = Image.open(os.path.join(self.tiles_path, f)).convert('RGBA')
    return tiles

  def _load_font(self):
    try:
      return ImageFont.truetype('Arial.ttf', size=self.tile_size // 2)
    except IOError:
      try:
        return ImageFont.truetype('DejaVuSans.ttf', size=self.tile_size // 2)
      except IOError:
        return ImageFont.load_default()