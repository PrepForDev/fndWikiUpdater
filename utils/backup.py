import time
from datetime import datetime, timedelta
from filelock import FileLock
from typing import Optional, List

class DatabaseBackupManager:    
    def __init__(self, config, mongodb, logger):
      """ Initialize backup manager """
      self.config = config
      self.client = mongodb.client
      self.db = mongodb.db
      self.logger = logger
            
      self.backup_db_prefix = self.config.MONGO_DB_BACKUP
      self.max_backups = self.config.BACKUP_RETENTION
      self.max_retries = self.config.BACKUP_MAX_RETRIES
      self.retry_delay = self.config.BACKUP_RETRY_DELAY
      
      self.lock_file = "/tmp/backup_modification.lock"
      self.lock_timeout = 30
    

    def _get_backup_databases(self) -> List[str]:
      """ Get a list of existing backup databases """
      return [db for db in self.client.list_database_names() if self.backup_db_prefix in db]
    

    def _parse_backup_date(self, db_name: str) -> Optional[datetime]:
      """ Parse date from backup database's name
        Args:
          db_name: Backup database's name            
        Returns:
          datetime or None
      """
      try:
        if '_' in db_name:
          timestamp_str = db_name.split('_')[-1]
          return datetime.strptime(timestamp_str, '%d-%m-%y-%H-%M')
      except:
        return None
    

    def _cleanup_old_backups(self, backup_databases: List[str]) -> None:
      """ Check databases and delet older ones
        Args:
          backup_databases: list of backup database names
      """
      if len(backup_databases) <= self.max_backups:
        return
      valid_backups = []
      invalid_backups = []
      for db_name in backup_databases:
        backup_date = self._parse_backup_date(db_name)
        if backup_date:
          valid_backups.append((db_name, backup_date))
        else:
          invalid_backups.append(db_name)
      for db_name in invalid_backups:
        self._delete_backup_database(db_name, 'invalid')
      if len(valid_backups) > self.max_backups:
        valid_backups.sort(key=lambda x: x[1])  # sort by date
        backups_to_delete = len(valid_backups) - self.max_backups
        for i in range(backups_to_delete):
          db_name = valid_backups[i][0]
          self._delete_backup_database(db_name, 'expired')
    

    def _delete_backup_database(self, db_name: str, reason: str) -> None:
        """ Delete a backup database        
          Args:
            db_name: database's name to delete
            reason: reason why deleting
        """
        try:
          self.client.drop_database(db_name)
          self.logger.info(f'Backup {reason} ({db_name}) : deleting...')
        except Exception as e:
          self.logger.error(f'Error while deleting {db_name}: {e}')
    

    def _generate_backup_name(self) -> str:
        """ Generate unique backup database name """
        timestamp = datetime.now().strftime('%d-%m-%y-%H-%M')
        return f'{self.backup_db_prefix}_{timestamp}'
    

    def _copy_database(self, backup_db_name: str) -> bool:
      """ Copy source database to backup database        
        Args:
          backup_db_name: backup database name to create
        Returns:
          bool: True on success or False instead
      """
      try:
        backup_db = self.client[backup_db_name]
        collections = self.db.list_collection_names()
        count = len(collections)
        self.logger.info(f'Backup {count} collection{'s' if count > 1 else ''} to {backup_db_name}')
        for collection_name in collections:
          self.logger.info(f'  Saving collection: {collection_name}')
          backup_db.drop_collection(collection_name)
          source_collection = self.db[collection_name]
          backup_collection = backup_db[collection_name]
          documents = list(source_collection.find())
          if documents:
            backup_collection.insert_many(documents)
        return True
      except Exception as e:
        self.logger.error(f'Error while copying to {backup_db_name}: {e}')
        return False
  

    def _create_backup_attempt(self, backup_db_name: str) -> bool:
      """ Attempt to create backup with lock
        Args:
          backup_db_name: backup database name to create
        Returns:
          bool: True on success or False instead
      """
      lock = FileLock(self.lock_file, timeout=self.lock_timeout)
      try:
        with lock:
          backup_databases = self._get_backup_databases()
          self._cleanup_old_backups(backup_databases)
          return self._copy_database(backup_db_name)    
      except Exception as e:
        self.logger.error(f'Error while creating backup: {e}')
        return False
    

    def create_backup(self, operation_name: str='modification') -> bool:
      """ Create a backup with auto retry
        Args:
          operation_name: optional description of the operation to be done
        Returns:
          bool: True on success or False instead
      """
      backup_db_name = self._generate_backup_name()
      for attempt in range(self.max_retries):
        self.logger.info(
          f'Backup creation before {operation_name}'
          f'(attempt {attempt + 1}/{self.max_retries})'
        )
        if self._create_backup_attempt(backup_db_name):
          self.logger.info(f"✓ Backup successfully created : {backup_db_name}")
          return True
        elif attempt < self.max_retries - 1:
          self.logger.info(f'Next attempt in {self.retry_delay} seconds...')
          time.sleep(self.retry_delay)
      error_msg = f'Impossible to create backup after {self.max_retries} attempts'
      self.logger.error(error_msg)
      return False