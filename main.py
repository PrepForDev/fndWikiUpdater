import sys
import os
import argparse
import copy
from dataclasses import dataclass, field
from typing import List

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
from classes.pet import Pet, match_images_with_pets
from classes.template_processor import TemplateProcessor
from classes.heroclass import create_heroclasses
from classes.talent import create_talents
from classes.map import create_all_maps, match_images_with_maps
from classes.grid import create_all_grids


class AppContext:
  """ Class to contain all application objects and data """
  def __init__(self):
    self.config = Config()
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
    self.pets = []
    self.maps = []
    self.grids = []
    self.generated_pages = []
    self.images = []
    self.heroclasses = []
    self.talents = []   
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
      {'name': 'Heroes', 'object': 'Hero', 'drive_key': self.config.PLAYSOME_DRIVE_KEY, 'mime_type': 'image/png', 'display': 'hero portraits'},
      {'name': 'PetPortraits-and-Icons', 'object': 'Pet','drive_key': self.config.PLAYSOME_DRIVE_KEY, 'mime_type': 'image/png', 'display': 'pet portraits'},
      {'name': None, 'object': 'Map', 'drive_key': self.config.PLAYSOME_SPIRE_KEY, 'mime_type': 'application/octet-stream', 'display': 'spire maps'},
    ]

  def init_stored_data(self):
    self.stored_data = [
      {'stored': 'heroes', 'new': [hero.to_dict() for hero in self.heroes]},
      {'stored': 'pets', 'new': [pet.to_dict() for pet in self.pets]},
      {'stored': 'elements_templates', 'new': copy.deepcopy([self.elements_templates])},
      {'stored': 'pages_templates', 'new': copy.deepcopy([self.pages_templates])},
      {'stored': 'playsome_data', 'new': copy.deepcopy([self.playsome_data])},
      {'stored': 'languages', 'new': [lang.to_dict() for lang in self.languages]},
      {'stored': 'maps', 'new': [map.to_dict() for map in self.maps]}
    ]

  def init_data_to_process(self):
    self.data_to_process = [
      {'object': 'hero', 'list': self.heroes},
      {'object': 'heroclass', 'list': self.heroclasses},
      {'object': 'talent', 'list': self.talents},
      {'object': 'pet', 'list': self.pets},
      {'object': 'map', 'list': self.maps},
      {'object': 'grid', 'list': self.grids},
    ]


@dataclass
class ArgsClass:
  """ Dataclass to store command line arguments """
  force: bool = False
  no_save: bool = False
  no_maps: bool = False
  templates: List[str] = field(default_factory=list)
  
