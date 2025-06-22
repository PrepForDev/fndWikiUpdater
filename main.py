import sys
from utils.config import Config
from utils.logger import Logger
from utils.mongodb import Mongo
from utils.sheets import Sheets

if __name__ == '__main__':
  config = Config()
  logger = Logger(log_file=config.LOG_FILE)
  mongodb = Mongo(config=config, logger=logger)
  connection_to_mongodb = mongodb.connect()
  if not connection_to_mongodb:
    sys.exit(1)
  sheets = Sheets(config=config, logger=logger)
  
  data = sheets.grab_sheets_data()
  mongodb.close()