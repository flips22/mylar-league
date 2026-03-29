import requests
import json
import os
import time
from enum import IntEnum
import xml.etree.ElementTree as ET
from glob import glob
from sys import argv
import numpy as np
import re
from simyan.comicvine import Comicvine
from simyan.cache import SQLiteCache
import configparser
#import xlsxwriter
from PIL import Image
import pandas as pd
import io
import shutil
import sys

import glob
import random
import base64
import pandas as pd

from PIL import Image
from io import BytesIO
from IPython.display import HTML

import unicodedata  # Needed to strip character accents
from datetime import datetime, timedelta
#from datetime import date
#import datetime
import sqlite3


config = configparser.ConfigParser(allow_no_value=True)

if os.path.exists('configPRIVATE.ini'): # an attempt to prevent me from sharing my api keys (again) :)
    config.read('configPRIVATE.ini')
else:
    config.read('config.ini')


### DEV OPTIONS
#Enable verbose output
VERBOSE = True
#Prevent overwriting of main CSV data file
TEST_MODE = False
#searchTruthDB = False
#Change forceCreateCBL to True to create CBL even if there are missing issues.
forceCreateCBL = False


#File prefs
SCRIPT_DIR = os.getcwd()
READINGLIST_DIR = os.path.join(SCRIPT_DIR, "ReadingLists")
DATA_FILE = os.path.join(SCRIPT_DIR, "Wishlist-Output.csv")

IMAGE_DIR = os.path.join(SCRIPT_DIR, "CVCoverImages")


#CV prefs
#CV_SEARCH_LIMIT = 10000 #Maximum allowed number of CV API calls
CACHE_RETENTION_TIME = timedelta(days=180)

CV_API_KEY = config['comicVine']['cv_api_key']
CV_API_RATE = 1 #Seconds between CV API calls
FORCE_RECHECK_CV = False
PUBLISHER_BLACKLIST = ["Panini Comics","Editorial Televisa","Planeta DeAgostini","Unknown","Urban Comics","Dino Comics","Ediciones Zinco","Abril","Panini Verlag","Panini España","Panini France","Panini Brasil","Egmont Polska","ECC Ediciones","RW Edizioni","Titan Comics","Dargaud","Federal", "Marvel UK/Panini UK","Grupo Editorial Vid","JuniorPress BV","Pocket Books", "Caliber Comics", "Panini Comics","Planeta DeAgostini","Newton Comics","Atlas Publishing","Heroic Publishing","TM-Semic"]
PUBLISHER_PREFERRED = ["Marvel","DC Comics","Vertigo"] #If multiple matches found, prefer this result
SERIESID_BLACKLIST = [137835,147775,89852,96070,78862,58231,50923]
SERIESID_GOODLIST = [42722,3824,4975,69322,3816,38005,1628] #index matches above list
#CV = None

dynamicNameTemplate = '[^a-zA-Z0-9]'
stop_words = ['the', 'a', 'and']
yearStringCleanTemplate = '[^0-9]'
#cleanStringTemplate = '[^a-zA-Z0-9\:\-\(\) ]'
#cleanStringTemplate = '[^a-zA-Z0-9:\-\(\) ]'


dfOrderList = ['SeriesName', 'SeriesStartYear', 'IssueNum', 'IssueType', 'CoverDate', 'Name', 'SeriesID', 'IssueID', 'CV Series Name', 'CV Series Year', 'CV Issue Number', 'CV Series Publisher', 'CV Cover Image', 'CV Issue URL', 'Days Between Issues']

r'''

class col(IntEnum):
    # listOrder = 0
    # SeriesName = 1
    # SeriesStartYear = 2
    # IssueNum = 3
    # IssueType = 4
    # CoverDate = 5
    # SeriesID = 6
    # IssueID = 7
    # cvSeriesName = 8
    # csSeriesYear = 9
    # cvCoverImage = 10
    # cvIssueURL = 11
    LISTORDER = 0
    SERIESNAME = 1
    SERIESYEAR = 2
    ISSUENUM = 3
    ISSUETYPE = 4
    COVERDATE = 5
    SERIESID = 6
    ISSUEID = 7
    CVSERIESNAME = 8
    CVSERIESYEAR = 9
    CVCOVERIMAGE = 10
    CVISSUEURL = 11

xlsheader = [
    #header / data field
    "List Order",
    "SeriesName",
    "SeriesStartYear",
    "IssueNum",
    "IssueType", 
    "CoverDate", 
    "SeriesID",
    "IssueID",
    "CV Series Name",
    "CV Series Year",
    "CV Cover Image",
    "CV Issue URL"
]


timeString = time.strftime("%y%m%d%H%M%S")

#File prefs
SCRIPT_DIR = os.getcwd()
RESULTS_DIR = os.path.join(SCRIPT_DIR, "Results")
DATA_DIR = os.path.join(SCRIPT_DIR, "Data")
READINGLIST_DIR = os.path.join(SCRIPT_DIR, "ReadingLists")
DATA_FILE = os.path.join(DATA_DIR, "data.csv")
RESULTS_FILE = os.path.join(RESULTS_DIR, "results-%s.txt" % (timeString))

#Create folders if needed
if not os.path.isdir(DATA_DIR): os.mkdirs(DATA_DIR)
if not os.path.isdir(RESULTS_DIR): os.mkdirs(RESULTS_DIR)
if not os.path.isdir(READINGLIST_DIR): os.mkdirs(READINGLIST_DIR)

OUTPUT_FILE = os.path.join(DATA_DIR, "data-%s.csv" % (timeString))
'''
timeString = datetime.today().strftime("%y%m%d%H%M%S")

rootDirectory = os.getcwd()
#rootDirectory = os.path.dirname(rootDirectory)
dataDirectory = os.path.join(rootDirectory, "ReadingList-DB")
readingListDirectory = os.path.join(rootDirectory, "ReadingList-ImportExport")
resultsDirectory = os.path.join(rootDirectory, "ReadingList-Results")
outputDirectory = os.path.join(rootDirectory, "ReadingList-Output")
#jsonOutputDirectory = os.path.join(outputDirectory, "JSON")
#cblOutputDirectory = os.path.join(outputDirectory, "CBL")
#truthTableDirectory = os.path.join(rootDirectory, "ReadingList-truthDB")
#dataFile = os.path.join(dataDirectory, "data.db")
#cvCacheFile = os.path.join(dataDirectory, "cv.db")
#overridesFile = os.path.join(dataDirectory,'SeriesOverrides.json')
#configFile = os.path.join(rootDirectory, 'config.ini')
resultsFile = os.path.join(resultsDirectory, "results-%s.txt" % (timeString))
problemsFile = os.path.join(resultsDirectory, "problems-%s.txt" % (timeString))
uniqueSeriesFile = os.path.join(resultsDirectory, "uniqueSeriesWarnings-%s.txt" % (timeString))
duplicateIssueFile = os.path.join(resultsDirectory, "duplicateIssuesRemoved-%s.txt" % (timeString))

#truthDB = os.path.join(dataDirectory, "truthDB.db")
#truthDB = os.path.join(dataDirectory, "CBRO.db")
#truthDB = os.path.join(dataDirectory, "x-men.db")
#truthDB = os.path.join(dataDirectory, "CMRO.db")

cvCacheFile = os.path.join(dataDirectory, "CV.db")
#cvCacheFile = os.path.join(dataDirectory, "CV-NEW.db")
#vCacheFile = os.path.join(dataDirectory, "CV-TEMP.db")

localCVdbFile = os.path.join(dataDirectory, "localcv.db")

# inputfile = " ".join(sys.argv[1:])
# #inputfile = '[Marvel] All-New, All Different Marvel- All-New, All-Different Marvel Part #2 (WEB-RIPCBRO).json'
# #inputfile = '[Marvel] Marvel Master Reading Order Part #5 (WEB-RIPCBRO).json'
# #inputfile = '102 One More Day (2007).cbl'
# #inputfile = '[Marvel] Marvel Master Reading Order Part #2 (WEB-RIPCBRO).json'
# #inputfile = '[Marvel] Infinity Gauntlet (WEB-CMROLIST).json'
# outputfile = inputfile.strip('.json') + '-USER.xlsx'
# outputcsvfile = inputfile.strip('.json') + '-USER.csv'
# outputhtmlfile = inputfile.strip('.json') + '-USER.html'
# print(inputfile)
# print(outputfile)
# if os.path.exists(outputfile):
#     firstRun = False
#     print('Not First Run')

