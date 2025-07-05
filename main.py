import sys
import os
import argparse
import copy
from dataclasses import dataclass

from glob import glob
from utils.config import Config
from utils.logger import Logger
from utils.mongodb import Mongo
from utils.backup import DatabaseBackupManager
from utils.sheets import Sheets
from utils.wiki import Wiki
from utils.yml import Yml
from utils.misc import *
from utils.language import Language
from utils.drive import Drive

from classes.hero import Hero, match_images_with_heroes
from classes.template_processor import TemplateProcessor
from classes.heroclass import create_heroclasses



class AppContext:
  """ Class to contain all application objects and data """
  def __init__(self):
    self.config = None
    self.logger = None
    self.sheets = None
    self.yml = None
    self.lang = None
    self.mongodb = None
    self.drive = None
    
    self.playsome_data = None
    self.languages = []
    self.elements_templates = None
    self.pages_templates = None
    self.heroes = []
    self.generated_pages = []
    self.images = []
    self.heroclasses = []
    
    self.files_to_load = [
      {'attr': 'playsome_data', 'data_dir': 'data', 'name': 'playsome_data.yml'},
      {'attr': 'pages_templates', 'data_dir': 'data', 'name': 'pages_templates.yml'},
      {'attr': 'elements_templates', 'data_dir': 'data', 'name': 'elements_templates.yml'}
    ]
    lang_files = glob(os.path.join('data','languages','language*.yml'))
    if not lang_files:
      self.logger.error('No language files found')
    for lang_file in lang_files:
      self.files_to_load.append({'attr': 'languages', 'data_dir': '', 'name': lang_file})

    self.folders = [
      {'name': 'Heroes', 'object': 'Hero'}
    ]

  def init_stored_data(self):
    self.stored_data = [
      {'stored': 'heroes', 'new': [hero.to_dict() for hero in self.heroes]},
      {'stored': 'elements_templates', 'new': copy.deepcopy([self.elements_templates])},
      {'stored': 'pages_templates', 'new': copy.deepcopy([self.pages_templates])},
      {'stored': 'playsome_data', 'new': copy.deepcopy([self.playsome_data])},
      {'stored': 'languages', 'new': [lang.to_dict() for lang in self.languages]}
    ]


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
  ctx.drive = Drive(logger=ctx.logger, config=ctx.config)


def init_mongodb_connection(ctx: AppContext, args: ArgsClass) -> bool:
  """ Initialize MongoDB connexion """
  if args.no_save:
    ctx.logger.info('MongoDB connection disabled by --no_save flag')
    return True
  ctx.mongodb = Mongo(config=ctx.config, logger=ctx.logger)
  connection_to_mongodb = ctx.mongodb.connect()
  if not connection_to_mongodb:
    ctx.logger.error('Failed to connect to MongoDB')
    return False
  backup_manager = DatabaseBackupManager(config=ctx.config, mongodb=ctx.mongodb, logger=ctx.logger)
  ctx.mongodb.set_backup_manager(backup_manager=backup_manager)
  return True


def load_files(ctx: AppContext) -> bool:
  """ Load .yml files """
  ctx.logger.info('Loading .yml files')
  for file in ctx.files_to_load:
    content = ctx.yml.load(file=file.get('name'), data_dir=file.get('data_dir'))
    if content:
      if getattr(ctx, file.get('attr')) is None:
        setattr(ctx, file.get('attr'), content)
      else:
        new_lang = Language(logger=ctx.logger)
        if new_lang.load_language(content):
          getattr(ctx, file.get('attr')).append(new_lang)
    else:
      ctx.logger.error(f'Failed to load {file.get('name')}')
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
    hero = Hero(ctx)
    hero.create_hero(data=group, header=data[0])
    ctx.heroes.append(hero)
  ctx.heroes.sort(key=lambda x:x.name)
  ctx.logger.info('Heroes parsed')
  return True

def create_classes_from_heroes(ctx: AppContext) -> bool:
  ctx.heroclasses = create_heroclasses(heroes=ctx.heroes)
  return True

def load_drive_data(ctx: AppContext) -> bool:
  """ Load files from shared Google Drive and associate them with their heroes """
  for folder in ctx.folders:
    image_list = ctx.drive.find_images(folder=folder.get('name'))
    if not image_list:
      return False
    
    if folder.get('object') == 'Hero':
      ctx.logger.info('Checking hero portraits...')
      match_images_with_heroes(ctx=ctx, images=image_list, attribute='drive')

  return True

def compare_actual_data_to_stored_data(ctx: AppContext, args: ArgsClass) -> bool:
  """ Compare stored data to freshly loaded data """
  if args.no_save:
    return True
  
  ctx.init_stored_data()
  has_new_data = False
  has_errors = False
  for d in ctx.stored_data:
    new_data = d.get('new')
    old_data = ctx.mongodb.read(collection=d.get('stored'))
  
    if not old_data:
      ctx.logger.info(f'No stored data: saving new data in {d.get('stored')}')
      if not ctx.mongodb.write(collection=d.get('stored'), data=d.get('new')):
        has_errors = True
      has_new_data = True
    else:
      if ctx.mongodb.compare_data(old_data=old_data, new_data=new_data):
        if args.force:
          ctx.logger.info('No change in data: update forced due to --force argument')
          has_new_data = True
  
  if has_new_data and not has_errors:
    ctx.logger.info('New data detected -> creating backup before update')
    if not ctx.mongodb.backup_db():
      return False
    for d in ctx.stored_data:
      if not ctx.mongodb.write(collection=d.get('stored'), data=d.get('new')):
        return False
  elif has_errors:
    return False
  elif not has_new_data:
    ctx.logger.warning('No change in data: update stopped -> restart with --force if you want to start updating anyway')
    return False
  
  return True
  

