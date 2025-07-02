from requests import Session
from requests.exceptions import RequestException, Timeout, ConnectionError
from datetime import datetime
import time
import random
import os

class Wiki:

  def __init__(self, config, logger, lang_code='en', timeout=10):
    self.session = Session()
    self.base_url = config.WIKI_URL
    self.username = config.WIKI_USERNAME
    self.password = config.WIKI_PWD
    self.lang_code = lang_code
    self.timeout = timeout
    self.logger = logger
    self.login_token = None
    self.csrf_token = None

    self.last_edit_time = 0
    self.consecutive_edits = 0
    self.base_delay = 1
    self.batch_pause_threshold = 20
    self.batch_pause_duration = 10

  def initialize(self) -> bool:
    """ Initialise wiki connexion """
    self.get_login_token()
    if self.login_token:
      self.login_request()
    self.get_csrf_token()
    if self.csrf_token:
      return True
    return None


  def _get_api_endpoint(self):
    """ Get the correct API endpoint for the current language """
    if self.lang_code == 'en':
        return f'{self.base_url}api.php'
    else:
        return f'{self.base_url}{self.lang_code}/api.php'


  def _make_request(self, method, params={}, data={}, file=None):
    """ Util func to make requests """
    self._apply_request_delay()
    endpoint = self._get_api_endpoint()
    try:
      if method.upper() == 'GET':
        params['uselang'] = self.lang_code
        response = self.session.get(
          url=endpoint, 
          params=params,
          timeout=self.timeout
        )
      elif method.upper() == 'POST':
        data['uselang'] = self.lang_code
        response = self.session.post(
          url=endpoint, 
          data=data, 
          timeout=self.timeout
        )
      elif method.upper() == 'POST UPLOAD':
        response = self.session.post(
          url=endpoint,
          data=data,
          files=file,
          timeout=self.timeout)
      else:
        self.logger.error(f'Unsupported request method : {method}')
      response.raise_for_status()
      return response
    
    except Timeout:
      self.logger.error('Timeout while requesting wiki')
    except ConnectionError:
      self.logger.error('Unable to login to wiki')
    except RequestException as e:
      self.logger.error(f'Request error : {e}')


  def _extract_values(self, data, *keys):
    """ Util to extract nested values """
    try:
      current = data
      for key in keys:
        current = current[key]
      return current
    except (KeyError, TypeError):
      self.logger.error(f'Answer error: missing key {'.'.join(keys)}')
      return None


  def get_login_token(self) -> bool:
    """ Step 1 : Get a login token """
    params = {
      'action': 'query',
      'meta': 'tokens',
      'type': 'login',
      'format': 'json'
    }
    try:
      response = self._make_request('GET', params=params)
      if not response:
        return False
      
      data = response.json()
      if 'error' in data:
        self.logger.error(f'API error while getting login token: {data['error']}')
        return False
      
      self.login_token = self._extract_values(data, 'query', 'tokens', 'logintoken')
      if not self.login_token:
        self.logger.error('Empty or invalid token')   
        return False
      
      self.logger.info('Login token success')
      return True

    except ValueError as e:
      self.logger.error(f'Invalid JSON response while getting login token: {e}')
      return False


  def login_request(self) -> bool:
    """ Step 2: Log in with credentials """
    if not self.login_token:
      self.logger.error('Missing login token')
      return False
    
    params = {
      'action': 'login',
      'lgname': self.username,
      'lgpassword': self.password,
      'lgtoken': self.login_token,
      'format': 'json'
    }
    try:
      response = self._make_request('POST', data=params)
      if not response:
        return False
      
      data = response.json()
      if 'error' in data:
        self.logger.error(f'API error while connecting: {data['error']}')
        return False
      
      login_result = data.get('login', {}).get('result')
      if login_result == 'Success':
        self.logger.info('Connexion success')
        return True
      
      elif login_result == 'Failed':
        self.logger.error('Invalid credentials')
      elif login_result == 'Throttled':
        self.logger.error('Too much login attempts, try again later')
      else:
        self.logger.error(f'Login failure: {login_result}')    
      return False
    
    except ValueError as e:
      self.logger.error(f'Invalid JSON response while log in: {e}')
      return False
    

  def get_csrf_token(self) -> bool:
    """ Step 3: Get a CSRF token to allow us to edit pages """
    params = {
      'action': 'query',
      'meta': 'tokens',
      'format': 'json'
    }
    try:
      response = self._make_request('GET', params=params)
      if not response:
        return False
      data = response.json()
      if 'error' in data:
        self.logger.error(f'API error while getting CSRF token: {data['error']}')
        return False
      
      self.csrf_token = self._extract_values(data, 'query', 'tokens', 'csrftoken')
      if not self.csrf_token or self.csrf_token == '+\\':
        self.logger.error('Invalid CSRF token')
        return False
      
      self.logger.info('CSRF token success')
      return True
    
    except ValueError as e:
      self.logger.error(f'Invalid JSON response while getting CSRF token: {e}')
      return False

  def _apply_request_delay(self):
    """ Apply delay between requests """
    current_time = time.time()
    if self.last_edit_time == 0:
      self.last_edit_time = current_time
      return
    elapsed = current_time - self.last_edit_time
    
    if elapsed < self.base_delay:
        delay = self.base_delay - elapsed + random.uniform(0.5, 1.5)
        self.logger.debug(f'Applying delay: {delay:.1f}s')
        time.sleep(delay)
    
    if self.consecutive_edits > 0 and self.consecutive_edits % self.batch_pause_threshold == 0:
        pause = self.batch_pause_duration + random.uniform(-5, 10)
        self.logger.info(f'Batch pause after {self.consecutive_edits} requests: {pause:.1f}s')
        time.sleep(pause)
    self.last_edit_time = time.time()

  def _apply_edit_delay(self):
    """ Apply extra delay between edits """
    extra_delay = random.uniform(1, 3)
    self.logger.debug(f'Extra edit delay: {extra_delay:.1f}s')
    time.sleep(extra_delay)

  def _build_page_title(self, title):
    return title.strip().replace(' ', '_').replace('\'','%27').replace('&', '%26')
  

  def _build_page_url(self, title):
    clean_title = self._build_page_title(title)
    if self.lang_code == 'en':
      return f'{self.base_url}wiki/{clean_title}'
    else:
      return f'{self.base_url}{self.lang_code}/wiki/{clean_title}'
  

  def edit_request(self, title, content, summary=None, minor=False):
    """ Edit a wiki page """
    if not self.csrf_token:
      self.logger.error('Missing CSRF token - unable to edit')
      return False
    
    if not title or not title.strip():
      self.logger.error('Page title cannot be empty')
      return False
    
    self._apply_edit_delay()
    clean_title = self._build_page_title(title)
    data = {
      'action': 'edit',
      'title': clean_title,
      'text': content,
      'token': self.csrf_token,
      'format': 'json'
    }
    if summary:
      data['summary'] = f'[{self.lang_code}] {summary}'
    else:
      data['summary'] = f'[{self.lang_code}] Update from {datetime.today().strftime('%Y-%m-%d')}'
    try:
      response = self._make_request('POST', data=data)
      if not response:
        return False
      data = response.json()
      if 'error' in data:
        error_info = data['error']
        error_code = error_info.get('code', 'unknown')
        error_message = error_info.get('info', 'unknown error')

        if error_code == 'badtoken':
          self.logger.error('Invalid CSRF token - need to reconnect')
          if self.get_csrf_token():
            return self.edit_request(title, content, summary, minor)
        elif error_code == 'ratelimited':
          self.logger.warning('Rate limited - waiting 60s before retry')
          time.sleep(60)
          return self.edit_request(title, content, summary, minor)
        elif error_code == 'protectedpage':
          self.logger.error(f'Protected page: {error_message}')
        elif error_code == 'permissiondenied':
          self.logger.error(f'Permission denied: {error_message}')
        else:
          self.logger.error(f'Edit error ({error_code}): {error_message}')
        return False
      
      edit_result = data.get('edit', {})
      if edit_result.get('result') == 'Success':
        self.consecutive_edits += 1
        self.last_edit_time = time.time()
        self.logger.info(f'Page {title} edited (#{self.consecutive_edits})')
        return True
      else:
        self.logger.error(f'Edit failed: {edit_result}')
        return False
      
    except ValueError as e:
      self.logger.error(f'Invalid JSON response while editing: {e}')
      return False
    

  def get_page_content(self, title):
    """ Get the content of a wiki page """
    if not title or not title.strip():
      self.logger.error('Page title cannot be empty')
      return False
      
    clean_title = self._build_page_title(title)
    params = {
      'action': 'query',
      'titles': clean_title,
      'prop': 'revisions',
      'rvprop': 'content',
      'rvslots': 'main',
      'format': 'json'
    }
    try:
      response = self._make_request('GET', params=params)
      if not response:
        return False
      
      data = response.json()
      if 'error' in data:
        self.logger.error(f'API error while getting page content: {data.get('error')}')
        return False
      
      pages = data.get('query', {}).get('pages', {})
      for page_id, page_data in pages.items():
        if page_id == '-1':
          self.logger.error(f'Page "{title}" does not exist')
          return True
        
        revisions = page_data.get('revisions', [])
        if revisions:
          return revisions[0].get('slots', {}).get('main', {}).get('*')
        else:
          self.logger.error(f'No revisions found for page "{title}"')
          return ''
        
    except ValueError as e:
      self.logger.error(f'Invalid JSON response while getting page content: {e}')
      return False
    
  def page_exists(self, title) -> bool:
    """ Check if page exists """
    if not title or not title.strip():
      self.logger.error('Page title cannot be empty')
      return False
        
    clean_title = self._build_page_title(title)
    params = {
        'action': 'query',
        'titles': clean_title,
        'format': 'json'
    }
    try:
      response = self._make_request('GET', params=params)
      if not response:
        return False
            
      data = response.json()
      if 'error' in data:
        return False
            
      pages = data.get('query', {}).get('pages', {})
      return not any(page_id == '-1' for page_id in pages.keys())
        
    except ValueError as e:
      self.logger.error(f'Invalid JSON response while checking if page exists: {e}')
      return False


  def switch_language(self, new_lang_code):
    """ Changes self.lang_code and reinitializes session for the new language """
    if new_lang_code == self.lang_code:
      return True
    
    self.logger.info(f'Switching language to {new_lang_code}')
    self.lang_code = new_lang_code

    self.session = Session()
    self.login_token = None
    self.csrf_token = None

    if not self.get_login_token():
      self.logger.error(f'Failed to get login token after switching to {new_lang_code}')
      return False

    if not self.login_request():
      self.logger.error(f'Failed to log in after switching to {new_lang_code}')
      return False

    if not self.get_csrf_token():
      self.logger.error(f'Failed to get new CSRF token after switching to {new_lang_code}')
      return False

    return True
  

  def upload_file(self, filepath, wiki_filename: str, ignore_warnings=True) -> bool:
    """ Upload a file to the wiki and delete local copy after upload
      Args:
        filepath: local path to the file (in /temp)
        filename: file name as it appears on the wiki
        ignore_warnings: if True, ignore warnings (duplicate)
      Returns:
        True on succes, False otherwise
    """
    if not os.path.isfile(filepath):
      self.logger.error(f'File not found: {filepath}')
      return False

    self._apply_edit_delay()
    try:
      with open(filepath, 'rb') as file_stream:
        file = {'file': (wiki_filename, file_stream, 'image/png')}
        data = {
          'action': 'upload',
          'filename': wiki_filename,
          'token': self.csrf_token,
          'format': 'json',
          'ignorewarnings': '1' if ignore_warnings else '0'
        }

        response = self._make_request('POST UPLOAD', data=data, file=file)
        response.raise_for_status()
        result = response.json()
        if 'error' in result:
          self.logger.error(f'Upload error: {result.get('error')}')
          return False
        upload_result = result.get('upload', {}).get('result')
        if upload_result != 'Success':
          self.logger.warning(f'Upload result: {upload_result}')
          return False
        self.logger.info(f'File {wiki_filename} uploaded successfully')          

    except RequestException as e:
      self.logger.error(f'Upload failed due to request error: {e}')
      return False
    except ValueError as e:
      self.logger.error(f'Invalid JSON response during upload: {e}')
      return False
    
    try:
      os.remove(filepath)
      return True
    except OSError as e:
      self.logger.warning(f'Error while removing file after upload : {e}')
    

  def update_traits_and_portraits_files_page(self):
    """ Update the 'TraitsAndPortraitsFiles' page with all png files containing 'Trait' or 'Portrait' in their name """
    filtered_files = []
    params = {
      'action': 'query',
      'list': 'allimages',
      'ailimit': '500',
      'format': 'json'
    }

    while True:
      response = self._make_request('GET', params=params)
      if not response:
        self.logger.error('Error while getting files list')
        return False

      data = response.json()
      if 'error' in data:
        self.logger.error(f'Error API allimages: {data.get('error')}')
        return False

      images = data.get('query', {}).get('allimages', [])
      for img in images:
        name = img.get('name', '')
        if name.lower().endswith('.png') and ('trait' in name.lower() or 'portrait' in name.lower()):
          filtered_files.append(name)

      if 'continue' in data:
        params.update(data.get('continue'))
      else:
        break

    if not filtered_files:
      self.logger.error('No traits nor portraits files found')
      return False
    
    page_content = ' '.join(filename for filename in sorted(filtered_files))
    return self.edit_request(
      title='TraitsAndPortraitsFiles',
      content=page_content
    )