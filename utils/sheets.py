import pygsheets
import os


class Sheets:
  def __init__(self, config, logger):
    self.config = config
    self.logger = logger
    self.gc = None


  def _connect_to_sheets(self):
    """ Read credentials JSON file and connect to Google Sheets """
    try:
      self.logger.info('Attempting to connect to Google Sheets API...')
      creds_file = os.path.join('creds', self.config.GOOGLE_CREDS)
      self.gc = pygsheets.authorize(service_file=creds_file)
      if not self.gc:
        self.logger.error(f'Google Sheets authorization failed')
        return False
      self.logger.info('Google Sheets connexion success')
      return True
    except FileNotFoundError as e:
      self.logger.error(f'Credentials JSON not found in {creds_file} - {e}')
      return False
    except pygsheets.exceptions.NoValidCredentialsError as e:
        self.logger.error(f'Invalid credentials file: {e}')
        return False
    except Exception as e:
      self.logger.error(f'Unexpected error while connecting to Google Sheets: {type(e).__name__} - {e}')
      return False


  def _read_sheet_data(self, sheet_key):
    """ Read data from Google Sheets file
      Args: 
        sheet_key (str) : Google Sheets file key
      Returns: 
        list: Google Sheets data or False on error
    """
    if not self.gc:
      self.logger.error('Not connected to Google Sheets')
      return False
    try:
      self.logger.info(f'Opening sheet with key: {sheet_key}')
      sh = self.gc.open_by_key(key=sheet_key)
      self.logger.info('Reading file...')
      sheet_data = sh.sheet1.get_all_values(include_tailing_empty_rows=False)
      if not sheet_data:
        self.logger.error('No data in this sheet')
        return False
      self.logger.info('Read sheets ok')
      return sheet_data
    except pygsheets.exceptions.SpreadsheetNotFound as e:
      self.logger.error(f'No Google Sheets file found with key {sheet_key}: {e}')
      return False
    except pygsheets.exceptions.WorksheetNotFound as e:
      self.logger.error(f'No sheet1 found in file {sheet_key}: {e}')
      return False
    except Exception as e:
      self.logger.error(f'Unexpected error while reading sheet {sheet_key}: {type(e).__name__} - {e}')
      return False
    

  def grab_sheets_data(self):
    """ Connect to Google Sheets and return data """
    connect = self._connect_to_sheets()
    if connect:
      playsome_data = self._read_sheet_data(self.config.PLAYSOME_KEY)
      if playsome_data:
        header_row = playsome_data.pop(0)
        return playsome_data
    return False