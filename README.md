# fndWikiUpdater
Tool to update Friends & Dragons Wiki

## Quick install: ##
1. clone repo + create your dev environnement (optional)
2. install requirements (pip install -r requirements.txt)
3. create a /cred directory c/p your google api .json file in it (https://developers.google.com/workspace/sheets/api/quickstart/python for more info)
4. rename .env-tpl file to .env and fill it
5. run script (py main.py)

## Command Line Arguments: ##
--no_save : skip mongoDB data storage and backups if you don't want to bother with it  
--force   : force update even if Playsome's data is the same as the one stored in mongoDB

## What does the script step by step: ##
1. first inits all classes
2. connects to mongoDB (skipped with --no_save)
3. loads .yml files :
   - special_heroes.yml -> data to transform Playsome's special recolored heroes and bard talents into their real names
   - events.yml -> data to transform Playsome's exclusivity column into something more readable
   - elements_templates.yml -> list all used templates with different options  
     **/!\ any change on existing templates or new templates should be reported here**
   - pages_templates.yml -> file to store pages templates, which are processed to generate pages contents  
     **/!\ all pages to update should be stored here (to be completed with more pages...)**
4. connects to Google Sheets, reads sheets data and transform it into a list of Hero objects
5. compares sheets data to stored data (skipped with --no_save) and creates a backup db if any new content is found. If nothing has changed, the script stops unless forced to process with --force
6. generates pages contents :
   - loads languages one by one (picked in data/languages/)  
     **/!\ add new .yml files here to translate the wiki in more languages**
   - process pages from pages_templates on by one using the template_processor class  
     **/!\ if any new data is needed in templates/pages, it should be added in class/template_processor.py**
7. connects to the wiki language by language and compare pages content with generated content -> update only if contents are not the same

all of this is logged both in your shell and in a log file

## TODO-LIST: ##
- add other hero pages in pages_templates.yml
- figure out how to automatize files upload from Google Drive (the hard part for me since I never did that before, new challenge !)
- TraitAndPortraitsFiles page update
- add other languages (whichones ?)
- add pet pages / talent pages

