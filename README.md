# fndWikiUpdater
Tool to update Friends & Dragons Wiki

## Quick install: ##
1. clone repo + create your dev environnement (optional)
2. install requirements (pip install -r requirements.txt)
3.  Go to [console.cloud.google.com](https://console.cloud.google.com/) to set up your API access [see help](https://developers.google.com/workspace/sheets/api/quickstart/python) :
      - create a project
      - activate Sheets and Drive API
      - create access credentials -> [OAuth client ID](https://developers.google.com/workspace/guides/create-credentials#oauth-client-id)
      - download your client_secret***.json file, create a /cred directory in your cloned repo and c/p your .json file in it
4. create a Fandom bot password [see help](https://community.fandom.com/wiki/Help:Bots#Using_Special:BotPasswords)
5. (optional) -> create a MongoDB free cluster to store data and get your cluster connection information [see help](https://www.mongodb.com/docs/atlas/tutorial/connect-to-your-cluster)
6. rename .env-tpl file to .env and fill it
7. run script (py main.py)

## Command Line Arguments: ##
--no_save   : skip mongoDB data storage and backups if you don't want to bother with it  
--force     : force update even if Playsome's data is the same as the one stored in mongoDB
--templates : updates only listed templates. Templates are string, so use double-quote, and you can list any number of templates
--help      : list all of these commands

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
   - /languages -> all translations files (currently en, es, fr)
     **/!\ add new .yml files here to translate the wiki in more languages / if any new content has to be translated, it should be duplicated in every file**
4. connects to Google Sheets :
   - reads Playsome's data and transform it into a list of Hero objects 
   - reads another sheet data and transform it into a list of Pet objects **(ask me if you want access to both sheets)**
   **/!\ If you launch this script for the first time (or if your token has expired), a Google Auth page will open for you to authorize the script**   
6. compares sheets data to stored data (skipped with --no_save) and creates a backup db if any new content is found. If nothing has changed, the script stops unless forced to process with --force
7. process pages from pages_templates one by one using the template_processor class  
   **/!\ if any new data is needed in templates/pages, it should be added in class/display_attributes.py**
8. connects to the wiki language by language and compare pages content with generated content -> update only if contents are not the same
9. connects to Google Drive, checks for new heroes portraits compared to the existing file list in the FilesPage page (used in /Module:Picture for a lot of templates)
   -> if new files are found, download them, upload them to the wiki, update the FilesPage and then delete the temp files

all of this is logged both in your shell and in a log file

## TODO-LIST: ##
- add other hero pages in pages_templates.yml
- add other languages (whichones ?)
- add talent pages

