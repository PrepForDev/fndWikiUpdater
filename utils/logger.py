import os
import logging
import datetime
from logging.handlers import RotatingFileHandler


class Logger:
  def __init__(self, log_file):
    self.log_dir = 'logs'
    self.setup_logger(log_file)

  def _str_now(self):
    return f'[{datetime.datetime.now().strftime('%d/%b/%Y %H:%M:%S')}]'

  def setup_logger(self, log_file):
    full_log_path = os.path.join(self.log_dir, f'{log_file}.log')
    os.makedirs(self.log_dir, exist_ok=True)
    self.logger = logging.getLogger()
    self.logger.setLevel(logging.INFO)
    file_handler = RotatingFileHandler(full_log_path, maxBytes=10485760, backupCount=5, encoding='utf-8')
    file_formatter = logging.Formatter('%(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    if not any(isinstance(h, RotatingFileHandler) for h in self.logger.handlers):
      self.logger.addHandler(file_handler)

  def error(self, msg):
    message = f'{self._str_now()} {msg}'
    print(message)
    self.logger.error(message)

  def info(self, msg):
    message = f'{self._str_now()} {msg}'
    print(message)
    self.logger.info(message)