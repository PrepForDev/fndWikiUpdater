def group_data_by_hero(data):
  if not data:
    return
  name_index = data[0].index('Name')
  groups = []
  current_group = []
  current_name = None

  for line in data[1:]:
    line_name = line[name_index]
    if current_name is None or line_name == current_name:
      current_group.append(line)
      current_name = line_name
    else:
      if current_group:
        groups.append(current_group)
      current_group = [line]
      current_name = line_name
  if current_group:
    groups.append(current_group)
  
  for group in groups:
    if len(group) < 5:
      group.append(['']*44)
  return groups