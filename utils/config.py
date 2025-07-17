import os
from dotenv import load_dotenv

class Config:
  def __init__(self):
    load_dotenv()
    self.MONGO_URI = f'mongodb+srv://{os.getenv('MONGODB_USER')}:{os.getenv('MONGODB_PWD')}@{os.getenv('MONGODB_CLUSTER')}'
    self.MONGO_DB_NAME = os.getenv('MONGODB_DB')

    self.MONGO_DB_BACKUP = os.getenv('MONGODB_BACKUP_DB')
    self.BACKUP_RETENTION = int(os.getenv('BACKUP_RETENTION'))
    self.BACKUP_MAX_RETRIES = int(os.getenv('BACKUP_MAX_RETRIES'))
    self.BACKUP_RETRY_DELAY = int(os.getenv('BACKUP_RETRY_DELAY'))

    self.LOG_FILE = os.getenv('LOG_FILE')

    self.GOOGLE_CREDS = os.path.join('creds', os.getenv('GOOGLE_API_CREDS_JSON_FILE'))
    self.PLAYSOME_SHEET_KEY = os.getenv('PLAYSOME_SHEET_KEY')
    self.PLAYSOME_DRIVE_KEY = os.getenv('PLAYSOME_DRIVE_KEY')
    self.PET_SHEET_KEY = os.getenv('PET_SHEET_KEY')

    self.WIKI_URL = os.getenv('WIKI_URL')
    self.WIKI_USERNAME = os.getenv('WIKI_USERNAME')
    self.WIKI_PWD = os.getenv('WIKI_PWD')