def parse_arguments(ctx: AppContext) -> ArgsClass:
  """ Parse command line arguments """
  parser = argparse.ArgumentParser(prog='fndWikiUpdater', description='Friends & Dragons Wiki Updater', formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument('--force', action='store_true', help='force updates even if content hasn\'t changed')
  parser.add_argument('--no_save', action='store_true', help='desactivate MongoDB data storage and backups')
  parser.add_argument('--no_maps', action='store_true', help='desactivate spire maps update')

  template_help = 'update only listed templates :\n' + '\n'.join([f'  - {k.lower()}' for k in ctx.pages_templates.keys()]) + '\nexemple: py main.py --template "hero 3a" "hero gear"'
  parser.add_argument('--templates', nargs='*', help=template_help)
  try:
    parsed_args = parser.parse_args()
    if parsed_args.templates:
      valid_templates = [k.lower() for k in ctx.pages_templates.keys()]
      invalid = [t for t in parsed_args.templates if t.lower() not in valid_templates]
      if invalid:
        ctx.logger.error(f"Invalid template name(s): {', '.join(invalid)}")
        parser.print_help()
        exit(1)
  except SystemExit:
    exit(0)
  return ArgsClass(force=parsed_args.force, no_save=parsed_args.no_save, no_maps=parsed_args.no_maps, templates=parsed_args.templates or [])


def init_classes(ctx: AppContext):
  """ Initialize util classes stored in /utils """
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
  """ Load and process Googlesheets (Playsome's heroes and personnal Pets) """
  heroes_data = ctx.sheets.grab_sheets_data(key=ctx.config.PLAYSOME_SHEET_KEY)
  if not heroes_data:
    ctx.logger.error('Failed to grab Playsome\'s sheet data')
    return False
  
  ctx.logger.info('Group Playsome Data by hero')
  groups = group_data_by_hero(heroes_data)
  if not groups:
    ctx.logger.error('Failed to group data by hero')
    return False

  ctx.logger.info('Parse data into Heroes')
  ctx.heroes = []
  for group in groups:
    hero = Hero(ctx)
    hero.create_hero(data=group, header=heroes_data[0])
    ctx.heroes.append(hero)
  ctx.heroes.sort(key=lambda x:x.name)
  ctx.logger.info('Heroes parsed')

  pets_data = ctx.sheets.grab_sheets_data(key=ctx.config.PET_SHEET_KEY)
  if not pets_data:
    ctx.logger.error('Failed to grab Pets sheet data')
    return False
  
  ctx.logger.info('Parse data into Pets')
  ctx.pets = []
  for pet_data in pets_data[1:]:
    pet = Pet(ctx)
    pet.create_pet(data=pet_data, header=pets_data[0])
    ctx.pets.append(pet)
  ctx.pets.sort(key=lambda x:x.name)
  ctx.logger.info('Pets parsed')
  return True

def create_classes_from_heroes(ctx: AppContext) -> bool:
  ctx.heroclasses = create_heroclasses(heroes=ctx.heroes)
  return True

def create_talents_from_heroes(ctx: AppContext) -> bool:
  ctx.talents = create_talents(heroes=ctx.heroes)
  return True

def load_drive_data(ctx: AppContext, args: ArgsClass) -> bool:
  """ Load files from shared Google Drive and associate them with their objects """
  for folder in ctx.folders:
    if args.no_maps and folder.get('object') == 'Map':
      ctx.logger.info(f'Maps skipped due to no_maps argument')
    else:
      ctx.logger.info(f'Checking {folder.get('display')}...')
      file_list = ctx.drive.find_files(drive_key=folder.get('drive_key'), folder=folder.get('name'), mime_type=folder.get('mime_type'))
      if not file_list:
        return False
      
      match folder.get('object'):
        case 'Hero':
          match_images_with_heroes(ctx=ctx, images=file_list, attribute='drive')
        case 'Pet':
          match_images_with_pets(ctx=ctx, images=file_list, attribute='drive')
        case 'Map':
          create_all_maps(ctx=ctx, files=[ctx.yml.load(raw_data=f['content']) for f in file_list])
          create_all_grids(ctx=ctx, path='temp')

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
  

def generate_pages_contents(ctx: AppContext, args: ArgsClass) -> bool:
  """ Generate pages contents translated in all known languages """
  ctx.logger.info('Generating pages contents')
  ctx.generated_pages = []

  for language in ctx.languages:
    ctx.logger.info(f'Language : {language.name}')
    processor = TemplateProcessor(logger=ctx.logger, elements_templates=ctx.elements_templates, pages_templates=ctx.pages_templates, all_languages=ctx.languages, all_heroes=ctx.heroes, all_pets=ctx.pets, maps_processing=args.no_maps, templates=args.templates)
    ctx.init_data_to_process()
    to_update = processor.process_all_templates(ctx.data_to_process, language)
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
      return False
    
    current_content = wiki_page_content.rstrip() if wiki_page_content is not None else None
    new_content = page.get('content').rstrip()
    if current_content is None:
      ctx.logger.info(f"Page {page.get('title')} doesn't exist")
    if current_content != new_content:
      edit_count += 1
      ctx.logger.info(f"New content: edit {lang_code}/{page.get('title')}...")
      success = wiki.edit_request(title=page.get('title'), content=new_content)
      if not success:
        ctx.logger.error(f"Failed to edit {page.get('title')}")
      else:
        ctx.logger.info(f"{page.get('title')} successfully edited")
    else:
      ctx.logger.info(f"Same content: skip {lang_code}/{page.get('title')}")
    
    if i % 50 == 0:
      ctx.logger.info(f'Progression: {i+1}/{len(ctx.generated_pages)} pages checked, {edit_count} edited')
  ctx.logger.info(f'{edit_count} pages edited out of {len(ctx.generated_pages)} checked')
  return True


def compare_and_update_files(ctx: AppContext):
    """ Compare drive files with wiki files, upload those which are not already in the wiki and update FilesPage in all wikis """

    all_wikis = []
    for lang in ctx.languages:
      wiki = Wiki(config=ctx.config, logger=ctx.logger, lang_code=lang.code)
      if not wiki.initialize():
        ctx.logger.error(f'Failed to initialize {lang.code} wiki connection')
        return False
      all_wikis.append(wiki)
    source_wiki = next((w for w in all_wikis if w.lang_code == 'en'), None)
    if not source_wiki:
      ctx.logger.error('Source wiki "en" not found')
      return False

    file_list_str = source_wiki.get_page_content('FilesPage')
    if file_list_str is False:
        ctx.logger.error(f'Failed to get content for FilesPage {lang.code}')
        return False
    images_list = file_list_str.split(' ') if file_list_str else []

    match_images_with_heroes(ctx=ctx, images=[{'name': i} for i in images_list if 'Portrait' in i], attribute='wiki')
    for hero in ctx.heroes:
      hero.portrait = f'{hero.name.replace(" ", "_")}_Portrait.png'
      if hero.file.drive and not hero.file.wiki:
        ctx.logger.info(f'---> New file found for {hero.name}')
        file_path = ctx.drive.download_file(hero.file.drive)
        if not file_path:
          return False        
        if not source_wiki.upload_file(filepath=file_path, wiki_filename=hero.portrait):
          return False
        
    match_images_with_pets(ctx=ctx, images=[{'name': i} for i in images_list if 'Portrait' in i], attribute='wiki')
    for pet in ctx.pets:
      pet.portrait = f'{pet.special_art_id if pet.special_art_id else pet.name.replace(" ", "_")}_Portrait.png'
      if pet.file.drive and not pet.file.wiki:
        ctx.logger.info(f'---> New file found for {pet.name}')
        file_path = ctx.drive.download_file(pet.file.drive)
        if not file_path:
          return False        
        if not source_wiki.upload_file(filepath=file_path, wiki_filename=pet.portrait):
          return False

    match_images_with_maps(ctx=ctx, images=[{'name': i} for i in images_list if 'Spire' in i], attribute='wiki_exists')
    for map in ctx.maps:
      for idx, image in enumerate(map.images):
        if len(map.images) == 1:
          should_upload = not image['wiki_exists']
        else:
          should_upload = idx in [1, 2] and not image['wiki_exists']
        if should_upload:
          ctx.logger.info(f'---> New file found for {image['filename']}')
          if not source_wiki.upload_file(filepath=image['filepath'], wiki_filename=image['filename']):
            return False
          
    for grid in ctx.grids:
      ctx.logger.info(f'---> Trying to upload file for {map.name}')
      if not source_wiki.upload_file(filepath=grid.filepath, wiki_filename=grid.filename):
        return False
    
    all_source_files = source_wiki.list_all_images()
    if not all_source_files:
      ctx.logger.error('Failed to retrieve image list from source wiki')
      return False

    for wiki in all_wikis:
      if not wiki.update_files_page(file_list=all_source_files):
        return False
      ctx.logger.info(f'FilesPage updated in {wiki.lang_code} wiki')

    heroes_without_portrait = [h.name for h in ctx.heroes if h.portrait is None]
    if heroes_without_portrait:
      ctx.logger.warning(f'---> Heroes found without portrait : {', '.join(heroes_without_portrait)}')
    pets_without_portrait = [p.name for p in ctx.heroes if p.portrait is None]
    if pets_without_portrait:
      ctx.logger.warning(f'---> Pets found without portrait : {', '.join(pets_without_portrait)}')
    
    return True

def cleanup(ctx: AppContext, args: ArgsClass):
  """ Cleanup before close """
  if ctx.mongodb and not args.no_save:
    ctx.mongodb.close()
  
  for file in os.listdir('temp'):
    file_path = os.path.join('temp', file)
    os.remove(file_path)
    ctx.logger.info(f'{file} removed from /temp')
    

def main():
  """ Main function """
  ctx = AppContext()

  try:
    init_classes(ctx)

    if not load_files(ctx):
      ctx.logger.error('Exit due to failure to load required files')
      sys.exit(1)

    args = parse_arguments(ctx)
    
    if not init_mongodb_connection(ctx, args):
      ctx.logger.error('Exit due to MongoDB connexion failure -> restart with --no_save if it doesn\'t matter ;)')
      sys.exit(1)
    
    if not load_sheets_data(ctx):
      ctx.logger.error('Exit due to failure to load sheet data')
      sys.exit(1)

    if not create_classes_from_heroes(ctx):
      ctx.logger.error('Exit due to failure to create classes objects')
      sys.exit(1)

    if not create_talents_from_heroes(ctx):
      ctx.logger.error('Exit due to failure to create talents objects')
      sys.exit(1)

    if not load_drive_data(ctx, args):
      ctx.logger.error('Exit due to failure to load files from shared drive')
      sys.exit(1)

    if not compare_actual_data_to_stored_data(ctx, args):
      sys.exit(1)
    
    if not generate_pages_contents(ctx, args):
      ctx.logger.error('Exit due to failure to generate pages contents')
      sys.exit(1)
    
    #ctx.generated_pages = [c for c in ctx.generated_pages if c.get('title') == 'Hero Ascend Gain' or c.get('title') == 'Ganancia de ascenso de héroe' or c.get('title') == 'Gain d\'ascension des Héros'] # FOR TESTS

    if not compare_and_update_wiki_pages(ctx, args):
      ctx.logger.error('Exit due to failure to compare and update wiki pages')
      sys.exit(1)

    if not compare_and_update_files(ctx):
      ctx.logger.error('Exit due to failure in files management')
      sys.exit(1)
    
    cleanup(ctx, args)
    ctx.logger.info('Script completed successfully')
  except SystemExit as e:
    return
  except Exception as e:
    if ctx.logger:
      ctx.logger.error(f'Unexpected error: {str(e)}')
    else:
      print(f'Error: {str(e)}')
      sys.exit(1)
    if args is not None:
      cleanup(ctx, args)


if __name__ == '__main__':
  main()