# else:
#     firstRun = True
#     print('First Run')
try:
    # 1. Open the connection ONCE at the start
    conn = sqlite3.connect(localCVdbFile)
    cursor = conn.cursor()
    print("Connected to local CV Cache DB")
except sqlite3.Error as error:
        print("Error while connecting to localCV Cache", error)

def main():
    checkDirectories()
    summaryResults = []
    problemResults = []
    uniqueSeriesWarnings = []
    uniqueSeriesWarnings.append('Found series with the same title and different Series IDs:\n')
    global duplicateIssues
    duplicateIssues = []
    
    try:
        # 1. Open the connection ONCE at the start
        conn = sqlite3.connect(localCVdbFile)
        cursor = conn.cursor()
        print("Connected to local CV Cache DB")
    except sqlite3.Error as error:
            print("Error while connecting to localCV Cache", error)
    r'''
    try:
        sqliteConnection = sqlite3.connect(truthDB,detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = sqliteConnection.cursor()
        #print("Database created and Successfully Connected to SQLite")

        # sqlite_select_Query = "select sqlite_version();"
        # cursor.execute(sqlite_select_Query)
        # record = cursor.fetchall()
        # print("SQLite Database Version is: ", record)
        # df = pd.read_sql_query("SELECT * from comics", sqliteConnection)
        # df=df.fillna({'year':0, 'issue':0}).astype({'year':int})
        # rows = cursor.execute(
        # "SELECT * FROM comics WHERE SeriesName = ? AND IssueNum = ?",
        # ('Action Comics','1'),
        # ).fetchall()
        # #print(rows)
        # print(rows[0][0])
        # cursor.close()

    except sqlite3.Error as error:
        print("Error while connecting to sqlite", error)
    
    '''


    #readingLists = []
    fileCount = 0
    for root, dirs, files in os.walk(readingListDirectory):
        for file in files:
            if file.endswith(".cbl") or file.endswith(".ccc") or file.endswith(".xlsx"):#file.endswith(".json") or 
                inputfile = file
                print('Processing %s'%(inputfile))
                #if file.endswith(".json"):
                    #outputfile = os.path.join(readingListDirectory, inputfile.replace('.json','') + '.xlsx')
                    #outputcsvfile = os.path.join(readingListDirectory, inputfile.replace('.json','') + '.csv')
                    #outputhtmlfile = os.path.join(readingListDirectory, inputfile.replace('.json','') + '.html')
                    #outputcblfile = os.path.join(outputDirectory, inputfile.replace('.json','') + '.cbl')
                if file.endswith(".cbl"):
                    outputfile = os.path.join(readingListDirectory, inputfile.replace('.cbl','') + '.xlsx')
                    outputcsvfile = os.path.join(readingListDirectory, inputfile.replace('.cbl','') + '.csv')
                    outputhtmlfile = os.path.join(readingListDirectory, inputfile.replace('.cbl','') + '.html')
                    outputcblfile = os.path.join(outputDirectory, inputfile.replace('.cbl','') + '.cbl')
                if file.endswith(".ccc"):
                    outputfile = os.path.join(readingListDirectory, inputfile.replace('.ccc','') + '.xlsx')
                    outputcsvfile = os.path.join(readingListDirectory, inputfile.replace('.ccc','') + '.csv')
                    outputhtmlfile = os.path.join(readingListDirectory, inputfile.replace('.ccc','') + '.html')
                    outputcblfile = os.path.join(outputDirectory, inputfile.replace('.ccc','') + '.cbl')
                if file.endswith(".xlsx"):
                    outputfile = os.path.join(readingListDirectory, inputfile)
                    outputcsvfile = os.path.join(readingListDirectory, inputfile.replace('.xlsx','') + '.csv')
                    outputhtmlfile = os.path.join(readingListDirectory, inputfile.replace('.xlsx','') + '.html')
                    outputcblfile = os.path.join(outputDirectory, inputfile.replace('.xlsx','') + '.cbl')

                inputfile = os.path.join(readingListDirectory, inputfile)
                #Get year range from file name
                # Example string

                # Extract years from the string
                global seriesNotFoundList
                seriesNotFoundList = []
                global year1
                global year2
                year1, year2 = extract_years_from_filename(inputfile)
                #print (year1)
                #print (year2)

                if int(year1) > 0 and int(year2) > 0:
                
                    year1 = int(year1) -1
                    year2 = int(year2) +1
                    print(f"     If no date is in defined, the year range for searching will be: {year1} to {year2}")
                else:
                    print(f"     Year range was not found in file name. Continuing...")
                    


                
                if os.path.exists(outputfile):
                    firstRun = False
                    #will also not be first run if xlsx is input file.
                    #print('Previous run detected')

                else:
                    firstRun = True

                    #print('First run for this file')




                fileCount += 1

                if firstRun and inputfile.endswith(".json"):
                    df = importJSON(inputfile)
                    
                elif firstRun and inputfile.endswith(".cbl"):
                    df = importCBL(inputfile)

                elif firstRun and inputfile.endswith(".ccc"):
                    df = importCCC(inputfile)
                    
                else:
                    df = importXLSX(outputfile)
                    df.index = np.arange(1, len(df) + 1)
                


                #df = df.reset_index()
                for index, row in df.iterrows():
                    #print(index)
                    seriesName = row['SeriesName']
                    seriesStartYear = row['SeriesStartYear']
                    dbissueNum = row['IssueNum']
                    issueNum = row['CV Issue Number']
                    if isinstance(issueNum, float):
                        issueNum = f'{issueNum:g}'
                    #issueNum = f'{float(issueNum):g}'
                    #issueNum = int(issueNum)
                    issueType = row['IssueType']
                    coverDate = row['CoverDate']
                    seriesID = row['SeriesID']
                    issueID = row['IssueID']
                    cvSeriesName = row['CV Series Name']
                    cvSeriesYear = row['CV Series Year']
                    cvIssueNum = row['CV Issue Number']
                    if isinstance(cvIssueNum, float):
                        cvIssueNum = f'{cvIssueNum:g}'
                    try:
                        cvSeriesPublisher = row['CV Series Publisher']
                    except:
                        cvSeriesPublisher = ''
                        #continue
                    cvIssueURL = row['CV Issue URL']
                    coverImage = row['CV Cover Image']
                    #print(seriesID)
                    if (df['SeriesID'] == 0).all():
                        firstRun = True

                    
                    r'''
                    #if sqliteConnection:
                    if sqliteConnection and searchTruthDB and issueID == 0:# and firstRun:
                    
                        try:
                            #truthMatch = cursor.execute(
                            #"SELECT * FROM comics WHERE SeriesName = ? AND SeriesStartYear = ? AND IssueNum = ? AND ReadingList = ?",
                            #(seriesName,seriesStartYear,dbissueNum,file),
                            #).fetchall()
                            truthMatch = cursor.execute(
                            "SELECT * FROM comics WHERE SeriesName = ? AND SeriesStartYear = ? AND IssueNum = ?",
                            (seriesName,seriesStartYear,dbissueNum),
                            ).fetchall()
                            
                            
                            
                            #'Action Comics', 1938, '1', 'Issue', '1938-06-30 00:00:00', 'Comicvine', 18005, 105403, 'Action Comics', 1938, ' ', 'https://comicvine.gamespot.com/issue/4000-105403/', 153, '1')
                            #coverDate = truthMatch[0][4]
                            print('Match found in truth table')
                            
                            #print(truthMatch)
                            seriesID = truthMatch[0][6]
                            issueID = truthMatch[0][7]
                            cvSeriesName = truthMatch[0][8]
                            cvSeriesYear = truthMatch[0][9]
                            issueNum = truthMatch[0][10]
                            cvIssueURL = truthMatch[0][13]
                            cvSeriesPublisher = truthMatch[0][11]
                            # try:
                            #     cvSeriesPublisher = truthMatch[0][11]
                            # except:
                            #     cvSeriesPublisher = ''
                        except:
                            print('No match found in truth table, trying only series and year')
                            
                            try:
                                truthMatch = cursor.execute(
                                "SELECT * FROM comics WHERE SeriesName = ? AND SeriesStartYear = ?",
                                (seriesName,seriesStartYear),
                                ).fetchall()
                                #'Action Comics', 1938, '1', 'Issue', '1938-06-30 00:00:00', 'Comicvine', 18005, 105403, 'Action Comics', 1938, ' ', 'https://comicvine.gamespot.com/issue/4000-105403/', 153, '1')
                                #coverDate = truthMatch[0][4]
                                #print(truthMatch)
                                seriesID = truthMatch[0][6]
                                
                            except:
                                print('No match found in truth table')
                        '''
                        
                    if issueNum == '' or issueNum == 'nan':
                        issueNum = dbissueNum

                    if seriesStartYear == 0:

                        #print(f"Checking {seriesName} #{issueNum}...")
                        pass
                    else:
                        #print(f"Checking {seriesName} ({seriesStartYear}) #{issueNum}...")
                        pass

                    #if isinstance(coverDate, str):
                        #print('coveDate is a string')

                    if isinstance(seriesID,int) and not seriesID == 0:
                        seriesIDPres = True
                    else:
                        seriesIDPres = False
                    
                    if isinstance(issueID,int) and not issueID == 0:
                        issueIDPres = True
                    else:
                        issueIDPres = False

                    if cvIssueURL == '' or coverImage == '' or coverDate == '' or isinstance(coverDate, str) or isinstance(coverDate, int) or cvIssueNum =='nan' or cvIssueNum == '':
                        missingIssueDetails = True
                    else:
                        missingIssueDetails = False
                    
                    if cvSeriesName == '' or cvSeriesYear =='' or cvSeriesPublisher == '':
                        missingSeriesDetails = True
                    else:
                        missingSeriesDetails = False
                    if issueIDPres and not seriesIDPres:
                        print('     Searching for series id from issueid')

                        seriesID = getSeriesIDfromIssue(issueID)
                        if not seriesID == 0:
                            seriesIDPres = True
                        #seriesID = seriesIDList[0]
                    validYear = is_valid_year(seriesStartYear)
                    if not seriesIDPres and not issueIDPres:
                        if validYear:
                            volumeresults = findVolume(seriesName,seriesStartYear)
                            print(f"Seaching for match using series and year...")
                            print(seriesID)
                            

                            if not volumeresults[1] == 0:
                                seriesID = volumeresults[1]
                                seriesIDPres = True
                            
                        if not validYear and not year1 == 0:
                            #try:

                                #seriesSearch = df.loc[df['SeriesName'] == seriesName, 'SeriesID'].values[0]# or .item()
                            #seriesSearch = df.query("SeriesName==seriesName")["SeriesID"]
                            
                            #print(f"     Checking if series name was searched for previously")

                            if seriesName in seriesNotFoundList:
                                print(f"     Searched for series previously and wasn't found, skipping...")
                            else:
                                    

                                seriesSearch = df.loc[(df['SeriesName'] == seriesName,'SeriesID')].values[0]
                                #print('seriesSearch: ' + str(seriesSearch))
                                
                                if not seriesSearch == 0:
                                #    
                                    seriesID = seriesSearch
                                    seriesIDPres = True
                                    print(f"     Found series ID ({seriesSearch}) in previous search...")
                                else:
                                    print(f"     Searching for match using series and year range...")
                                    volumeresults = findVolumeNoYear(seriesName, issueNum)
                                    
                                    
                                    #print(seriesID)
                                    if not volumeresults[1] == 0:
                                        seriesIDPres = True
                                        seriesID = volumeresults[1]
                                        print(f"     Found matching series id: {seriesID}")
                                    if not volumeresults[2] == 0:
                                        issueIDPres = True
                                        issueID = volumeresults[2]
                                        print(f"     Found matching issue ID: {issueID}")
                            
                            
                    # if seriesIDPres:
                    #     imageFileName = str(issueID) + '.jpg'
                    #     imageFilePath = os.path.join(IMAGE_DIR, imageFileName)
                    #     if not os.path.exists(imageFilePath): 
                    #         cvIssueDetails = getIssueDetails(issueID)
                    #         cvImageURL = cvIssueDetails[0]
                    #         cvIssueURL = cvIssueDetails[1]
                    #         coverDate = cvIssueDetails[2]
                    #         if not cvImageURL == '':
                    #             try:
                    #                 imageFilePath = getcvimage(issueID,cvImageURL)
                    #                 coverImage = get_thumbnail(imageFilePath)
                    #                 coverImage = image_formatter(imageFilePath)
                    #                 #print(imageFilePath)
                    #             except:
                    #                 print('Not able to load issueID image from %s'%(imageFilePath))

                    # if seriesIDPres:     #acting strange
                    #     if seriesID in SERIESID_BLACKLIST:
                    #         print('SeriesID in Blacklist replacing....')
                    #         index = SERIESID_BLACKLIST.index(seriesID)
                    #         print(seriesID)
                    #         print('to:')
                    #         seriesID = SERIESID_GOODLIST[index]
                    #         print(seriesID)
                    #         volumedetails = getVolumeDetails(seriesID)
                    #         cvSeriesName = volumedetails[0]
                    #         cvSeriesYear = volumedetails[1]
                    #         df.loc[df['SeriesID'] == seriesID, 'CV Series Name'] = cvSeriesName #testing
                    #         df.loc[df['SeriesID'] == seriesID, 'CV Series Year'] = cvSeriesYear
                            


                    if seriesIDPres and missingSeriesDetails:

                        volumedetails = getVolumeDetails(seriesID)
                        #print (volumedetails)
                        cvSeriesName = volumedetails[0]
                        cvSeriesYear = volumedetails[1]
                        cvSeriesPublisher = volumedetails[2]
                        df.loc[df['SeriesID'] == seriesID, 'CV Series Name'] = cvSeriesName #testing
                        df.loc[df['SeriesID'] == seriesID, 'CV Series Year'] = cvSeriesYear
                        df.loc[df['SeriesID'] == seriesID, 'CV Series Publisher'] = cvSeriesPublisher
                        
                    
                    if seriesIDPres and not issueIDPres:
            
                        cvIssueFind = findIssueID(seriesID,issueNum)
                        issueID = cvIssueFind
                        if issueID == 0:

                            print('     Could not find issue: %s from %s' % (issueNum,seriesID))
                    
                        if not issueID == 0:
                            
                            cvIssueDetails = getIssueDetails(issueID)
                            cvImageURL = cvIssueDetails[0]
                            cvIssueURL = cvIssueDetails[1]
                            coverDate = cvIssueDetails[2]
                            cvIssueNum = cvIssueDetails[3]
                            #if not cvImageURL == '':
                            #    try:
                            #        imageFilePath = getcvimage(issueID,cvImageURL)
                            #        coverImage = get_thumbnail(imageFilePath)
                            #        coverImage = image_formatter(imageFilePath)
                            #        #print(imageFilePath)
                            #    except:
                            #        print('Not able to load issueID image from %s'%(imageFilePath))
                    if issueIDPres:# and 'google' in cvIssueURL:
                        cvIssueURL = 'https://comicvine.gamespot.com/issue/4000-' + str(issueID) + '/'

                    if issueIDPres and missingIssueDetails:
                        cvIssueDetails = getIssueDetails(issueID)
                        cvImageURL = cvIssueDetails[0]
                        cvIssueURL = cvIssueDetails[1]
                        coverDate = cvIssueDetails[2]
                        cvIssueNum = cvIssueDetails[3]
                        #if not cvImageURL == '':
                        #    try:
                        #        imageFilePath = getcvimage(issueID,cvImageURL)
                        #        coverImage = get_thumbnail(imageFilePath)
                        #        coverImage = image_formatter(imageFilePath)
                        #    except:
                        #        print('Not able to load issueID image from %s'%(imageFilePath))
                    r'''
                    if issueIDPres and coverImage == ' ':
                        imageFileName = str(issueID) + '.jpg'
                        imageFilePath = os.path.join(IMAGE_DIR, imageFileName)
                        #print(imageFilePath)
                        if os.path.exists(imageFilePath):
                            try: 
                                coverImage = get_thumbnail(imageFilePath)
                                coverImage = image_formatter(imageFilePath)
                                #print('image exists')
                            except:
                                print('Not able to load issueID image from %s'%(imageFilePath))
                        else:
                            try: 
                                cvIssueDetails = getIssueDetails(issueID)
                                cvImageURL = cvIssueDetails[0]
                                cvIssueURL = cvIssueDetails[1]
                                coverDate = cvIssueDetails[2]
                                cvIssueNum = cvIssueDetails[3]
                                imageFilePath = getcvimage(issueID,cvImageURL)
                                print('image doesnt exist')
                                coverImage = get_thumbnail(imageFilePath)
                                coverImage = image_formatter(imageFilePath)
                                
                            except:
                                print('Not able to load issueID image from %s'%(imageFilePath))
                    '''
                    if not issueIDPres:
                        #print(str(seriesStartYear))
                        #cvIssueURL = searchCV(seriesName,seriesStartYear)
                        #cvIssueURL = ('https://www.google.com/search?q=' + str(seriesName) + '+' + str(seriesStartYear) + '+comicvine').replace(" ", "%20")
                        cvIssueURL = ('https://comicvine.gamespot.com/search/?i=volume&q=' + str(seriesName) + '+' + str(seriesStartYear)).replace(' &', '+%26').replace(" ", "+")
                    dateDelta = pd.to_timedelta(0, unit='D')#pd.Timedelta(0)#
                    if index == 0:
                        dateDelta = pd.to_timedelta(0, unit='D')#pd.Timedelta(0)#
                    indexbefore = index + 1
                    try:
                        coverDateAbove = (df.iloc[index]['CoverDate'])
                    except:
                        print('Possible date issue, moving along...')
                        #continue
                    if not coverDate == pd.NaT and not coverDateAbove == pd.NaT:

                        #dateDelta = daysBetween(coverDate,coverDateAbove)
                        try:
                            #dateDelta = abs(coverDate - coverDateAbove)
                            dateDelta = coverDateAbove - coverDate
                            if dateDelta == 0:
                               dateDelta = pd.NaT

                            #print(coverDateAbove)
                            #print(coverDate)
                        #     #print(dateDelta)
                        except:
                            print('Possible date issue, moving along...')
                            #continue
                    
                    #print('     Found issueid: %s'%(str(issueID)))
                    df.loc[index, 'CoverDate'] = pd.to_datetime(coverDate)
                    df.loc[index,'IssueID'] = issueID
                    df.loc[index,'CV Series Name'] = cvSeriesName
                    df.loc[index,'CV Series Year'] = cvSeriesYear
                    df.loc[index,'CV Issue Number'] = cvIssueNum
                    df.loc[index,'CV Series Publisher'] = cvSeriesPublisher
                    df.loc[index,'CV Issue URL'] = cvIssueURL
                    df.loc[index,'CV Cover Image'] = coverImage
                    df.loc[index,'IssueType'] = 'Issue' # everything's an issue?
                    df.loc[index,'Name'] = 'Comicvine'
                    df.loc[index,'SeriesID'] = seriesID
                    df = df.astype({'Days Between Issues':'timedelta64[ns]'})
                    df.loc[index,'Days Between Issues'] = dateDelta
                    
                    # clear variables
                    coverDate = ''
                    issueID = 0
                    cvSeriesName = ''
                    cvSeriesYear = ''
                    cvIssueURL = ''
                    coverImage = ''
                    cvSeriesPublisher = ''
                    #issueType = ''
                    seriesID = 0
                    dateDelta = pd.to_timedelta(0, unit='D')#pd.Timedelta(0)#




                #df=df.drop('Name',axis='columns')
                #df=df.drop('IssueType',axis='columns')
                #df.to_excel(outputfile)
                #df = df.style.format({'CV Issue URL': make_clickable})
                #df = df.style.highlight_null(null_color="red")


            #df.style.applymap(color_cells, subset=['total_amt_usd_diff','total_amt_usd_pct_diff'])
                #df['CoverDate'] = pd.to_datetime(df['CoverDate'], errors='coerce').dt.date()
                
                numIssueFound = len(df[df['IssueID']>0])
                numIssueTotal = len(df['IssueID'])
                numIssueMissing = numIssueTotal - numIssueFound
                try:
                    maxDays = df['Days Between Issues'].max()
                    minDays = df['Days Between Issues'].min()
                    maxAbsDays = max(abs(maxDays),abs(minDays))
                    
                except:
                    maxAbsDays = 'Unknown'
                summaryString = 'Reading list has ' + str(numIssueMissing) + ' unidentified issues out of ' + str(numIssueTotal) + ' total issues. Maximum days between consecutive issues: ' + str(maxAbsDays)
                
                # if numIssueMissing == 0:
                #     cblData = getCBLData(df,inputfile,numIssueFound)
                #     with open(outputcblfile, 'w') as f:
                #         f.writelines(cblData)
                


                uniqueSeriesList = df.SeriesName.unique()


                for uniqueseries in uniqueSeriesList:
                    seriestemp = df.loc[(df['SeriesName'] == uniqueseries)]
                    if not len(seriestemp) == 0:
                        if len(seriestemp.SeriesID.unique()) > 1:
                            print('Found possible TPB, logging....')
                            print(len(seriestemp.SeriesID.unique()))
                            #print(uniqueseries)
                            uniqueSeriesWarnings.append('\n' + outputfile + '\n     ' + uniqueseries + '\n          ' + str(seriestemp.SeriesID.unique()) + '\n['+str(seriestemp.IssueNum)+']\n')
       

                df['CV Series Name'] = df['CV Series Name'].str.strip()
                #.set_caption(summaryString)
                df = df[dfOrderList]
                dfe = df
                df = df.style.set_table_styles(
                [{"selector": "", "props": [("border", "1px solid grey")]},
                {"selector": "tbody td", "props": [("border", "1px solid grey")]},
                {"selector": "th", "props": [("border", "1px solid grey")]}
                ]).set_caption(summaryString).map(color_cels).format({'CV Issue URL': make_clickable})#.to_html(outputhtmlfile)#,formatters={'CV Cover Image': image_formatter}, escape=False)
                df.to_html(outputhtmlfile)
            #FIX    dfe['CoverDate'] = pd.to_datetime(dfe['CoverDate']).dt.date
                dfe['CV Cover Image'] = ' '
                dfe.to_csv(outputcsvfile)
                dfe = dfe.style.set_table_styles(
                [{"selector": "", "props": [("border", "1px solid grey")]},
                {"selector": "tbody td", "props": [("border", "1px solid grey")]},
                {"selector": "th", "props": [("border", "1px solid grey")]}
                ]).map(color_cels).format({'CV Issue URL': make_clickable})#.to_html(outputhtmlfile)#,formatters={'CV Cover Image': image_formatter}, escape=False)
                dfe.to_excel(outputfile)
                
                print(outputfile)
                print(summaryString)
                summaryResults.append(inputfile + '\n' + outputfile + '\n' + summaryString + '\n')
                if not numIssueMissing == 0:
                    problemResults.append(inputfile + '\n' + outputfile + '\n' + summaryString + '\n')
                if numIssueMissing == 0 or forceCreateCBL:
                    try:
                        print(inputfile)
                        cblName = str(file).replace(readingListDirectory,'').replace('.json','').replace('.cbl','').replace('.ccc','').replace('.xlsx','').strip('\\')
                        print(cblName)
                        cblData = getCBLData(df.data,cblName,numIssueFound)
                        with open(outputcblfile, 'w', encoding='utf-8') as f:
                            f.writelines(cblData)
                    except:
                        problemResults.append('\n     -- CBL Export Failed --    ' + inputfile + '\n' + outputfile + '\n' + '\n')
                    # cblData = getCBLData(df.data,inputfile,numIssueFound)
                    # with open(outputcblfile, 'w') as f:
                    #     f.writelines(cblData)
    r'''
    if sqliteConnection:
        cursor.close()
        sqliteConnection.close()
        print("The truthDB connection is closed")
    if conn:
        cursor.close()
        conn.close()
        print("Local CV DB connection is closed.")
    '''                
                
    with open(resultsFile, 'w', encoding='utf-8') as f:
        f.writelines(summaryResults)
    with open(problemsFile, 'w', encoding='utf-8') as f:
        f.writelines(problemResults)
    with open(uniqueSeriesFile, 'w', encoding='utf-8') as f:
        f.writelines(uniqueSeriesWarnings)
    with open(duplicateIssueFile, 'w', encoding='utf-8') as f:
        f.writelines(duplicateIssues)
        
    
    return

