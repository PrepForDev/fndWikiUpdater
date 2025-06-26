import sys
import os
import argparse
from dataclasses import dataclass
from typing import Dict

from glob import glob
from utils.config import Config
from utils.logger import Logger
from utils.mongodb import Mongo
from utils.sheets import Sheets
from utils.wiki import Wiki
from utils.yml import Yml
from utils.misc import *
from utils.language import Language

from classes.hero import Hero
from classes.template_processor import TemplateProcessor



class AppContext:
  """ Class to contain all application objects and data """
  def __init__(self):
    self.config = None
    self.logger = None
    self.sheets = None
    self.yml = None
    self.lang = None
    self.mongodb = None
    
    self.special_heroes = None
    self.events = None
    self.elements_templates = None
    self.pages_templates = None
    self.heroes = []
    self.generated_pages = []

@dataclass
class ArgsClass:
  """ Dataclass to store command line arguments """
  force: bool = False
  no_save: bool = False
  
def parse_arguments() -> ArgsClass:
  """ Parse command line arguments """
  parser = argparse.ArgumentParser(description='Friends & Dragons Wiki Updater')
  parser.add_argument('--force', action='store_true', help='Force updates even if content hasn\'t changed')
  parser.add_argument('--no_save', action='store_true', help='Desactivate MongoDB data storage and backups')
  parsed_args = parser.parse_args()
  return ArgsClass(force=parsed_args.force, no_save=parsed_args.no_save)

def init_classes(ctx: AppContext):
  """ Initialize util classes stored in /utils """
  ctx.config = Config()
  ctx.logger = Logger(log_file=ctx.config.LOG_FILE)
  ctx.logger.info('Init classes')
  ctx.sheets = Sheets(config=ctx.config, logger=ctx.logger)
  ctx.yml = Yml(logger=ctx.logger)
  ctx.lang = Language(logger=ctx.logger)

def init_mongodb_connection(ctx: AppContext, args: ArgsClass) -> bool:
  """ Initialize MongoDB connexion """
  if args.no_save:
    ctx.logger.info('MongoDB connection disabled by --no_save flag')
    return True
  mongodb = Mongo(config=ctx.config, logger=ctx.logger)
  connection_to_mongodb = mongodb.connect()
  if not connection_to_mongodb:
    ctx.logger.error('Failed to connect to MongoDB')
    return False
  return True

def load_files(ctx: AppContext) -> bool:
  """ Load .yml files """
  ctx.logger.info('Loading .yml files')
  ctx.special_heroes = ctx.yml.load(file='special_heroes', data_dir='data')
  if not ctx.special_heroes:
    ctx.logger.error('Failed to load special_heroes.yml')
    return False
  
  events_data = ctx.yml.load(file='events', data_dir='data')
  if not events_data:
    ctx.logger.error('Failed to load events.yml')
    return False
  ctx.events = events_data['Events']

  ctx.elements_templates = ctx.yml.load(file='elements_templates', data_dir='data')
  if not ctx.elements_templates:
    ctx.logger.error('Failed to load elements_templates.yml')
    return False
  
  ctx.pages_templates = ctx.yml.load(file='pages_templates', data_dir='data')
  if not ctx.pages_templates:
    ctx.logger.error('Failed to load pages_templates.yml')
    return False
  
  return True

def load_sheets_data(ctx: AppContext) -> bool:
  """ Load and process Playsome's datasheet """
  data = ctx.sheets.grab_sheets_data()
  if not data:
    ctx.logger.error('Failed to grab sheets data')
    return False
  
  ctx.logger.info('Group Playsome Data by hero')
  groups = group_data_by_hero(data)
  if not groups:
    ctx.logger.error('Failed to group data by hero')
    return False

  ctx.logger.info('Parse data into Heroes')
  ctx.heroes = []
  for group in groups:
    hero = Hero(logger=ctx.logger, special_heroes=ctx.special_heroes, events=ctx.events, elements_templates=ctx.elements_templates)
    hero.create_hero(data=group, header=data[0])
    ctx.heroes.append(hero)
  ctx.heroes.sort(key=lambda x:x.name)
  ctx.logger.info('Heroes parsed')
  return True

def load_language(ctx: AppContext, lang_file: str) -> Dict|None:
  """ Load a specific language file """
  ctx.logger.info(f'Loading language file: {lang_file}')
  lang_yml = ctx.yml.load(file=lang_file)
  if not lang_yml:
    ctx.logger.error(f'Failed to load language file: {lang_file}')
    return None
  
  lang = Language(logger=ctx.logger)
  language = lang.load_language(lang_yml)
  if not language:
    ctx.logger.error(f'Failed to process language data from: {lang_file}')
    return None
  return language

