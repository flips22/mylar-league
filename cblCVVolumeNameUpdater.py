# Check CBL files with ComicVine IDs for up-to-date volume names.  Will use cached CV data younger than 30 days.
# By default this will change the cbl files in place.
#
# Can be run against a folder of CBLs recursively, or against individual files
import argparse
import os
from pathlib import Path
import configparser
import time
import traceback
import requests
import json

from xml.etree import ElementTree
import xml.etree.ElementTree as ET


from simyan.comicvine import Comicvine
from simyan.sqlite_cache import SQLiteCache

class CommentedTreeBuilder(ElementTree.TreeBuilder):
    def comment(self, data):
        self.start(ElementTree.Comment, {})
        self.data(data)
        self.end(ElementTree.Comment)

config = configparser.ConfigParser(allow_no_value=True)

if os.path.exists('configPRIVATE.ini'):
    config.read('configPRIVATE.ini')
else:
    config.read('config.ini')

rootDirectory = os.getcwd()
dataDirectory = os.path.join(rootDirectory, "ReadingList-DB")
cvCacheFile = os.path.join(dataDirectory, "CV-VolumeNames.db")

#Mylar prefs
mylarAPI = config['mylar']['mylarapi']
mylarBaseURL = config['mylar']['mylarbaseurl']

mylarVolumeURL = mylarBaseURL + 'api?apikey=' + mylarAPI + '&cmd=getComic&id='

#CV prefs
CACHE_RETENTION_TIME = 30 #days

CV_API_KEY = config['comicVine']['cv_api_key']
#CV_API_RATE = 0.1 #Seconds between CV API calls

def check_file(filePath, save_old=False, use_mylar=False):
    cbl = ET.parse(filePath, parser=ElementTree.XMLParser(target=CommentedTreeBuilder()))
    cbl.getroot().set('xmlns:xsd', "http://www.w3.org/2001/XMLSchema")
    cbl.getroot().set('xmlns:xsi', "http://www.w3.org/2001/XMLSchema-instance")

    books = cbl.findall(".//Book")
    first_entry_database = books[0].find(".//Database[@Name='cv']")
    if first_entry_database is None:
        print(f"{filePath} does not contain cv Database IDs.  No changes made.")
        return
        
    volumes_updated = False
    update_counter = 0
    series_updates = {}
    try:
        cv_session = Comicvine(api_key=CV_API_KEY, cache=SQLiteCache(cvCacheFile,CACHE_RETENTION_TIME))
    except:
        print(f"{filePath} Error creating CV session.  No changes made.")
        return

    try:
        for book in books:
            series_name = book.get("Series")
            cv_series_id = book.find(".//Database[@Name='cv']").get("Series")

            if cv_series_id is None:
                print(f"{filePath} has missing cv Series ID for entry {book}.  No changes made.")
                return
            
            found_volume_in_mylar = False
            if use_mylar:
                volumeURL = f"{mylarVolumeURL}{cv_series_id}"
                mylarData = requests.get(volumeURL).text
                jsonData = json.loads(mylarData)
                #jsonData = mylarData.json()
                mylarComicData = jsonData['data']['comic']
                if len(mylarComicData) > 0:                
                    #print(f"Found volume for ID: {cv_series_id} in Mylar {mylarComicData}")
                    found_volume_in_mylar = True

            if not found_volume_in_mylar:            
                goodResponse = False
                while not goodResponse:
                    goodResponse = True
                    try:
                        response = cv_session.get_volume(cv_series_id)

                    except Exception as e:
                        print(f"=== CV error looking up {cv_series_id}")
                        print(repr(e))
                        goodResponse = False
                        if 'Rate limit exceeded' in repr(e):
                            print('Rate limited sleeping 200 seconds...')
                            time.sleep(200)
                
                current_name = response.name
            else:
                current_name = mylarComicData[0]['name']

            if series_name != current_name:
                book.attrib["Series"] = current_name
                update_counter += 1
                series_updates[series_name] = current_name
            
            #time.sleep(CV_API_RATE)

        # Save the original file, then the updated file
        if update_counter > 0:
            if save_old:
                os.replace(filePath, filePath.with_suffix(".old"))

            cbl.write(filePath, encoding='utf-8', xml_declaration=True)
                                  
            print(f"{filePath} {update_counter} books updated. {series_updates}")
        else:
            print(f"{filePath} No updates needed for file.")
    except Exception as e:
        print(f"{filePath} Error processing.  No updates made.")
        print(traceback.format_exc())
        if book is not None:
            print(f"Last book processed: {ET.tostring(book)}")
        return

                

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='CBL Sanity Checker',
                    description='Reviews Comic Book Lists for potential issues')
    parser.add_argument('target', help='Either a folder containing CBL files or a single CBL file to analyse')
    parser.add_argument('-b', help='If a cbl is updated, save the original file with an .old suffix', action='store_true')
    parser.add_argument('-m', help='Use mylar for a data source (if available)', action='store_true')
    args = parser.parse_args()

    # Handle the awkward issue of the final backslash in a quoted windows path being treated as an escaped quote mark
    if args.target.endswith('"') or args.target.endswith(' '):
        args.target = args.target.strip()
        args.target = args.target.rstrip('"')

    root = Path(args.target)
    
    if not root.exists():
        print(f"Error: {args.target} does not exist")
        exit()

    if root.is_file() :
        check_file(root, save_old = args.b, use_mylar = args.m)
    elif root.is_dir():
        
        cblFiles = root.rglob("*.cbl")

        for cblFile in cblFiles:
            check_file(cblFile, save_old = args.b, use_mylar = args.m)