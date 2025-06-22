from requests import Session
from requests.exceptions import RequestException, Timeout, ConnectionError
import logging


class Wiki:

  def __init__(self, config, timeout=10):
    self.session = Session()
    self.end_point = config.WIKI_API
    self.username = config.WIKI_USERNAME
    self.password = config.WIKI_PWD
    self.logger = logging.Logger()
    self.login_token = None
    self.csrf_token = None

    self.get_login_token()
    self.login_request()
    self.get_csrf_token()


  def _initialize(self):
    """ Initialise wiki connexion """
    self.get_login_token()
    self.login_request()
    self.get_csrf_token()


  def _make_request(self, method, params=None, data=None):
    """ Util func to make requests """
    try:
      if method.upper() == 'GET':
        response = self.session.get(
          url=self.end_point, 
          params=params,
          timeout=self.timeout
        )
      elif method.upper() == 'POST':
        response = self.session.post(
          url=self.end_point, 
          data=data, 
          timeout=self.timeout
        )
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


  def get_login_token(self):
    """ Step 1 : Get a login token """
    params = {
      'action': 'query',
      'meta': 'tokens',
      'type': 'login',
      'format': 'json'
    }
    try:
      response = self._make_request('GET', params=params)
      data = response.json()
      if 'error' in data:
        self.logger.error(f'API error while getting login token: {data['error']}')
      self.login_token = self._extract_values(data, 'query', 'tokens', 'logintoken')
      if not self.login_token:
        self.logger.error('Empty or invalid token')      
      self.logger.info('Login token success')
    except ValueError as e:
      self.logger.error(f'Invalid JSON response while getting login token: {e}')


  def login_request(self):
    """ Step 2: Log in with credentials """
    if not self.login_token:
      self.logger.error('Missing login token')   
    params = {
      'action': 'login',
      'lgname': self.username,
      'lgpassword': self.password,
      'lgtoken': self.login_token,
      'format': 'json'
    }
    try:
      response = self._make_request('POST', data=params)
      data = response.json()
      if 'error' in data:
        self.logger.error(f'API error while connecting: {data['error']}')
      login_result = data.get('login', {}).get('result')
      if login_result == 'Success':
        self.logger.info('Connexion success')
        return data
      elif login_result == 'Failed':
        self.logger.error('Invalid credentials')
      elif login_result == 'Throttled':
        self.logger.error('Too much login attempts, try again later')
      else:
        self.logger.error(f'Login failure: {login_result}')    
    except ValueError as e:
      self.logger.error(f'Invalid JSON response while log in: {e}')
    

  def get_csrf_token(self):
    """ Step 3: Get a CSRF token to allow us to edit pages """
    params = {
      'action': 'query',
      'meta': 'tokens',
      'format': 'json'
    }
    try:
      response = self._make_request('GET', params=params)
      data = response.json()
      if 'error' in data:
        self.logger.error(f'API error while getting CSRF token: {data['error']}')
      self.csrf_token = self._extract_nested_value(data, 'query', 'tokens', 'csrftoken')
      if not self.csrf_token or self.csrf_token == '+\\':
        self.logger.error('Invalid CSRF token')
      self.logger.info('CSRF token success')
    except ValueError as e:
      self.logger.error(f'Invalid JSON response while getting CSRF token: {e}')


  def edit_request(self, title, content, summary=''):
    """ Edit a wiki page """
    if not self.csrf_token:
      self.logger.error('Missing CSRF token - unable to edit')
    if not title or not title.strip():
      self.logger.error('Page title cannot be empty')
    params = {
      'action': 'edit',
      'title': title.strip(),
      'text': content,
      'token': self.csrf_token,
      'format': 'json'
    }
    if summary:
      params['summary'] = summary
    try:
      response = self._make_request('POST', data=params)
      data = response.json()
      if 'error' in data:
        error_info = data['error']
        error_code = error_info.get('code', 'unknown')
        error_message = error_info.get('info', 'unknown error')
        if error_code == 'badtoken':
          self.logger.error('Invalid CSRF token - need to reconnect')
        elif error_code == 'protectedpage':
          self.logger.error(f'Protected page: {error_message}')
        elif error_code == 'permissiondenied':
          self.logger.error(f'Permission denied: {error_message}')
        else:
          self.logger.error(f'Edit error ({error_code}): {error_message}')
      edit_result = data.get('edit', {})
      if edit_result.get('result') == 'Success':
        self.logger.info(f'Page {title} edited')
        return data
      else:
        self.logger.error(f'Edit failed: {edit_result}')
    except ValueError as e:
      self.logger.error(f'Invalid JSON response while editing: {e}')