def generate_pages_contents(ctx: AppContext) -> bool:
  """ Generate pages contents translated in all known languages """
  ctx.logger.info('Generating pages contents')
  ctx.generated_pages = []

  for language in ctx.languages:
    ctx.logger.info(f'Language : {language.name}')
    processor = TemplateProcessor(logger=ctx.logger, elements_templates=ctx.elements_templates, pages_templates=ctx.pages_templates, all_languages=ctx.languages)
    to_process = [{'object': 'hero', 'list': ctx.heroes}, {'object': 'heroclass', 'list': ctx.heroclasses}]
    to_update = processor.process_all_templates(to_process, language)
    if not to_update:
      ctx.logger.warning(f'No content generated for language: {language.name}')
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
  lang_count = len(ctx.languages)
  ctx.logger.info(f'Generated content for {int(pages_count/lang_count)} pages in {lang_count} different languages (total {pages_count} pages)')
  return True


def compare_and_update_wiki_pages(ctx: AppContext, args: ArgsClass) -> bool:
  """ Compare generated content with wiki pages content and update if different """
  lang_code = ctx.generated_pages[0]['lang_code']
  wiki = Wiki(config=ctx.config, logger=ctx.logger, lang_code=lang_code)
  wiki_login = wiki.initialize()
  if not wiki_login:
    ctx.logger.error('Failed to initialize wiki connection')
    return False
  
  edit_count = 0
  for i, page in enumerate(ctx.generated_pages):
    if page.get('lang_code') != lang_code:
      if not wiki.switch_language(page.get('lang_code')):
        ctx.logger.error(f'Could not switch to language {page.get('lang_code')}')
        continue
      lang_code = page.get('lang_code')
    wiki_page_content = wiki.get_page_content(page.get('title'))
    if wiki_page_content is False:
      ctx.logger.error(f'Failed to get content for {page.get('title')}')
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

def compare_and_update_portrait_files(ctx: AppContext):
  """ Compare drive files with wiki files, upload those which are not already in the wiki and update the TraitsAndPortraitsFiles page """
  wiki = Wiki(config=ctx.config, logger=ctx.logger, lang_code='en')
  wiki_login = wiki.initialize()
  if not wiki_login:
    ctx.logger.error('Failed to initialize wiki connection')
    return False
  file_list_str = wiki.get_page_content('TraitsAndPortraitsFiles')
  if not file_list_str:
    ctx.logger.error('Failed to get content for TraitsAndPortraitsFiles page')
    return False
  traits_and_portraits_list = file_list_str.split(' ')
  match_images_with_heroes(ctx=ctx, images=[{'name': portrait} for portrait in traits_and_portraits_list if 'Portrait' in portrait], attribute='wiki')

  has_new_images = False
  for hero in ctx.heroes:
    if hero.file.drive and not hero.file.wiki:
      ctx.logger.info(f'---> New file found for {hero.name}')
      file_path = ctx.drive.download_image(hero.file.drive)
      if not file_path:
        return False
      hero.portrait = f'{hero.name.replace(' ', '_')}_Portrait.png'
      wiki_upload = wiki.upload_file(filepath=file_path, wiki_filename=hero.portrait)
      if not wiki_upload:
        return False
      has_new_images = True
    elif hero.file.wiki:
      hero.portrait = f'{hero.name.replace(' ', '_')}_Portrait.png'
  
  if has_new_images:
    update_wiki = wiki.update_traits_and_portraits_files_page()
    if not update_wiki:
      return False
  
  heroes_without_portrait = [h.name for h in ctx.heroes if h.portrait is None]
  if len(heroes_without_portrait) > 0:
    ctx.logger.warning(f'---> Heroes found without portrait : {', '.join(heroes_without_portrait)}')
  
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

    if not load_files(ctx):
      ctx.logger.error('Exit due to failure to load required files')
      sys.exit(1)
    
    if not init_mongodb_connection(ctx, args):
      ctx.logger.error('Exit due to MongoDB connexion failure -> restart with --no_save if it doesn\'t matter ;)')
      sys.exit(1)
    
    if not load_sheets_data(ctx):
      ctx.logger.error('Exit due to failure to load sheet data')
      sys.exit(1)

    if not create_classes_from_heroes(ctx):
      ctx.logger.error('Exit due to failure to create classes objects')
      sys.exit(1)

    if not load_drive_data(ctx):
      ctx.logger.error('Exit due to failure to load files from shared drive')
      sys.exit(1)
    
    if not compare_actual_data_to_stored_data(ctx, args):
      sys.exit(1)
    
    if not generate_pages_contents(ctx):
      ctx.logger.error('Exit due to failure to generate pages contents')
      sys.exit(1)
    
    #ctx.generated_pages = [c for c in ctx.generated_pages if c.get('title') == 'Hero Class Analysis' or c.get('title') == 'Análisis de la clase de Héroe' or c.get('title') == 'Analyse des classes de Héros'] # FOR TESTS
    
    if not compare_and_update_wiki_pages(ctx, args):
      ctx.logger.error('Exit due to failure to compare and update wiki pages')
      sys.exit(1)
    
    if not compare_and_update_portrait_files(ctx):
      ctx.logger.error('Exit due to failure to compare wiki files with drive')
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