def extract_years_from_filename(filename):
    # Define the regular expression pattern to find years in the string with brackets
    year1 = 1930
    year2 = 2026
    #patternYearFileName = r'\[(\d{4})\s*-\s*(\d{4})\]'  # Matches years in the format [YYYY - YYYY]
    #patternYearFileName = r'(\d{4} - \d{4})|([0-9]{4} - Present)|(\d{4})'

    # Find all matches of the pattern in the input string
    #matches = re.findall(patternYearFileName, filename)
    #yearRangeMatch =  re.findall(r'\[(\d{4}-\d{4})\]', filename)
    yearRangeMatch =  re.findall(r'(\d{4}-\d{4})', filename)

    yearRangeMatchPresent = re.findall(r'\[(\d{4}-Present)\]|\((\d{4}-Present)\)', filename, re.IGNORECASE)
    #yearRangeMatchSingleYear = re.findall(r'\[(\d{4})\]', filename)
    yearRangeMatchSingleYear = re.findall(r'\[(\d{4})\]|\((\d{4})\)',filename)
    #if re.match(r'\[(\d{4}-\d{4})\]', filename):
    if yearRangeMatch:
        print(f"     Found date range.")
        #year1year2Pattern = r'\[(\d{4})-(\d{4})\]'
        year1year2Pattern = r'(\d{4})-(\d{4})'
        
        yearRange = re.findall(year1year2Pattern, filename)
        year1 = yearRange[0][0]
        year2 = yearRange[0][1]
        # Do something specific for date range like storing or processing
    elif yearRangeMatchPresent:
        print(f"     Found 'Present' date range.")
        year1year2Pattern = r'\[(\d{4})-Present'
        yearRange = re.findall(year1year2Pattern, filename)
        year1 = yearRange[0]
        year2 = datetime.now().year
        # Handle the case when 'Present' is matched
    elif yearRangeMatchSingleYear:
        print(f"     Found single year match")
        year1year2Pattern = r'\d{4}'
        yearRange = re.findall(year1year2Pattern, filename)
        year1 = yearRange[0]
        year2 = yearRange[0]
        # Handle the case when only a single year is matched






    '''
    if matches:
        # Extract years from the matched pattern groups
        year1 = matches.group(1)
        year2 = matches.group(2)
        print(filename)
        print(year1)
        print(year2)
    '''
    return year1, year2
    

