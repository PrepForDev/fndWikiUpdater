from pymongo import MongoClient
from typing import List, Dict


class Mongo:
  def __init__(self, config, logger):
    """ MongoDB initialisation
      Args:
        config: config object loaded from config.py which contains mongoDB credentials
        logger: custom logger from logger.py
    """
    self.logger = logger
    self.config = config
    self.backup = None
  

  def set_backup_manager(self, backup_manager):
    """ Inject backup_manager after init to solve circular dependencies """
    self.backup = backup_manager
    self.logger.info('Backup manager initialisation success')


  def connect(self) -> bool:
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


  def read(self, collection: str) -> List[Dict]|bool:
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
    

  def write(self, collection: str, data: List[Dict]) -> bool:
    """ Overwrite a collection
      Args:
        collection (str): name of the collection
        data (List[Dict]): data to write
    """
    if not data:
      self.logger.error(f'no data to write in {collection}')
      return False
    try:
      self.db.get_collection(collection).delete_many({})
      result = self.db.get_collection(collection).insert_many(data)
      lines = len(result.inserted_ids)
      self.logger.info(f'{lines} document{'s' if lines > 1 else ''} written in {collection}')
      return True
    except Exception as e:
      self.logger.error(f'Mongo write error : {e}')
      return False
    
    
  def delete(self, collection: str, filter_dict: Dict=None) -> bool:
    """ Delete documents from a collection
      Args:
        collection (str): name of the collection
        filter_dict (Dict): Filter to know which documents to delete, if None delete all documents
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
  

  def insert(self, collection: str, data: List[Dict]|Dict) -> bool:
    """ Add data to collection (without deletion)
      Args:
        collection (str): name of the collection
        data (List[Dict]|Dict): data to insert
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
  

  def update(self, collection: str, filter_dict: Dict, update_dict: List[Dict]) -> bool:
    """ Update data in collection
      Args:
        collection (str): name of the collection
        filter_dict (Dict): Filter to know which documents to update
        data (List[Dict]): data to update
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
  
  
  def close(self) -> bool:
    """ Close mongoDB connexion"""
    if self.client:
      self.client.close()
      self.logger.info('MongoDB connexion closed')
      return True
    self.logger.error('No MongoDB connexion to close')
    return False
  
  
  def compare_data(self, old_data: List[Dict], new_data: List[Dict]) -> bool:
    """ Compares old_data (previously extracted from a collection) to new_data (freshly extracted from Playsome's sheet) 
      Returns : False on error or if old_data == new_data, True instead 
    """
    if not old_data or not new_data:
      self.logger.error('No data to compare')
      return False
    old_cleaned_data = [{k: v for k, v in doc.items() if k != '_id'} for doc in old_data]
    old_cleaned_data.sort(key=lambda x:x['name'])
    new_data.sort(key=lambda x:x['name'])
    return old_cleaned_data == new_data
  

  def backup_db(self) -> bool:
    """ Creates backup """
    if not self.backup.create_backup():
      return False
    return True