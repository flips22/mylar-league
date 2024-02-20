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
from simyan.sqlite_cache import SQLiteCache
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
from datetime import datetime
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
searchTruthDB = False
#Change forceCreateCBL to True to create CBL even if there are missing issues.
forceCreateCBL = False


#File prefs
SCRIPT_DIR = os.getcwd()
READINGLIST_DIR = os.path.join(SCRIPT_DIR, "ReadingLists")
DATA_FILE = os.path.join(SCRIPT_DIR, "Wishlist-Output.csv")

IMAGE_DIR = os.path.join(SCRIPT_DIR, "CVCoverImages")


#CV prefs
#CV_SEARCH_LIMIT = 10000 #Maximum allowed number of CV API calls
CACHE_RETENTION_TIME = 180 #days

CV_API_KEY = config['comicVine']['cv_api_key']
CV_API_RATE = 1 #Seconds between CV API calls
FORCE_RECHECK_CV = False
PUBLISHER_BLACKLIST = ["Panini Comics","Editorial Televisa","Planeta DeAgostini","Unknown","Urban Comics","Dino Comics","Ediciones Zinco","Abril","Panini Verlag","Panini España","Panini France","Panini Brasil","Egmont Polska","ECC Ediciones","RW Edizioni","Titan Comics","Dargaud","Federal", "Marvel UK/Panini UK","Grupo Editorial Vid","JuniorPress BV","Pocket Books", "Caliber Comics", "Panini Comics","Planeta DeAgostini","Newton Comics","Atlas Publishing"]
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