def checkDirectories():

    directories = [
        dataDirectory,
        readingListDirectory,
        resultsDirectory,
        outputDirectory,
        IMAGE_DIR,
        #jsonOutputDirectory,
        #cblOutputDirectory
        ]

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)



def importJSON(inputfile):
    print(inputfile)
    with open(inputfile) as json_file:
        data = json.load(json_file)
    
    issue_data = data['Issues']

    dfo = pd.DataFrame.from_dict(data['Issues'], orient='index')#, columns=columns)
    dfo.reset_index(drop=True, inplace=True)
    df = dfo.join(pd.json_normalize(dfo['Database']))#.drop('Database', axis='columns')
    df = df.join(pd.json_normalize(df['Name'])).fillna(0)#, inplace=True)
    
    df.reset_index(drop=True, inplace=True)
    #print(df)
    rowlist = df['Database'].values.tolist()
    for i in range(len(rowlist)):
        y = i+1
        df.loc[i,'Name'] = rowlist[i]['Name']
        if rowlist[i]['SeriesID'] == None or rowlist[i]['SeriesID'] == '':
            rowlist[i]['SeriesID'] = 0
        
        if rowlist[i]['IssueID'] == None or rowlist[i]['IssueID'] == '':
            rowlist[i]['IssueID'] = 0
  
        
        df.loc[i,'SeriesID'] = rowlist[i]['SeriesID']
        df.loc[i,'IssueID'] = rowlist[i]['IssueID']
        
        #print(rowlist[i]['IssueID'])
        #print(df[i, 'IssueID'])
        df.fillna({'SeriesID':0, 'IssueID':0}, inplace=True)
        #df = df.astype({'SeriesID':float,'IssueID':float}).astype({'SeriesID':int,'IssueID':int})#.fillna(0)#,errors='ignore')#.fillna(0)#,'IssueID':'int'})
        df = df.astype({'SeriesID':int,'IssueID':int})#.fillna(0)#,errprint\([A-Z].*ors='ignore')#.fillna(0)#,'IssueID':'int'})


    df = df.drop('Database', axis='columns')

    df['CV Series Name'] = ''
    df['CV Series Year'] = ''
    df['CV Issue Number'] = df['IssueNum']
    df['CV Series Publisher'] = ''
    df['CV Cover Image'] = ''
    df['CV Issue URL'] = ''

    return(df)


