from pymongo import MongoClient


class Mongo:
  def __init__(self, config, logger):
    """ MongoDB initialisation
      Args:
        config: config object loaded from config.py which contains mongoDB credentials
        logger: custom logger from logger.py
    """
    self.logger = logger
    self.config = config

  
  def connect(self):
    """ MongoDB connexion
      Returns: True if connected, False instead
    """
    self.logger.info('Attempting to connect to MongoDB...')
    try:
      self.client = MongoClient(self.config.MONGO_URI)
      self.db = self.client[self.config.MONGO_DB_NAME]
      self.logger.info(f'MongoDB connexion success')
      return True
    except Exception as e:
      self.logger.error(f'Error while connecting to MongoDB: {e}')
      return False


  def read(self, collection):
    """ Read a collection
      Args:
        collection (str): name of the collection
    """
    try:
      cursor = self.db.get_collection(collection).find()
      self.logger.info(f'read {collection} ok')
      return list(cursor)
    except Exception as e:
      self.logger.error(f'Mongo read error : {e}')
      return False
    

  def write(self, collection, data):
    """ Overwrite a collection
      Args:
        collection (str): name of the collection
        data (list[dict]): data to write
    """
    if not data:
      self.logger.error(f'no data to write in {collection}')
      return False
    self.db.get_collection(collection).delete_many({})
    result = self.insert(collection, data)
    if result.get('status'):
      result.get('return').replace('inserted', 'written')
    else:
      result.get('return').replace('insert', 'write')
    self.logger.info(f'write {collection} ok')
    return result
    
    
  def delete(self, collection, filter_dict=None):
    """ Delete documents from a collection
      Args:
        collection (str): name of the collection
        filter_dict (dict): Filter to know which documents to delete, if None delete all documents
    """
    try:
      if filter_dict is None:
        result = self.db.get_collection(collection).delete_many({})
      else:
        result = self.db.get_collection(collection).delete_many(filter_dict)
      self.logger.info(f'{result.deleted_count} document{'s' if result.deleted_count > 1 else ''} deleted')
      return True
    except Exception as e:
      self.logger.error(f'Mongo delete error : {e}')
      return False
  

  def insert(self, collection, data):
    """ Add data to collection (without deletion)
      Args:
        collection (str): name of the collection
        data (list[dict]): data to insert
    """
    try:
      if not data:
        self.logger.error(f'no data to insert in {collection}')
      if isinstance(data, list):
        result = self.db.get_collection(collection).insert_many(data)
        lines = len(result.inserted_ids)
      else:
        result = self.db.get_collection(collection).insert_one(data)
        lines = 1 if result.inserted_id else 0
      self.logger.info(f'{lines} document{'s' if lines > 1 else ''} inserted in {collection}')
      return True
    except Exception as e:
      self.logger.error(f'Mongo insert error : {e}')
      return False
  

  def update(self, collection, filter_dict, update_dict):
    """ Update data in collection
      Args:
        collection (str): name of the collection
        filter_dict (dict): Filter to know which documents to update
        data (list[dict]): data to update
    """
    try:
      if not update_dict:
        self.logger.error(f'no data to update in {collection}')
        return False
      result = self.db.get_collection(collection).update_many(filter_dict, {"$set": update_dict})
      self.logger.info(f'{result.modified_count} document{'s' if result.modified_count > 1 else ''} updated in {collection}')
      return True
    except Exception as e:
      self.logger.error(f'Mongo update error : {e}')
      return False
  
  
  def close(self):
    """ Close mongoDB connexion"""
    if self.client:
      self.client.close()
      self.logger.info('MongoDB connexion closed')
      return True
    self.logger.error('No MongoDB connexion to close')
    return False