def generate_pages_contents(ctx: AppContext) -> bool:
  """ Generate pages contents translated in all known languages """
  ctx.logger.info('Generating pages contents')
  ctx.generated_pages = []
  lang_files = glob(os.path.join('data','languages','language*.yml'))
  if not lang_files:
    ctx.logger.error('No language files found')
    return False
  
  for lang_file in lang_files:
    language = load_language(ctx=ctx, lang_file=lang_file)  
    processor = TemplateProcessor(logger=ctx.logger, elements_templates=ctx.elements_templates, pages_templates=ctx.pages_templates)
    to_update = processor.process_all_templates(ctx.heroes, language)
    if not to_update:
      ctx.logger.warning(f'No content generated for language: {lang_file}')
      continue
    if isinstance(to_update, list):
      for upd in to_update:
        ctx.generated_pages.append({'lang_code': language.code, 'title': upd.get('title'), 'content': upd.get('content')})
    else:
      ctx.generated_pages.append({'lang_code': language.code, 'title': to_update.get('title'), 'content': to_update.get('content')})
  
  if len(ctx.generated_pages) == 0:
    ctx.logger.error('No pages content generated')
    return False
  
  ctx.generated_pages.sort(key=lambda x:(x['lang_code'], x['title']))
  pages_count = len(ctx.generated_pages)
  lang_count = len(lang_files)
  ctx.logger.info(f'Generated content for {int(pages_count/lang_count)} pages in {lang_count} different languages (total {pages_count} pages)')
  return True

def compare_and_update_wiki_pages(ctx: AppContext, args: ArgsClass) -> bool:
  """ Compare generated content with wiki pages content and update if different """
  print('here')

  lang_code = ctx.generated_pages[0]['lang_code']
  print(lang_code)
  wiki = Wiki(config=ctx.config, logger=ctx.logger, lang_code=lang_code)
  wiki_login = wiki.initialize()
  if not wiki_login:
    ctx.logger.error("Failed to initialize wiki connection")
    return False
  
  edit_count = 0
  for i, page in enumerate(ctx.generated_pages):
    if page.get('lang_code') != lang_code:
      if not wiki.switch_language(page.get('lang_code')):
        ctx.logger.error(f"Could not switch to language {page.get('lang_code')}")
        continue
      lang_code = page.get('lang_code')
    wiki_page_content = wiki.get_page_content(page.get('title'))
    if wiki_page_content is False:
      ctx.logger.error(f"Failed to get content for {page.get('title')}")
      continue
    if not isinstance(wiki_page_content, bool):
      wiki_page_content = wiki_page_content.rstrip()
    if wiki_page_content and wiki_page_content != page.get('content').rstrip():
      edit_count += 1
      ctx.logger.info(f'New content: edit {lang_code}/{page.get('title')}...')
      success = wiki.edit_request(title=page.get('title'), content=page.get('content').rstrip())
      if not success:
        ctx.logger.error(f'Failed to edit {page.get('title')}')
      else:
        ctx.logger.info(f'{page.get('title')} successfully edited')
    else:
      ctx.logger.info(f'Same content: skip {lang_code}/{page.get('title')}')
    
    if i % 50 == 0:
      ctx.logger.info(f'Progression: {i+1}/{len(ctx.generated_pages)} pages checked, {edit_count} edited')
  ctx.logger.info(f'{edit_count} pages edited out of {len(ctx.generated_pages)} checked')
  return True


def cleanup(ctx: AppContext, args: ArgsClass):
  """ Cleanup before close """
  if ctx.mongodb and not args.no_save:
    ctx.mongodb.close()


def main():
  """ Main function """
  args = parse_arguments()
  ctx = AppContext()

  try:
    init_classes(ctx)
    if not init_mongodb_connection(ctx, args):
      ctx.logger.error('Exit due to MongoDB connexion failure -> restart with --no_save if it doesn\'t matter ;)')
      sys.exit(1)
      
    if not load_files(ctx):
      ctx.logger.error('Exit due to failure to load required files')
      sys.exit(1)

    if not load_sheets_data(ctx):
        ctx.logger.error('Exit due to failure to load sheet data')
        sys.exit(1)
    
    if not generate_pages_contents(ctx):
      ctx.logger.error('Exit due to failure to generate pages contents')
      sys.exit(1)

    #ctx.generated_pages = [c for c in ctx.generated_pages if c.get('title') == 'Hero Stats' or c.get('title') == 'Estadísticas de Héroe' or c.get('title') == 'Statistiques du Héros'] # FOR TESTS

    if not compare_and_update_wiki_pages(ctx, args):
      ctx.logger.error('Exit due to failure to compare and update wiki pages')
      sys.exit(1)

    ctx.logger.info('Script completed successfully')

  except Exception as e:
    if ctx.logger:
      ctx.logger.error(f'Unexpected error: {str(e)}')
    else:
      print(f'Error: {str(e)}')
      sys.exit(1)

  finally:
    cleanup(ctx, args)


if __name__ == '__main__':
  main()