def importCBL(inputfile):
    bookList = []
    
    # print("Checking CBL files in %s" % (READINGLIST_DIR),2)
    # for root, dirs, files in os.walk(READINGLIST_DIR):
    #     for file in files:
    #         if file.endswith(".cbl"):
    #             try:
    #                 filename = os.path.join(root, file)
    #                 #print("Parsing %s" % (filename))
    #                 tree = ET.parse(filename)
    #                 fileroot = tree.getroot()

    #                 cblinput = fileroot.findall("./Books/Book")
    #                 for entry in cblinput:
    #                     book = {'seriesName':entry.attrib['Series'],'seriesYear':entry.attrib['Volume'],'issueNumber':entry.attrib['Number']}#,'issueYear':entry.attrib['Year']}
    #                     bookList.append(book)
    #             except Exception as e:
    #                 print("Unable to process file at %s" % ( os.path.join(str(root), str(file)) ),3)
    #                 print(repr(e),3)


    try:
        tree = ET.parse(inputfile)
        fileroot = tree.getroot()

        cblinput = fileroot.findall("./Books/Book")
    
        for entry in cblinput:
            try:
                book = {'seriesName':entry.attrib['Series'],'seriesYear':entry.attrib['Volume'],'issueNumber':entry.attrib['Number'], 'seriesID':entry[0].attrib['Series'], 'issueID':entry[0].attrib['Issue']}#,'issueYear':entry.attrib['Year']}

            except:
                book = {'seriesName':entry.attrib['Series'],'seriesYear':entry.attrib['Volume'],'issueNumber':entry.attrib['Number'], 'issueID':0, 'seriesID':0}#,'issueYear':entry.attrib['Year']}
            bookList.append(book)
    except Exception as e:
        print("Unable to process file at %s" % (str(inputfile)))
        print(repr(e))
        



    #bookSet = set()
    finalBookList = []

    for book in bookList:
        curSeriesName = book['seriesName']
        curSeriesYear = book['seriesYear']
        curIssueNumber = book['issueNumber']
        curSeriesID = book['seriesID']
        curIssueID = book['issueID']

        #bookSet.add((curSeriesName,curSeriesYear,curIssueNumber))
        finalBookList.append([curSeriesName,curSeriesYear,curIssueNumber,curSeriesID, curIssueID])
    #df = pd.DataFrame(bookSet, columns =['seriesName', 'seriesYear', 'issueNumber'])
    df = pd.DataFrame(finalBookList, columns =['seriesName', 'seriesYear', 'issueNumber', 'seriesID', 'issueID'])
    
    #print(df)
    



    # print(bookSet)
    
    # #Iterate through unique list of series
    # if VERBOSE: print('Compiling set of issueNumbers from CBLs',2)
    # for series in bookSet:
    #     curSeriesName = series[0]
    #     curSeriesYear = series[1]
    #     curSeriesIssues = []
    #     #Check every book for matches with series
    #     for book in bookList:
    #         if book['seriesName'] == curSeriesName and book['seriesYear'] == curSeriesYear:
    #             #Book matches current series! Add issueNumber to list
    #             curSeriesIssues.append({'issueNumber':book['issueNumber'],'issueID':"Unknown"})


    #     finalBookList.append({'seriesName':curSeriesName,'seriesYear':curSeriesYear,'issueNumberList':curSeriesIssues})

    # print(finalBookList[1]['issueNumberList'])
    # #print(type(finalBookList[1]['issueNumberList'][issueID]))
    # issuedict = finalBookList[1]['issueNumberList']
    # print(issuedict[issueID])
    
    # #print(finalBookList)
    # #print(type(finalBookList))
    # df = pd.DataFrame(finalBookList, columns =['seriesName', 'seriesYear', 'issueNumberList'])
    # #df = pd.DataFrame(finalBookList['issueNumberList'], columns =['issueNumber', 'fissueID'])
    
    # #df = pd.DataFrame(finalBookList, columns =['SeriesName', 'SeriesStartYear', 'IssueNum'])
    # #print(df['issueNumberList'].values.tolist())

    # #print(finalBookList[0]['issueNumberList']['issueNumber'])
    # #rowlist = 
    # #print(rowlist['issueID'])
    # #print(rowlist[2]['issueNumberList'])
    # #print(len(finalBookList))
    # for i in range(len(finalBookList)):
    #     # y = i+1
    #     # #df.loc[i,'issueNumberList'] = rowlist[i]['issueNumberList']
    #     # if finalBookList[i]['issueNumberList'] == None or finalBookList[i]['issueNumberList'] == '':
    #     #     finalBookList[i]['issueNumberList'] = 0
        
    #     # if rowlist[i]['issueID'] == None or rowlist[i]['issueID'] == '':
    #     #     rowlist[i]['issueID'] = 0
  
    #     #print(finalBookList[i]['issueNumberList'][0])
    #     #print(finalBookList[i]['issueNumberList'][1])
    #     df.loc[i,'issueNumber'] = finalBookList[i]['issueNumberList'][0]
    #     df.loc[i,'issueID'] = finalBookList[i]['issueNumberList'][1]
        
    #     #print(rowlist[i]['IssueID'])
    #     #print(df[i, 'IssueID'])
    #     ###df.fillna({'issueNumber':0, 'issueID':0}, inplace=True)
    #     #df = df.astype({'SeriesID':float,'IssueID':float}).astype({'SeriesID':int,'IssueID':int})#.fillna(0)#,errors='ignore')#.fillna(0)#,'IssueID':'int'})
    #     ###df = df.astype({'issueNumber':int,'issueID':int})#.fillna(0)#,errors='ignore')#.fillna(0)#,'IssueID':'int'})


    # df = df.drop('issueNumberList', axis='columns')

    # print(df)
    #df['issueID'] = 0
    df.fillna({'issueNumber':0, 'issueID':0}, inplace=True)
    df = df.astype({'issueNumber':str, 'seriesID':int,'issueID':int})#.fillna(0)#,errors='ignore')#.fillna(0)#,'IssueID':'int'})


    df.rename(columns={'seriesName': 'SeriesName', 'seriesYear': 'SeriesStartYear', 'issueNumber': 'IssueNum', 'issueID':'IssueID','seriesID':'SeriesID'}, inplace=True)




    df['IssueType'] = ''
    df['CoverDate'] = ''
    df['Name'] = ''
    #df['SeriesID'] = ''
    #df['IssueID'] = ''
    df['CV Series Name'] = ''
    df['CV Series Year'] = ''
    df['CV Issue Number'] = df['IssueNum']
    df['CV Issue Number'] = ''

    df['CV Series Publisher'] = ''
    df['CV Cover Image'] = ''
    df['CV Issue URL'] = ''
    df['Days Between Issues'] = ''
    #print(df)
    #df = df[dfOrderList]
    #print(df)

    return (df)

