import io
import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

from utils.google import GoogleAPIConnector

from typing import List, Dict

class Drive:
    def __init__(self, logger, config):
      self.logger = logger
      self.config = config
      self.drive = None
    
    def _connect_to_drive(self) -> bool:
      """ Connect to Google Drive """
      connector = GoogleAPIConnector(logger=self.logger, config=self.config)
      creds = connector.connect()

      if creds:
        try:
          self.service = build('drive', 'v3', credentials=creds)
          self.logger.info('Google Drive ready')
          return True
        except Exception as e:
          self.logger.error(f'API build failed: {e}')
      else:
          self.logger.error('Google Drive init failed')
      return False
     
    def _get_files_in_folder(self, folder_id: str, mime_type: str, folder_name=None) -> List[Dict]:
      """ Get all images in a drive folder        
        Args:
          folder_id (str)
          folder_name (str)
        Returns:
          list: List of found images
      """
      try:
        raw_files = []
        page_token = None
        while True:
          results = self.service.files().list(
            q=f'\'{folder_id}\' in parents and mimeType=\'{mime_type}\' and trashed=false',
            pageSize=100,
            pageToken=page_token,
            fields='nextPageToken, files(id, name)',
            includeItemsFromAllDrives=True,
            supportsAllDrives=True
          ).execute()
          
          raw_files.extend(results.get('files', []))
          page_token = results.get('nextPageToken')
          if not page_token:
            break
        
        processed_files = []
        for file in raw_files:
          to_append = {'name': file['name'], 'id': file['id'], 'folder_name': folder_name}
          if mime_type == 'application/octet-stream':
            content = self.download_file(to_append, return_content=True)
            to_append['content'] = content  
          processed_files.append(to_append)
        return processed_files
      except Exception as e:
        self.logger.error(f'Error listing files: {e}')
        return []
    
    def _find_folder_by_name(self, drive_key: str, folder_name: str) -> Dict|None:
      """ Find a folder by its name in Playsome's shared folder
        Args:
          folder_name (str)
        Returns:
          dict: Folder name and id (for queries)
      """
      try:
        query = (f'\'{drive_key}\' in parents and mimeType=\'application/vnd.google-apps.folder\' and name = \'{folder_name}\' and trashed = false')
        results = self.service.files().list(
          q=query, 
          includeItemsFromAllDrives=True,
          supportsAllDrives=True
        ).execute()
        items = results.get('files', [])
        if items:
          return {'id': items[0]['id'], 'name': items[0]['name']}
      except HttpError as e:
        self.logger.error(f'Error finding folder: {e}')
      return None
    
    def _get_folder_name(self, folder_id: str) -> str|None:
      """ Get folder name from its ID
        Args:
          folder_id (str): The folder ID
        Returns:
          str: Folder name or None if not found
      """
      try:
        result = self.service.files().get(
          fileId=folder_id,
          fields='name',
          supportsAllDrives=True
        ).execute()
        return result.get('name')
      except HttpError as e:
        self.logger.error(f'Error getting folder name: {e}')
        return None
  
    def find_files(self, drive_key, folder=None, mime_type=None):
      if not self._connect_to_drive():
        return False
      
      result = []
      if folder:
        fold = self._find_folder_by_name(drive_key, folder)
        if not fold:
          self.logger.warning(f'Folder \'{folder}\' not found')
          return False
      else:
        folder_name = self._get_folder_name(drive_key)
        fold = {'id': drive_key, 'name': folder_name}
        folder = folder_name or drive_key

      files = self._get_files_in_folder(fold.get('id'), mime_type)
      self.logger.info(f'{len(files)} files found in \'{folder}\'')
      for f in files:
        result.append(f)
      return result
    
    def download_file(self, file: Dict, return_content: bool = False):
      """ Download file from Playsome's shared folder in /temp
        Args:
          file (Dict): Drive file name and id (same as extracted with _get_images_in_folder)
          return_content (bool): If True, returns file content as bytes. If False, saves to disk and returns path.
        Returns:
          bytes if return_content=True, str (file path) if return_content=False, None on error
      """
      try:
        request = self.service.files().get_media(fileId=file.get('id'))
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
          status, done = downloader.next_chunk()
        if return_content:
          self.logger.debug(f'File content retrieved: {file.get('name')}')
          return fh.getvalue()
        else:
          os.makedirs('temp', exist_ok=True)
          file_path = os.path.join('temp', file.get('name'))
          with open(file_path, 'wb') as f:
              f.write(fh.getbuffer())
          self.logger.info(f'File downloaded : {file_path}')
          return file_path
      except Exception as e:
        self.logger.error(f'Error while downloading {file.get('name')} : {e}')
        return None