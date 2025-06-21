from utils.config import Config
from utils.mongodb import Mongo
from utils.sheets import grab_sheets_data

if __name__ == '__main__':
  config = Config()
  mongodb = Mongo(config)
  
  data = grab_sheets_data(config)
  for line in data:
    print(line)

  mongodb.close()