def importCCC(inputfile):
    bookList = []
    finalBookList = []
    print(inputfile)
    with open(inputfile) as ccc_file:
        for row in ccc_file:
            cccLine = row.split(";")
            finalBookList.append([cccLine[0], cccLine[1]])
            df = pd.DataFrame(finalBookList, columns =['SeriesID', 'IssueID'])
   

    #df['issueID'] = 0
    df['IssueNumber'] = 1
    
    df.fillna({'IssueNumber':0}, inplace=True)
    df = df.astype({'IssueNumber':str,'IssueID':int})#.fillna(0)#,errors='ignore')#.fillna(0)#,'IssueID':'int'})


    df.rename(columns={'seriesName': 'SeriesName', 'seriesYear': 'SeriesStartYear', 'issueNumber': 'IssueNum', 'issueID':'IssueID'}, inplace=True)



    df['IssueType'] = ''
    df['IssueNum'] = ''

    df['SeriesName'] = ''
    df['SeriesStartYear'] = ''
    df['CoverDate'] = ''
    df['Name'] = ''
    #df['SeriesID'] = ''
    #df['IssueID'] = ''
    df['CV Series Name'] = ''
    df['CV Series Year'] = ''
    df['CV Issue Number'] = ''#df['IssueNum']
    df['CV Series Publisher'] = ''
    df['CV Cover Image'] = ''
    df['CV Issue URL'] = ''


    # print(bookSet)
    
    # #Iterate through unique list of series
    # if VERBOSE: print('Compiling set of issueNumbers from CBLs',2)
    # for series in bookSet:
    #     curSeriesName = series[0]
    #     curSeriesYear = series[1]
    #     curSeriesIssues = []
    #     #Check every book for matches with series
    #     for book in bookList:
    #         if book['seriesName'] == curSeriesName and book['seriesYear'] == curSeriesYear:
    #             #Book matches current series! Add issueNumber to list
    #             curSeriesIssues.append({'issueNumber':book['issueNumber'],'issueID':"Unknown"})


    #     finalBookList.append({'seriesName':curSeriesName,'seriesYear':curSeriesYear,'issueNumberList':curSeriesIssues})

    # print(finalBookList[1]['issueNumberList'])
    # #print(type(finalBookList[1]['issueNumberList'][issueID]))
    # issuedict = finalBookList[1]['issueNumberList']
    # print(issuedict[issueID])
    
    # #print(finalBookList)
    # #print(type(finalBookList))
    # df = pd.DataFrame(finalBookList, columns =['seriesName', 'seriesYear', 'issueNumberList'])
    # #df = pd.DataFrame(finalBookList['issueNumberList'], columns =['issueNumber', 'fissueID'])
    
    # #df = pd.DataFrame(finalBookList, columns =['SeriesName', 'SeriesStartYear', 'IssueNum'])
    # #print(df['issueNumberList'].values.tolist())

    # #print(finalBookList[0]['issueNumberList']['issueNumber'])
    # #rowlist = 
    # #print(rowlist['issueID'])
    # #print(rowlist[2]['issueNumberList'])
    # #print(len(finalBookList))
    # for i in range(len(finalBookList)):
    #     # y = i+1
    #     # #df.loc[i,'issueNumberList'] = rowlist[i]['issueNumberList']
    #     # if finalBookList[i]['issueNumberList'] == None or finalBookList[i]['issueNumberList'] == '':
    #     #     finalBookList[i]['issueNumberList'] = 0
        
    #     # if rowlist[i]['issueID'] == None or rowlist[i]['issueID'] == '':
    #     #     rowlist[i]['issueID'] = 0
  
    #     #print(finalBookList[i]['issueNumberList'][0])
    #     #print(finalBookList[i]['issueNumberList'][1])
    #     df.loc[i,'issueNumber'] = finalBookList[i]['issueNumberList'][0]
    #     df.loc[i,'issueID'] = finalBookList[i]['issueNumberList'][1]
        
    #     #print(rowlist[i]['IssueID'])
    #     #print(df[i, 'IssueID'])
    #     ###df.fillna({'issueNumber':0, 'issueID':0}, inplace=True)
    #     #df = df.astype({'SeriesID':float,'IssueID':float}).astype({'SeriesID':int,'IssueID':int})#.fillna(0)#,errors='ignore')#.fillna(0)#,'IssueID':'int'})
    #     ###df = df.astype({'issueNumber':int,'issueID':int})#.fillna(0)#,errors='ignore')#.fillna(0)#,'IssueID':'int'})


    # df = df.drop('issueNumberList', axis='columns')

   
    #print(df)

    return (df)

def importXLSX(outputfile):

    df = pd.read_excel(outputfile, index_col=0)#, header=None)
    df['SeriesStartYear'] = pd.to_numeric(df['SeriesStartYear'], errors='coerce').fillna(0).astype(int)
    df['SeriesID'] = pd.to_numeric(df['SeriesID'], errors='coerce').fillna(0).astype(int)
    df['IssueID'] = pd.to_numeric(df['IssueID'], errors='coerce').fillna(0).astype(int)
    df['CV Series Year'] = pd.to_numeric(df['CV Series Year'], errors='coerce').fillna(0).astype(int)
    df['CV Issue Number'] = df['CV Issue Number'].astype(str).str.replace(".0","",regex=False)
    df['IssueNum'] = df['IssueNum'].astype(str).str.replace(".0","",regex=False)
    df['CV Issue URL'] = df['CV Issue URL'].astype(str)
    '''
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col].fillna('', inplace=True)  # Fill string columns with empty string
        elif df[col].dtype == 'datetime64[ns]':
            df[col].fillna(pd.NaT, inplace=True)  # Fill datetime columns with NaT
        else:
            df[col].fillna(0, inplace=True) 
    
    '''
    df = df.astype(object).fillna('')
    #rowint = 0

    df = df.reset_index(drop=True)  # make sure indexes pair with number of rows
    return(df)


