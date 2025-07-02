import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

class GoogleAPIConnector:
  def __init__(self, logger, config):
    self.logger = logger
    self.creds_file = config.GOOGLE_CREDS
    self.token_file = os.path.join('creds', 'google_token.json')
    self.scopes = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
    self.creds = None

  def connect(self):
    try:
      self.logger.info('Connecting to Google APIs...')
      if os.path.exists(self.token_file):
        self.creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
      if not self.creds or not self.creds.valid:
        if self.creds and self.creds.expired and self.creds.refresh_token:
          self.creds.refresh(Request())
          self.logger.info('-> Token refreshed')
        else:
          flow = InstalledAppFlow.from_client_secrets_file(self.creds_file, self.scopes)
          self.creds = flow.run_local_server(port=0)
          self.logger.info('-> Auth completed via browser')
        with open(self.token_file, 'w') as token:
          token.write(self.creds.to_json())
          self.logger.info('-> Credentials saved')
      return self.creds

    except Exception as e:
      self.logger.error(f'Google auth failed: {type(e).__name__} - {e}')
      return None