'''

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
truthDB = os.path.join(dataDirectory, "CMRO.db")

#cvCacheFile = os.path.join(dataDirectory, "CV.db")
cvCacheFile = os.path.join(dataDirectory, "CV-NEW.db")
#vCacheFile = os.path.join(dataDirectory, "CV-TEMP.db")


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


def main():
    checkDirectories()
    summaryResults = []
    problemResults = []
    uniqueSeriesWarnings = []
    uniqueSeriesWarnings.append('Found series with the same title and different Series IDs:\n')
    global duplicateIssues
    duplicateIssues = []
    


    
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
                            if not cvImageURL == '':
                                try:
                                    imageFilePath = getcvimage(issueID,cvImageURL)
                                    coverImage = get_thumbnail(imageFilePath)
                                    coverImage = image_formatter(imageFilePath)
                                    #print(imageFilePath)
                                except:
                                    print('Not able to load issueID image from %s'%(imageFilePath))
                    if issueIDPres:# and 'google' in cvIssueURL:
                        cvIssueURL = 'https://comicvine.gamespot.com/issue/4000-' + str(issueID) + '/'

                    if issueIDPres and missingIssueDetails:
                        cvIssueDetails = getIssueDetails(issueID)
                        cvImageURL = cvIssueDetails[0]
                        cvIssueURL = cvIssueDetails[1]
                        coverDate = cvIssueDetails[2]
                        cvIssueNum = cvIssueDetails[3]
                        if not cvImageURL == '':
                            try:
                                imageFilePath = getcvimage(issueID,cvImageURL)
                                coverImage = get_thumbnail(imageFilePath)
                                coverImage = image_formatter(imageFilePath)
                            except:
                                print('Not able to load issueID image from %s'%(imageFilePath))

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
                    df.loc[index,'CoverDate'] = coverDate
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

    if sqliteConnection:
        cursor.close()
        sqliteConnection.close()
        print("The truthDB connection is closed")

                    
                
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
    year1 = 2019
    year2 = 2024
    #patternYearFileName = r'\[(\d{4})\s*-\s*(\d{4})\]'  # Matches years in the format [YYYY - YYYY]
    #patternYearFileName = r'(\d{4} - \d{4})|([0-9]{4} - Present)|(\d{4})'

    # Find all matches of the pattern in the input string
    #matches = re.findall(patternYearFileName, filename)
    #yearRangeMatch =  re.findall(r'\[(\d{4}-\d{4})\]', filename)
    yearRangeMatch =  re.findall(r'(\d{4}-\d{4})', filename)

    yearRangeMatchPresent = re.findall(r'\[(\d{4}-Present)\]|\((\d{4}-Present)\)', filename)
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
    df.fillna('', inplace=True)
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
    if '&' in name:
        name = name.replace('&','&#38;')
    else:
        name = name

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
                if '&' in cvSeriesName:
                    cvSeriesNameCBL = cvSeriesName.replace('&','&#38;')
                else:
                    cvSeriesNameCBL = cvSeriesName
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
    goodResponse = False
    issueID = 0 # did this fix the len?
    coverDate = ""
    while not goodResponse:
        goodResponse = True
        if not seriesID == 0:
            try:
                if VERBOSE: print("     Searching for %s on CV" % (seriesID))
            
                session = Comicvine(api_key=CV_API_KEY, cache=SQLiteCache(cvCacheFile,CACHE_RETENTION_TIME))
                searchparam = "volume:" + str(seriesID)


                response = session.list_issues(params={"filter": searchparam},max_results=1500)
                if len(response) == 0: #change to response 200?
                    print("     No results found for %s" % (seriesID))
                else: #Results were found
                    for result in response: #Iterate through CV results
                        #print(result.number)
                        #print(type(result.number))
                        #print(issueNum)
                        #print(type(issueNum))
                        #If exact series name and year match
                        if result.number == str(issueNum):
                            #print(result.number)
                            #print(type(result.number))
                            #print(issueNum)
                            #print(type(issueNum))
                            issueID = result.id

            except Exception as e:
                print("     There was an error processing %s)" % (seriesID))
                print(repr(e))
                goodResponse = False
                if 'Rate limit exceeded' in repr(e):
                    print('Rate limited sleeping 200 seconds...')
                    time.sleep(200)
                if 'Object Not Found' in repr(e):
                    print('Not Found...  moving on....')
                    goodResponse = True
    #print(issueID)
    return (issueID)

def getVolumeDetails(seriesID):
    goodResponse = False
    cvSeriesName = ''
    cvSeriesYear = ''
    cvSeriesPublisher = ''
    while not goodResponse:
        goodResponse = True
        if seriesID > 0:

            try:
                print("     Searching for %s volume details on CV" % (str(seriesID)))
                #time.sleep(CV_API_RATE)
                session = Comicvine(api_key=CV_API_KEY, cache=SQLiteCache(cvCacheFile,CACHE_RETENTION_TIME))
                response = session.get_volume(seriesID)
                cvSeriesName = response.name
                cvSeriesYear = response.start_year
                cvSeriesPublisher = response.publisher.name
                

            except Exception as e:
                print("     There was an error processing %s" % (str(seriesID)))
                print(repr(e))
                goodResponse = False
                if 'Rate limit exceeded' in repr(e):
                    print('Rate limited sleeping 200 seconds...')
                    time.sleep(200)
                if 'Object Not Found' in repr(e):
                    print('Not Found...  moving on....')
                    goodResponse = True

    return[cvSeriesName, cvSeriesYear, cvSeriesPublisher]

def getSeriesIDfromIssue(issueID):
    goodResponse = False
    seriesid = 0
    while not goodResponse:
        goodResponse = True
        try:
            session = Comicvine(api_key=CV_API_KEY, cache=SQLiteCache(cvCacheFile,CACHE_RETENTION_TIME))

            response = session.get_issue(issue_id=issueID)
            seriesid = response.volume.id
            #print('found series id')
            #print(seriesid)
        except Exception as e:
                print("     There was an error processing %s" % (issueID))
                print(repr(e))
                goodResponse = False
                if 'Rate limit exceeded' in repr(e):
                    print('Rate limited sleeping 200 seconds...')
                    time.sleep(200)
                if 'Object Not Found' in repr(e):
                    print('Not Found...  moving on....')
                    goodResponse = True
    return seriesid

def getIssueDetails(issueID):
    goodResponse = False
    cvImageURL = ''
    cvIssueURL = ''
    coverDate = ''
    cvIssueNum = ''
    while not goodResponse:
        goodResponse = True
        if not issueID == 0:
                
            try:
                print("     Searching for %s issue details on CV" % (str(issueID)))
                #time.sleep(CV_API_RATE)
                session = Comicvine(api_key=CV_API_KEY, cache=SQLiteCache(cvCacheFile,CACHE_RETENTION_TIME))

                response = session.get_issue(issueID)
                cvImageURL = response.image.medium_url
                cvIssueURL = response.site_url
                #seriesID = response.volume
                coverDate = response.cover_date
                cvIssueNum = response.number
                #print('new cover Date type: %s'%(type(coverDate)))
            except Exception as e:
                print("     There was an error processing %s" % (issueID))
                print(repr(e))
                goodResponse = False
                if 'Rate limit exceeded' in repr(e):
                    print('Rate limited sleeping 200 seconds...')
                    time.sleep(200)
                if 'Object Not Found' in repr(e):
                    print('Not Found...  moving on....')
                    goodResponse = True
            #print(cvImageURL, cvIssueURL, coverDate, cvIssueNum)
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


def findVolume(series,year):
    goodResponse = False
    found = False
    comicID = 0
    publisher = "Unknown"
    global searchCount
    global CVNotFound
    global CVFound
    #global CV
    while not goodResponse:
        goodResponse = True
        if isinstance(series,str):
            try:
                #searchCount += 1

                result_matches = 0
                preferred_matches = 0
                result_publishers = []
                result_matches_blacklist = 0
                issueCounter = 0

                series_matches = []
                publisher_blacklist_results = set()

                #try:
                if VERBOSE: print("     Searching for %s (%s) on CV" % (series,year))
                
                session = Comicvine(api_key=CV_API_KEY, cache=SQLiteCache(cvCacheFile,CACHE_RETENTION_TIME))
                searchparam = "name:" + series

                response = session.list_volumes(params={"filter": searchparam},max_results=1500)
                if len(response) == 0:
                    print("     No results found for %s (%s)" % (series,year))
                else: #Results were found
                    for result in response: #Iterate through CV results
                        #If exact series name and year match
                        #print(type(result.start_year))
                        #print(type(year))
                        year = int(year)
                        #print(year-1)
                        #print(year +1)
                        resultCleanName = getCleanName(result.name)
                        seriesCleanName = getCleanName(series)
                        #if resultCleanName == seriesCleanName and year -1 <=result.start_year <= year + 1:
                        #if result.name.lower() == series.lower() and year -1 <=result.start_year <= year + 1:
                        #if result.name.lower() == series.lower() and str(result.start_year) == year:
                        try:
                            if resultCleanName == seriesCleanName and year -1 <=result.start_year <= year + 1:


                                print('made it this far')
                                publisher_temp = result.publisher.name
                                result_publishers.append(publisher_temp)

                                series_matches.append(result)
                                if result.id in SERIESID_BLACKLIST:
                                    print('Series ID found in blacklist, skipping')
                                if publisher_temp in PUBLISHER_BLACKLIST:
                                    result_matches_blacklist += 1
                                    publisher_blacklist_results.add(publisher_temp)
                                else:
                                    found = True
                                    result_matches += 1
                                    publisher = publisher_temp
                                    if publisher in PUBLISHER_PREFERRED: preferred_matches += 1
                                    comicID = result.id
                                    numIssues = result.issue_count
                                    print("         Found on comicvine: %s - %s (%s) : %s (%s issues)" % (publisher, series, year, comicID, numIssues))
                        except:
                            print('Year is in wrong format')

                        #Handle multiple publisher matches
                        if result_matches > 1:
                            print("             Warning: Multiple valid matches found! Publishers: %s" % (", ".join(result_publishers)))
                            #print(series_matches)
                            #set result to preferred publisher
                            for item in series_matches:
                                if item.publisher.name in PUBLISHER_PREFERRED or preferred_matches == 0:
                                    numIssues = item.issue_count
                                    if numIssues > issueCounter and year ==result.start_year:
                                        #Current series has more issues than any other preferred results!
                                        publisher = item.publisher.name
                                        comicID = item.id
                                        issueCounter = numIssues
                                        ## TODO: Remove "preferred text labels"
                                        print("             Selected series from multiple results: %s - %s (%s issues)" % (publisher,comicID,numIssues))
                                    if numIssues > issueCounter and year ==result.start_year:
                                        #Current series has more issues than any other preferred results!
                                        publisher = item.publisher.name
                                        comicID = item.id
                                        issueCounter = numIssues
                                        ## TODO: Remove "preferred text labels"
                                        print("             Selected series from multiple results: %s - %s (%s issues)" % (publisher,comicID,numIssues))
                                    else:
                                        #Another series has more issues
                                        print("             Skipped Series : %s - %s (%s issues) - another preferred series has more issues!" % (item.publisher.name,item.id,numIssues))

                        if len(response) == 0: # is this going to work?
                            print("         No results found for %s (%s)" % (series,year))

                        if result_matches_blacklist > 0 and result_matches == 0:
                            #Only invalid results found
                            print("             No valid results found for %s (%s). %s blacklisted results found with the following publishers: %s" % (series,year,result_matches_blacklist, ",".join(publisher_blacklist_results)))
            except Exception as e:
                print("     There was an error processing %s (%s)" % (series,year))
                print(repr(e))
                goodResponse = False
                if 'Rate limit exceeded' in repr(e):
                    print('Rate limited sleeping 200 seconds...')
                    time.sleep(200)
                if 'Object Not Found' in repr(e):
                    print('Not Found...  moving on....')
                    goodResponse = True
            #Update counters
            if not found:
                #CVNotFound += 1
                print('not found')
            else:
                #CVFound += 1
                print('found')



    return [publisher,int(comicID)]


def findVolumeNoYear(series,issuenumber):
    goodResponse = False
    found = False
    comicID = 0
    issueID = 0
    publisher = "Unknown"
    global searchCount
    global CVNotFound
    global CVFound
    #global CV


    '''
    #series = series.replace('Spider-Man -', 'Spider-Man:')
    series = series.replace(' vs ', ' vs. ')
    series = series.replace(' - ', ': ')
    series = series.replace('Spider Island', 'Spider-Island')
    series = series.replace('Mr. ', 'Mister ')
    series = series.replace('2009-2099', '2009/2099')
    series = series.replace('Ghost Spider', 'Ghost-Spider')
    series = series.replace(' Inc ', ' Inc. ')
    #series = series.replace(' & ', ' and ')
    series = series.replace(' & ', '/')
    series = series.replace(' USA', ' U.S.A.')
    #series = series.replace(' v1', '')
    
    
    series = series.replace('Saga of the Swamp Thing', 'The Saga of the Swamp Thing')
    series = series.replace(', ', ': ')
    #series = series.replace(': ', ', ')
    series = series.replace('Cloak and Dagger', 'The Mutant Misadventures of Cloak and Dagger')
    

    series = series.replace(': The Darkseid War - ',': Darkseid War: ')

    
    series = series.replace('Convergence:', 'Convergence')
    series = series.replace(' / ', '/')
    series = series.replace(': ', ' ')
    series = series.replace('Sinestro', 'The Sinestro')
    series = series.replace(' - ', ': ')
        #TEMP:
    
    #series = series.replace(' and ', ' & ')
    series = series.replace('Black:','Black -')
    #series = series.replace(':', '')
    #series = re.sub(r' \([^)]*\)', '', series)
    #series = re.sub(r' \d\D\D series','',series)
    '''




    if isinstance(series,str):
        while not goodResponse:
            
            goodResponse = True
            try:

                #searchCount += 1

                result_matches = 0
                preferred_matches = 0
                result_publishers = []
                result_matches_blacklist = 0
                issueCounter = 0

                series_matches = []
                publisher_blacklist_results = set()

                #try:
                if VERBOSE: print("     Searching for %s on CV" % (series))
                
    

                session = Comicvine(api_key=CV_API_KEY, cache=SQLiteCache(cvCacheFile,CACHE_RETENTION_TIME))
                searchparam = "name:" + series
                response = session.list_volumes(params={"filter": searchparam},max_results=1500)
                if len(response) == 0:
                    print("     No results found for %s" % (series))
                    
                else: #Results were found
                    print('     Found ' + str(len(response)) +' volumes. Checking for match..')

                    for result in response: #Iterate through CV results
                        #If exact series name and year match
                        #print(type(result.start_year))
                        #print(type(year))
                        ##year = int(year)
                        #print(year-1)
                        #print(year +1)
                        resultCleanName = getCleanName(result.name)
                        seriesCleanName = getCleanName(series)
                        #print(resultCleanName)
                        #print(seriesCleanName)
                        publisher = ''
                        #if resultCleanName == seriesCleanName and year -1 <=result.start_year <= year + 1:
                        #if result.name.lower() == series.lower() and year -1 <=result.start_year <= year + 1:
                        #if result.name.lower() == series.lower() and str(result.start_year) == year:
                        if result.publisher:
                            publisher = result.publisher.name

                        if resultCleanName == seriesCleanName and not publisher in PUBLISHER_BLACKLIST:# and year -1 <=result.start_year <= year + 1:
                            print(f"     Found match for series: {result.name} ({result.start_year})")
                            cvIssueFind = findIssueID(result.id,issuenumber)
                            issueID = cvIssueFind
                            if not issueID == 0:

                                cvIssueDetails = getIssueDetails(issueID)
                            
                                coverDate = cvIssueDetails[2]
                                #print(coverDate)
                                #print(type(coverDate))
                                if not coverDate is None:
                                    print(f'     Cover date is: ({coverDate})')
                                    #print(f'Cover date ({coverDate}) is type: {type(coverDate)} and is a proper date')
                                #if not type(coverDate) is type(None) and int(year1) > 0 and int(year2) > 0:
                                    #print(coverDate.year)
                                    #print(year1)
                                    
                                    #print(coverDate.year)
                                    #print(year2)
                                    if coverDate == '':
                                        coverYear = 0
                                    else:
                                        coverYear = coverDate.year
                                        

                                    if int(year1) <= coverYear <= int(year2):
                                        found =True
                                        comicID = result.id
                                        issueID = cvIssueFind
                                        
                                        publisher = result.publisher.name
                                        print(f"     Found Match: Series ID: {comicID} and Issue ID: {issueID} with a cover date of: {coverDate}.")
                                        break
                                    #else:
                                    #    comicID = 0
                                    #    issueID = 0
                                    #    publisher=''
                                    #    print(f"Issue number is in series, but cover date ({coverDate}) is not between {year1} and {year2}")
                                else:
                                    print(f'     Cover date ({coverDate}) is type: {type(coverDate)} and is not a proper date')
                                    #print(type(coverDate))
                            else:
                                print(f"     Series did not contain issue number: {issuenumber}, continuing.")
                            '''













                            print('Searching for the right year')
                            publisher_temp = result.publisher.name
                            result_publishers.append(publisher_temp)

                            series_matches.append(result)
                            if result.id in SERIESID_BLACKLIST:
                                print('Series ID found in blacklist, skipping')
                            if publisher_temp in PUBLISHER_BLACKLIST:
                                result_matches_blacklist += 1
                                publisher_blacklist_results.add(publisher_temp)
                            else:
                                
                                found = True
                                result_matches += 1
                                print(result_matches)
                                publisher = publisher_temp
                                if publisher in PUBLISHER_PREFERRED: preferred_matches += 1
                                comicID = result.id
                                numIssues = result.issue_count
                                print("         Found on comicvine: %s - %s: %s (%s issues)" % (publisher, series, comicID, numIssues))





                        #Handle multiple publisher matches
                    if result_matches > 1:
                        print("             Warning: Multiple valid matches found! Publishers: %s" % (", ".join(result_publishers)))
                        #print(series_matches)
                        #set result to preferred publisher
                        for item in series_matches:
                            print('matches:')
                            print(len(series_matches))
                            print(item.name)
                            #print(item)
                            #print(type(item))
                            #print(item.id)
                            cvIssueFind = findIssueID(item.id,issuenumber)
                            issueID = cvIssueFind
                            if not issueID == 0:

                                cvIssueDetails = getIssueDetails(issueID)
                            
                                coverDate = cvIssueDetails[2]
                                
                                if not type(coverDate) is type(None) and int(year1) > 0 and int(year2) > 0:
                                    print(coverDate.year)
                                    if int(year1) <= coverDate.year <= int(year2):

                                        comicID = item.id
                                        
                                        if item.publisher.name in PUBLISHER_PREFERRED or preferred_matches == 0:
                                            numIssues = item.issue_count
                                            
                                            if numIssues > issueCounter:
                                                #Current series has more issues than any other preferred results!
                                                publisher = item.publisher.name
                                                comicID = item.id
                                                issueCounter = numIssues
                                                ## TODO: Remove "preferred text labels"
                                                print("             Selected series from multiple results: %s - %s (%s issues)" % (publisher,comicID,numIssues))
                                            
                                            #if numIssues > issueCounter and year ==result.start_year:
                                            #    #Current series has more issues than any other preferred results!
                                            #    publisher = item['publisher']['name']
                                            #    comicID = item['id']
                                            #    issueCounter = numIssues
                                            #    ## TODO: Remove "preferred text labels"
                                            #    print("             Selected series from multiple results: %s - %s (%s issues)" % (publisher,comicID,numIssues))
                                            
                                            else:
                                                #Another series has more issues
                                                print("             Skipped Series : %s - %s (%s issues) - another preferred series has more issues!" % (item.publisher.name,item.id,numIssues))
                                        

                                
                                else: 
                                    if item.publisher.name in PUBLISHER_PREFERRED or preferred_matches == 0:
                                        numIssues = item.issue_count
                                        
                                        if numIssues > issueCounter:
                                            #Current series has more issues than any other preferred results!
                                            publisher = item.publisher.name
                                            comicID = item.id
                                            issueCounter = numIssues
                                            ## TODO: Remove "preferred text labels"
                                            print("             Selected series from multiple results: %s - %s (%s issues)" % (publisher,comicID,numIssues))
                                        
                                        #if numIssues > issueCounter and year ==result.start_year:
                                        #    #Current series has more issues than any other preferred results!
                                        #    publisher = item['publisher']['name']
                                        #    comicID = item['id']
                                        #    issueCounter = numIssues
                                        #    ## TODO: Remove "preferred text labels"
                                        #    print("             Selected series from multiple results: %s - %s (%s issues)" % (publisher,comicID,numIssues))
                                        
                                        else:
                                            #Another series has more issues
                                            print("             Skipped Series : %s - %s (%s issues) - another preferred series has more issues!" % (item.publisher.name,item.id,numIssues))

                        if len(response) == 0: # is this going to work?
                            print("         No results found for %s (%s)" % (series))

                        if result_matches_blacklist > 0 and result_matches == 0:
                            #Only invalid results found
                            print("             No valid results found for %s. %s blacklisted results found with the following publishers: %s" % (series,result_matches_blacklist, ",".join(publisher_blacklist_results)))
                #except Exception as e:
                    #print("     There was an error processing %s" % (series))
                    #print(repr(e))
        '''
            except Exception as e:
                print("     There was an error processing %s #%s" % (series,issuenumber))
                print(repr(e))
                goodResponse = False
                if 'Rate limit exceeded' in repr(e):
                    print('Rate limited sleeping 200 seconds...')
                    time.sleep(200)
                if 'Object Not Found' in repr(e):
                    print('Not Found...  moving on....')
                    goodResponse = True

    #Update counters
    if not found:
        #CVNotFound += 1
        #print('not found')
        seriesNotFoundList.append(series)
    #else:
        #CVFound += 1
        #print('found')
        #print(publisher,int(comicID),int(issueID))
        

    return [publisher,int(comicID), int(issueID)]

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
