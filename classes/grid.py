import os
from PIL import Image, ImageDraw

class Grid:
  def __init__(self, ctx):
    self.logger = ctx.logger
    self.maps = ctx.maps
  
    self.filename = None
    self.image = None
    self.filepath = None
  
  def create_grid(self, data):
    self.filename = data.get('filename')
    self.image = data.get('image')
    self.filepath = data.get('filepath')
    print(f'filename: {self.filename}, filepath: {self.filepath}')
    return self
  
def create_all_grids(ctx, path):
  grid_images = compose_maps_grid(ctx.maps)
  for idx, grid_img in enumerate(grid_images):
    filename = f'Spire_maps_grid_{idx + 1}' if len(grid_images) > 1 else 'Spire_maps_grid'
    full_path = os.path.join(path, f'{filename}.png')
    grid_img.save(full_path)
    grid = Grid(ctx)
    grid.create_grid({'filename': filename, 'image': grid_img, 'filepath': full_path})
    ctx.grids.append(grid)
    ctx.logger.debug(f'Grid {idx + 1}/{len(grid_images)} saved as {full_path}')

def compose_maps_grid(maps, max_columns = 3, max_rows = 8, scale_factor=0.5, line_spacing = 20, line_width = 20, bg_color=(0,0,0,255), separator_color = (200, 200, 40, 255)):
  if not maps:
    return None
  
  water_images = [get_water_image(m) for m in maps if get_water_image(m) is not None]
  if not water_images:
    return None
  
  original_max_width = max(img.width for img in water_images)
  original_max_height = max(img.height for img in water_images)
  max_width = int(original_max_width * scale_factor)
  max_height = int(original_max_height * scale_factor)
  separator_width = 2 * line_spacing + line_width
  maps_per_grid = max_columns * max_rows
  grid_images = []

  for grid_idx in range(0, len(maps), maps_per_grid):
    maps_chunk = maps[grid_idx:grid_idx + maps_per_grid]
    columns = min(len(maps_chunk), max_columns)
    rows = (len(maps_chunk) + columns - 1) // columns
    total_width = columns * max_width + (columns - 1) * separator_width
    total_height = rows * max_height + (rows - 1) * separator_width
    grid_img = Image.new('RGBA', (total_width, total_height), bg_color)
    draw = ImageDraw.Draw(grid_img)

    for idx, m in enumerate(maps_chunk):
      col = idx % columns
      row = idx // columns
      cell_x = col * (max_width + separator_width)
      cell_y = row * (max_height + separator_width)
      map_img = get_water_image(m)
      img_w, img_h = map_img.size
      new_w = int(img_w * scale_factor)
      new_h = int(img_h * scale_factor)
      resized_img = map_img.resize((new_w, new_h), Image.LANCZOS)
      x = cell_x + (max_width - new_w) // 2
      y = cell_y + (max_height - new_h) // 2
      grid_img.paste(resized_img, (x, y))
    
    for col in range(columns - 1):
      x_line = col * (max_width + separator_width) + max_width + line_spacing + line_width // 2
      draw.line([(x_line, 0), (x_line, total_height)], fill=separator_color, width=line_width)
    for row in range(rows - 1):
      y_line = row * (max_height + separator_width) + max_height + line_spacing + line_width // 2
      draw.line([(0, y_line), (total_width, y_line)], fill=separator_color, width=line_width)
      
    grid_images.append(grid_img)
  return grid_images

def get_water_image(map_obj):
  if not map_obj.images:
    return None
  for img_data in map_obj.images:
    if img_data['variant'] == 'water':
      return img_data['image']
  return map_obj.images[0]['image']