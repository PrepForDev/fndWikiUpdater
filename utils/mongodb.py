from pymongo import MongoClient


class Mongo:
  def __init__(self, config):
    """ MongoDB initialisation
      Args:
        config: config object loaded from config.py which contains mongoDB credentials
    """
    self.client = MongoClient(config.MONGO_URI)
    self.db = self.client[config.MONGO_DB_NAME]
    print(f'connected at {config.MONGO_URI}')


  def read(self, collection):
    """ Read a collection
      Args:
        collection (str): name of the collection
    """
    try:
      cursor = self.db.get_collection(collection).find()
      return {'status': True, 'return': list(cursor)}
    except Exception as e:
      return {'status': False, 'return': f'Mongo read error : {e}'}
    

  def write(self, collection, data):
    """ Overwrite a collection
      Args:
        collection (str): name of the collection
        data (list[dict]): data to write
    """
    if not data:
      return {'status': False, 'return': f'no data to write in {collection}'}
    self.db.get_collection(collection).delete_many({})
    result = self.insert(collection, data)
    if result.get('status'):
      result.get('return').replace('inserted', 'written')
    else:
      result.get('return').replace('insert', 'write')
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
      return {'status': True, 'return': f'{result.deleted_count} document{'s' if result.deleted_count > 1 else ''} deleted'}
    except Exception as e:
      return {'status': False, 'return': f'Mongo delete error : {e}'}
  

  def insert(self, collection, data):
    """ Add data to collection (without deletion)
      Args:
        collection (str): name of the collection
        data (list[dict]): data to insert
    """
    try:
      if not data:
        return {'status': False, 'return': f'no data to insert in {collection}'}
      if isinstance(data, list):
        result = self.db.get_collection(collection).insert_many(data)
        lines = len(result.inserted_ids)
      else:
        result = self.db.get_collection(collection).insert_one(data)
        lines = 1 if result.inserted_id else 0
      return {'status': True, 'return': f'{lines} document{'s' if lines > 1 else ''} inserted in {collection}'}
    except Exception as e:
      return {'status': False, 'return': f'Mongo insert error : {e}'}
  

  def update(self, collection, filter_dict, update_dict):
      """ Update data in collection
        Args:
          collection (str): name of the collection
          filter_dict (dict): Filter to know which documents to update
          data (list[dict]): data to update
      """
      try:
        if not update_dict:
          return {'status': False, 'return': f'no data to update in {collection}'}
        result = self.db.get_collection(collection).update_many(filter_dict, {"$set": update_dict})
        return {'status': True, 'return': f'{result.modified_count} document{'s' if result.modified_count > 1 else ''} updated in {collection}'}
      except Exception as e:
        return {'status': False, 'return': f'Mongo update error : {e}'}
  
  
  def close(self):
      """ Close mongoDB connexion"""
      if self.client:
        self.client.close()
        print('MongoDB connexion closed')