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
          self.logger.error(f"API build failed: {e}")
      else:
          self.logger.error('Google Drive init failed')
      return False
     
    def _get_images_in_folder(self, folder_id: str, folder_name=None) -> List[Dict]:
      """ Get all images in a drive folder        
        Args:
          folder_id (str)
          folder_name (str)
        Returns:
          list: List of found images
      """
      try:
        results = self.service.files().list(
            q=f"'{folder_id}' in parents and mimeType='image/png' and trashed=false",
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        file_list = results.get('files', [])
        images = []

        for file in file_list:
          images.append({
            'name': file['name'],
            'id': file['id'],
            'folder_name': folder_name
          })
        return images
      except Exception as e:
        self.logger.error(f"Error listing images: {e}")
        return []
    
    def _find_folder_by_name(self, folder_name: str) -> Dict|None:
      """ Find a folder by its name in Playsome's shared folder
        Args:
          folder_name (str)
        Returns:
          dict: Folder name and id (for queries)
      """
      try:
        query = (f"'{self.config.PLAYSOME_DRIVE_KEY}' in parents and mimeType='application/vnd.google-apps.folder' and name = '{folder_name}' and trashed = false")
        results = self.service.files().list(
          q=query, 
          includeItemsFromAllDrives=True,
          supportsAllDrives=True
        ).execute()
        items = results.get('files', [])
        if items:
          return {'id': items[0]['id'], 'name': items[0]['name']}
      except HttpError as e:
        self.logger.error(f"Error finding folder: {e}")
      return None
  
    def find_images(self, folder):
      if not self._connect_to_drive():
        return False
      
      result = []
      fold = self._find_folder_by_name(folder)
      if not fold:
        self.logger.warning(f'Folder \'{folder}\' not found')
        return False

      images = self._get_images_in_folder(fold.get('id'))
      self.logger.info(f'{len(images)} images found in \'{folder}\'')
      for img in images:
        result.append(img)
      return result
    
    def download_image(self, image: Dict) -> bool:
      """ Download file from Playsome's shared folder in /temp
        Args:
          image (Dict): Drive file name and id (same as extracted with _get_images_in_folder)
          filename (str): Drive file name
        Returns:
          path of the downloaded file
      """
      try:
        request = self.service.files().get_media(fileId=image.get('id'))
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
          status, done = downloader.next_chunk()
        os.makedirs('temp', exist_ok=True)
        file_path = os.path.join('temp', image.get('name'))
        with open(file_path, 'wb') as f:
            f.write(fh.getbuffer())
        self.logger.info(f'File downloaded : {file_path}')
        return file_path
      except Exception as e:
        self.logger.error(f'Error while downloading {image.get('name')} : {e}')
        return None