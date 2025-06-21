import pygsheets
import os


def grab_sheets_data(config):
  gc = pygsheets.authorize(service_file=os.path.join('creds', config.GOOGLE_CREDS))

  sh = gc.open_by_key(key=config.PLAYSOME_KEY)
  playsome_data = sh.sheet1.get_all_values(include_tailing_empty_rows=False)
  header_row = playsome_data.pop(0)

  return playsome_data