def getCBLData(df,name,numissues):
    lines = []
    IDsList = []
    duplicateIssues.append('\n' + name + ':\n')
    #name = name.strip('.json')
    lines.append("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
    lines.append(
        "<ReadingList xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">\n")
    
    print("     Creating CBL: %s " % (name))
    name = name.replace("&","&amp;").replace('"',"&quot;").replace("'","&apos;").replace("<","&lt;").replace(">","&gt;")

    lines.append("<Name>%s</Name>\n" % (name))
    lines.append("<NumIssues>%s</NumIssues>\n" % (numissues))
    #lines.append("<Source>%s</Source>\n" % (self.source.name))
    #lines.append("<Database Name=\"cv\" ID=\"%s\" />\n" % (id))
    lines.append("<Books>\n")

    
    for index, row in df.iterrows():
        #print(index)
        seriesName = row['SeriesName']
        seriesStartYear = row['SeriesStartYear']
        issueNum = row['CV Issue Number']
        #issueNum = f'{float(issueNum):g}'
        #issueNum = int(issueNum)
        issueType = row['IssueType']
        coverDate = row['CoverDate']
        seriesID = row['SeriesID']
        issueID = row['IssueID']
        cvSeriesName = row['CV Series Name']
        cvSeriesYear = row['CV Series Year']
        cvSeriesPublisher = row['CV Series Publisher']
        cvIssueURL = row['CV Issue URL']
        coverImage = row['CV Cover Image']
        
        issueYear = coverDate.year
        if not isinstance(issueYear,int):
            issueYear = 0
        if issueID in IDsList:
            duplicateIssues.append('     ' + seriesName + ' (' + str(seriesStartYear) + ') #' + str(issueNum) + '  Issue ID: ' + str(issueID) + '  CV: ' + cvSeriesName + ' (' + str(cvSeriesYear) + ')\n')
            print('Found Duplicate Issue: ' + str(issueID))

        else:
                
            if isinstance(issueID,int) and not issueID == 0:
                cvSeriesNameCBL = cvSeriesName.replace("&","&amp;").replace('"',"&quot;").replace("'","&apos;").replace("<","&lt;").replace(">","&gt;")
                
                lines.append("<Book Series=\"%s\" Number=\"%s\" Volume=\"%s\" Year=\"%s\">\n" % (
                        cvSeriesNameCBL, issueNum, cvSeriesYear, issueYear))
                lines.append(
                        "<Database Name=\"cv\" Series=\"%s\" Issue=\"%s\" />\n" % (seriesID, issueID))
                lines.append("</Book>\n")
                IDsList.append(issueID)

        
    # # For each issue in arc
    # for key, issue in sorted(self.issueList.items()):
    #     if isinstance(issue, Issue):
    #         # Check if issue cover date exists
    #         if issue.coverDate is not None and isinstance(issue.coverDate, datetime.datetime):
    #             issueYear = issue.coverDate.year
    #         else:
    #             issueYear = issue.year

    #         seriesName = utilities.escapeString(issue.series.name)
    #         issueNum = utilities.escapeString(issue.issueNumber)

    #         if issue.hasValidID() or (isinstance(issue.series, Series) and issue.series.hasValidID()):
    #             lines.append("<Book Series=\"%s\" Number=\"%s\" Volume=\"%s\" Year=\"%s\">\n" % (
    #                 seriesName, issueNum, issue.series.startYear, issueYear))
    #             lines.append(
    #                 "<Database Name=\"cv\" Series=\"%s\" Issue=\"%s\" />\n" % (issue.series.id, issue.id))
    #             lines.append("</Book>\n")
    #         else:
    #             lines.append("<Book Series=\"%s\" Number=\"%s\" Volume=\"%s\" Year=\"%s\" />\n" %
    #                             (seriesName, issueNum, issue.series.startYear, issueYear))

    lines.append("</Books>\n")
    lines.append("<Matchers />\n")
    lines.append("</ReadingList>\n")

    return lines

# def insertImage(issueID, cvImageURL):
#     imageFileName = str(issueID) + '.jpg'
#     imageFilePath = os.path.join(IMAGE_DIR, imageFileName)
#     if not os.path.exists(imageFilePath) and not cvImageURL == 'Unknown':
#         imageFilePath = getcvimage(issueID,cvImageURL)
            
#     # imageInsert = Image.open(imageFilePath)
#     # imageInsert.thumbnail((400,500))
#     # imageInsertFile = str(issueID) + '_small.jpg'
#     # imageInsertPath = os.path.join(IMAGE_DIR, imageInsertFile)
#     # imageInsert.save(imageInsertPath)

#     return(imageFilePath)



def findIssueID(seriesID,issueNum):
    #goodResponse = False
    issueID = 0 # did this fix the len?
    coverDate = ""
    #while not goodResponse:
        #goodResponse = True
    if not seriesID == 0:
        try:
            if VERBOSE: print("     Searching for %s on CV" % (seriesID))

            # Query the database directly for the specific match
            # Note: issue_number is TEXT in your schema, so we cast to string
            query = "SELECT id FROM cv_issue WHERE volume_id = ? AND issue_number = ?"
            cursor.execute(query, (seriesID, str(issueNum)))
            #ccursor.execute(query, (seriesID, str(issueNum)))

            result = cursor.fetchone()
            if result:
                issueID = result[0]
            else:
                if VERBOSE: 
                    print(f"    No results found for {seriesID} issue {issueNum}")
                    
        except Exception as e:
            print(f"    There was an error querying the database for series {seriesID}")
            print(repr(e))
            #goodResponse = True
    return issueID




def getVolumeDetails(seriesID):
    """
    Look up volume name, year, and publisher name by joining 
    cv_volume and cv_publisher.
    """
    cvSeriesName = ''
    cvSeriesYear = ''
    cvSeriesPublisher = ''
    
    if seriesID > 0:
        try:
            if VERBOSE:
                print(f"    Searching for {seriesID} volume details in Local DB")

            # The JOIN connects the two tables based on the publisher ID
            query = """
                SELECT 
                    v.name, 
                    v.start_year, 
                    p.name 
                FROM cv_volume AS v
                LEFT JOIN cv_publisher AS p ON v.publisher_id = p.id
                WHERE v.id = ?
            """
            
            cursor.execute(query, (seriesID,))
            result = cursor.fetchone()
            
            if result:
                # result is a tuple: (volume_name, start_year, publisher_name)
                cvSeriesName, cvSeriesYear, cvSeriesPublisher = result
            else:
                if VERBOSE:
                    print(f"    No volume details found for ID: {seriesID}")
                    
        except Exception as e:
            print(f"    Error retrieving volume/publisher for {seriesID}")
            print(repr(e))

    return [cvSeriesName, cvSeriesYear, cvSeriesPublisher]

def getSeriesIDfromIssue(issueID):
    """
    Look up the volume_id (Series ID) for a specific issue ID.
    Replaces the ComicVine API get_issue call.
    """
    seriesid = 0
    
    if issueID > 0:
        try:
            # We just need the volume_id column from the cv_issue table
            query = "SELECT volume_id FROM cv_issue WHERE id = ?"
            
            cursor.execute(query, (issueID,))
            result = cursor.fetchone()
            
            if result:
                seriesid = result[0]
            else:
                if VERBOSE:
                    print(f"    No issue found with ID: {issueID}")
                    
        except Exception as e:
            print(f"    There was an error retrieving volume for issue {issueID}")
            print(repr(e))
            
    return seriesid


def getIssueDetails(issueID):
    """
    Look up issue-specific details from the local database.
    Replaces the ComicVine API get_issue call.
    """
    cvImageURL = ''
    cvIssueURL = ''
    coverDate = ''
    cvIssueNum = ''
    
    if issueID != 0:
        try:
            if VERBOSE:
                print(f"    Searching for {issueID} issue details in Local DB")

            # Selecting the specific columns defined in your cv_issue schema
            query = """
                SELECT 
                    image_url, 
                    site_detail_url, 
                    cover_date, 
                    issue_number 
                FROM cv_issue 
                WHERE id = ?
            """
            
            cursor.execute(query, (issueID,))
            result = cursor.fetchone()
            
            if result:
                # Unpack the database row into your variables
                cvImageURL, cvIssueURL, coverDate, cvIssueNum = result
            else:
                if VERBOSE:
                    print(f"    No results found for issue ID: {issueID}")
                    
        except Exception as e:
            print(f"    There was an error processing issue {issueID}")
            print(repr(e))
            
    return [cvImageURL, cvIssueURL, coverDate, cvIssueNum]




def getcvimage(issueID,cvImageURL):
    imageFileName = str(issueID) + '.jpg'
    imageFilePath = os.path.join(IMAGE_DIR, imageFileName)
    if not os.path.exists(imageFilePath): 
        image_request = requests.get(cvImageURL)
        #print(cvImageURL)
        if image_request.status_code == 200:
            with open(imageFilePath, 'wb') as f:
                f.write(image_request.content)
             
    return imageFilePath

def make_clickable(val):
    # target _blank to open new window
    return '<a target="_blank" href="{}">{}</a>'.format(val, 'CV Issue or Search Missing')

def searchCV(seriesName,seriesStartYear):
    #print(type(seriesStartYear))
    #searchURL = ('https://www.google.com/search?q=' + seriesName + '+' + str(seriesStartYear) + '+comic vine').replace(" ", "%20").replace('&', '%26')
    searchURL = ('https://comicvine.gamespot.com/search/?i=volume&q=' + seriesName + '+' + str(seriesStartYear)).replace(' &', '+%26').replace(" ", "+")
    #print(searchURL)
    return '<a target="_blank" href="{}">{}</a>'.format(searchURL, 'Search for Series')

def get_thumbnail(path):
    i = Image.open(path)
    i.thumbnail((200, 200), Image.LANCZOS)
    return i

def image_base64(im):
    if isinstance(im, str):
        im = get_thumbnail(im)
        if im.mode in ("RGBA", "P"): im = im.convert("RGB")
    with BytesIO() as buffer:
        im.save(buffer, 'jpeg')
        return base64.b64encode(buffer.getvalue()).decode()

def image_formatter(im):
    return f'<img src="data:image/jpeg;base64,{image_base64(im)}">'

def color_cels(value):

    if value == 0:
        color = 'red'
    elif value == '':
        color = 'red'
    else:
        color = 'white'


    return 'background-color: %s' % color

def is_valid_year(value):
    if value == "":
        return False  # An empty string is not a valid year
    try:
        # Try converting the value to an integer
        year = int(value)
        # Check if the converted value is within a reasonable range for a year
        return 1900 <= year <= 2100  # Modify the range as needed
    except ValueError:
        # If conversion to int fails, check if it's a string that can be converted
        try:
            # Try converting the value to a float
            year = float(value)
            # Check if the float value represents a whole number and is within the year range
            return year.is_integer() and 1900 <= int(year) <= 2100  # Modify the range as needed
        except ValueError:
            # If both int and float conversions fail, it's not a valid year
            return False


def getCleanName(string):
    string = str(string)
    string = stripAccents(string.lower())
    cleanString = " ".join([word for word in str(
        string).split() if word not in stop_words])
    cleanString = re.sub(dynamicNameTemplate, '', str(cleanString))

    return cleanString

def stripAccents(s):
    # Converts accented letters to their basic english counterpart
    s = str(s)
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def findVolume(series, year):
    """
    Search for a volume ID using name and year in the local database.
    Replaces the list_volumes API call and handles publisher preferences.
    """
    comicID = 0
    publisher = "Unknown"
    found = False
    
    # We use a year range (+/- 1 year) as per your original logic
    try:
        search_year = int(year)
    except (ValueError, TypeError):
        print('    Year is in wrong format')
        return [publisher, 0]

    if isinstance(series, str):
        if VERBOSE: 
            print(f"    Searching for {series} ({search_year}) in Local DB")
            
        try:
            # We fetch all matching volumes within the year range
            # Using JOIN to get publisher names for blacklist/preferred checks
            query = """
                SELECT 
                    v.id, 
                    v.name, 
                    v.start_year, 
                    v.count_of_issues,
                    p.name AS publisher_name
                FROM cv_volume v
                LEFT JOIN cv_publisher p ON v.publisher_id = p.id
                WHERE v.name LIKE ? 
                AND v.start_year BETWEEN ? AND ?
            """
            # Using % for partial matches if needed, but your original 
            # used getCleanName, so we'll look for exact matches here.
            cursor.execute(query, (series, search_year - 1, search_year + 1))
            results = cursor.fetchall()

            if not results:
                print(f"    No results found for {series} ({search_year})")
                return [publisher, 0]

            valid_matches = []
            
            for row in results:
                v_id, v_name, v_start_year, v_count, p_name = row
                
                # Blacklist logic
                if v_id in SERIESID_BLACKLIST or p_name in PUBLISHER_BLACKLIST:
                    if VERBOSE: print(f"    Skipping blacklisted: {p_name} - {v_name} ({v_id})")
                    continue
                
                valid_matches.append({
                    'id': v_id,
                    'name': v_name,
                    'year': v_start_year,
                    'count': v_count,
                    'publisher': p_name
                })

            if valid_matches:
                # Logic to pick the best match
                # 1. Look for preferred publishers
                # 2. If multiple, or none preferred, pick the one with most issues
                best_match = None
                
                # Filter for preferred if any exist
                preferred = [m for m in valid_matches if m['publisher'] in PUBLISHER_PREFERRED]
                candidates = preferred if preferred else valid_matches
                
                # Pick the candidate with the highest issue count
                best_match = max(candidates, key=lambda x: x['count'])
                
                comicID = best_match['id']
                publisher = best_match['publisher']
                found = True
                
                if VERBOSE:
                    print(f"    Found on local DB: {publisher} - {series} ({search_year}) : {comicID}")

        except Exception as e:
            print(f"    Error processing {series} ({search_year})")
            print(repr(e))

    return [publisher, int(comicID)]


def findVolumeNoYear(series, issuenumber):
    """
    Search for a volume ID and issue ID by matching the name and 
    confirming the issue number exists within that volume.
    """
    comicID = 0
    issueID = 0
    publisher = "Unknown"
    found = False
    
    if not isinstance(series, str):
        return [publisher, 0, 0]

    if VERBOSE: 
        print(f"    Searching for {series} (No Year) in Local DB")

    try:
        # 1. Find all volumes that match the name and aren't blacklisted
        # We join with publisher immediately to handle the blacklist/preference
        query = """
            SELECT 
                v.id, v.name, v.count_of_issues, p.name AS pub_name
            FROM cv_volume v
            LEFT JOIN cv_publisher p ON v.publisher_id = p.id
            WHERE v.name LIKE ?
        """
        cursor.execute(query, (series,))
        volume_results = cursor.fetchall()

        series_matches = []
        for v_id, v_name, v_count, p_name in volume_results:
            if v_id in SERIESID_BLACKLIST or p_name in PUBLISHER_BLACKLIST:
                continue
            
            # 2. For each matching volume, check if the issue number exists
            # We call your existing findIssueID logic (as a query here for speed)
            cursor.execute(
                "SELECT id FROM cv_issue WHERE volume_id = ? AND issue_number = ?", 
                (v_id, str(issuenumber))
            )
            issue_match = cursor.fetchone()

            if issue_match:
                series_matches.append({
                    'id': v_id,
                    'publisher': p_name or "Unknown",
                    'issue_count': v_count,
                    'issue_id': issue_match[0]
                })

        # 3. Handle multiple matches (Pick preferred or most issues)
        if series_matches:
            # Filter for preferred publishers
            preferred = [m for m in series_matches if m['publisher'] in PUBLISHER_PREFERRED]
            candidates = preferred if preferred else series_matches
            
            # Pick the one with the highest issue count (usually the "main" series)
            best_match = max(candidates, key=lambda x: x['issue_count'])
            
            comicID = best_match['id']
            issueID = best_match['issue_id']
            publisher = best_match['publisher']
            found = True
            
            if VERBOSE:
                print(f"    Found Match: Series {comicID}, Issue {issueID} ({publisher})")

    except Exception as e:
        print(f"    Error processing {series} #{issuenumber}")
        print(repr(e))

    if not found:
        seriesNotFoundList.append(series)

    return [publisher, int(comicID), int(issueID)]

# def daysBetween(d1, d2):
#     d1 = datetime.strptime(str(d1), "%Y-%m-%d")
#     d2 = datetime.strptime(str(d2), "%Y-%m-%d")
#     return abs((d2 - d1).days)


# def highlight(x):
#     c1 = 'background-color: yellow'

#     #empty DataFrame of styles
#     df1 = pd.DataFrame('', index=x.index, columns=x.columns)
#     #set new columns by condition
    
#     df1.loc[(x['SeriesName'] == 'Hero for Hire'), 'CV Series Name'] = c1
#     #df1.loc[(x['SeriesYear'] != x['CV Series Year']), 'CV Series Year'] = c1
#     #df1.loc[(x['C'] < 3), 'C'] = c1
    
#     return df1
# #df.style.apply(highlight, axis=None)


main()


    
# def writeJSON(file):
#     listData = dict()

#     with open(file, 'r'):

#     return(listData)

#issueheader = data['Issues']['1']
#database = data['Issues']['1']['Database']['Name']['1]']
#csvheader = issues + database
#print(database)
#print(data.values['Issues']['1']['SeriesName'])

# now we will open a file for writing
#data_file = open(outputfile, 'w')

# print(type(data))
# print(type(issue_data))
# print(type (issueheader))

# xlsheader = [
#      #header / data field
#     ("Series Name", "SeriesName"),
#     ("Series Start Year", "SeriesStartYear"),
#     ("Issue Number", "IssueNum"),
#     ("Issue Type", "IssueType"),
#     ("Cover Date", "CoverDate"),
#     ("CV Series ID", "SeriesID"),
#     ("CV Issue ID", "IssueID"),
# ]
