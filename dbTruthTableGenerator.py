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
import sqlite3
'''

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

#File prefs
SCRIPT_DIR = os.getcwd()
READINGLIST_DIR = os.path.join(SCRIPT_DIR, "ReadingLists")
DATA_FILE = os.path.join(SCRIPT_DIR, "Wishlist-Output.csv")

IMAGE_DIR = os.path.join(SCRIPT_DIR, "CVCoverImages")


#CV prefs
CV_SEARCH_LIMIT = 10000 #Maximum allowed number of CV API calls
CV_API_KEY = config['comicVine']['cv_api_key']
CV_API_RATE = 1 #Seconds between CV API calls
FORCE_RECHECK_CV = False
PUBLISHER_BLACKLIST = ["Panini Comics","Editorial Televisa","Planeta DeAgostini","Unknown","Urban Comics"]
PUBLISHER_PREFERRED = ["Marvel","DC Comics","Vertigo"] #If multiple matches found, prefer this result
#CV = None

dynamicNameTemplate = '[^a-zA-Z0-9]'
stop_words = ['the', 'a', 'and']
yearStringCleanTemplate = '[^0-9]'
cleanStringTemplate = '[^a-zA-Z0-9\:\-\(\) ]'

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
'''
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
#dataDirectory = os.path.join(rootDirectory, "Data")
truthTableDirectory = os.path.join(rootDirectory, "dbTruthTable-Import")
outputDirectory = os.path.join(rootDirectory, "dbTruthTable-Output")
resultsDirectory = os.path.join(rootDirectory, "dbTruthTable-Results")
#outputDirectory = os.path.join(rootDirectory, "ReadingList-Output")
#jsonOutputDirectory = os.path.join(outputDirectory, "JSON")
#cblOutputDirectory = os.path.join(outputDirectory, "CBL")

#dataFile = os.path.join(dataDirectory, "data.db")
#cvCacheFile = os.path.join(dataDirectory, "cv.db")
#overridesFile = os.path.join(dataDirectory,'SeriesOverrides.json')
#configFile = os.path.join(rootDirectory, 'config.ini')
#resultsFile = os.path.join(resultsDirectory, "results-%s.txt" % (timeString))
#problemsFile = os.path.join(resultsDirectory, "problems-%s.txt" % (timeString))
#uniqueSeriesFile = os.path.join(resultsDirectory, "uniqueSeriesWarnings-%s.txt" % (timeString))

outputfileXLSX = os.path.join(outputDirectory, "dbTruthTable-%s.xlsx" % (timeString))
outputfileCSV = os.path.join(outputDirectory, "dbTruthTable-%s.csv" % (timeString))
truthtableDB = os.path.join(outputDirectory, "dbTruthTable-%s.db" % (timeString))

def checkDirectories():

    directories = [
        #dataDirectory,
        truthTableDirectory,
        resultsDirectory,
        outputDirectory,
        #jsonOutputDirectory,
        #cblOutputDirectory
        ]

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)


def importXLSX(outputfile):

    df = pd.read_excel(outputfile, index_col=0)#, header=None)
    #change:
    df['SeriesStartYear'] = pd.to_numeric(df['SeriesStartYear'], errors='coerce').fillna(0).astype(int)
    df['SeriesID'] = pd.to_numeric(df['SeriesID'], errors='coerce').fillna(0).astype(int)
    df['IssueID'] = pd.to_numeric(df['IssueID'], errors='coerce').fillna(0).astype(int)
    df['CV Series Year'] = pd.to_numeric(df['CV Series Year'], errors='coerce').fillna(0).astype(int)
    df['IssueNum'] = df['IssueNum'].astype(str).str.replace(".0","",regex=False)
    df.fillna('', inplace=True)
    #rowint = 0

    df = df.reset_index(drop=True)  # make sure indexes pair with number of rows
    return(df)


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
    dfAll = pd.DataFrame()

    summaryResults = []
    problemResults = []
    uniqueSeriesWarnings = []
   #readingLists = []
    fileCount = 0
    for root, dirs, files in os.walk(truthTableDirectory):
        for file in files:
            if file.endswith(".xlsx"):

                print('Processing %s'%(file))
                inputfile = os.path.join(truthTableDirectory, file)
                df = importXLSX(inputfile)
                df.index = np.arange(1, len(df) + 1)
                df.drop('Days Between Issues', axis='columns', inplace=True)



                #df = df.reset_index()
                for index, row in df.iterrows():
                    #print(index)
                    seriesName = row['SeriesName']
                    seriesStartYear = row['SeriesStartYear']
                    issueNum = row['IssueNum']
                    if isinstance(issueNum, float):
                        issueNum = f'{issueNum:g}'
                    #issueNum = f'{float(issueNum):g}'
                    #issueNum = int(issueNum)
                    issueType = row['IssueType']
                    coverDate = row['CoverDate']
                    #coverDate = pd.DatetimeIndex(coverDate).year
                    try:
                        coverDate = coverDate.to_pydatetime().year
                    except:
                        coverDate = coverDate
                    seriesID = row['SeriesID']
                    issueID = row['IssueID']
                    cvSeriesName = row['CV Series Name']
                    cvSeriesYear = row['CV Series Year']
                    cvIssueURL = row['CV Issue URL']
                    #coverImage = row['CV Cover Image']
                    #print(seriesID)
                    
                    #print('found issueid %s'%(str(issueID)))
                    df.loc[index,'CoverDate'] = coverDate
                    df.loc[index,'IssueID'] = issueID
                    df.loc[index,'CV Series Name'] = cvSeriesName
                    df.loc[index,'CV Series Year'] = cvSeriesYear
                    df.loc[index,'CV Issue Number'] = issueNum
                    df.loc[index,'CV Issue URL'] = cvIssueURL
                    #df.loc[index,'CV Cover Image'] = coverImage
                    df.loc[index,'IssueType'] = 'Issue' # everything's an issue?
                    df.loc[index,'SeriesID'] = seriesID
                    df.loc[index,'ReadingList'] = str(file).replace(truthTableDirectory,'')
                    #df.loc[index,'Days Between Issues'] = dateDelta
                    
                    # # clear variables
                    # coverDate = ''
                    # issueID = 0
                    # cvSeriesName = ''
                    # cvSeriesYear = ''
                    # cvIssueURL = ''
                    # coverImage = ''
                    # #issueType = ''
                    # seriesID = 0
                    # dateDelta = 0



                dfAll = pd.concat([dfAll,df])
    dfAll.reset_index(drop=True, inplace=True)
    dfAll.to_excel(outputfileXLSX)
    dfAll.to_csv(outputfileCSV)
    #dfAll = dfAll.drop('CoverDate', axis='columns')
    con = sqlite3.connect(truthtableDB, isolation_level='DEFERRED')
    cur = con.cursor()
    #SeriesName	SeriesStartYear	IssueNum	IssueType	CoverDate	Name	SeriesID	IssueID	CV Series Name	CV Series Year	CV Cover Image	CV Issue URL	Days Between Issues

    # cur.execute('''
    #     CREATE TABLE IF NOT EXISTS comics(SeriesName text, SeriesStartYear integer, IssueNum text, CoverDate text, SeriesID integer, IssueID integer, CVSeriesName text, CVSeriesYear text, CVIssueURL text)
    #     ''')
    dfAll.to_sql('comics', con, if_exists='replace', index = False)
    con.commit()



    return

main()
                #df=df.drop('Name',axis='columns')
                #df=df.drop('IssueType',axis='columns')
                #df.to_excel(outputfile)
                #df = df.style.format({'CV Issue URL': make_clickable})
                #df = df.style.highlight_null(null_color="red")


            #df.style.applymap(color_cells, subset=['total_amt_usd_diff','total_amt_usd_pct_diff'])
                #df['CoverDate'] = pd.to_datetime(df['CoverDate'], errors='coerce').dt.date()
'''
                numIssueFound = len(df[df['IssueID']>0])
                numIssueTotal = len(df['IssueID'])
                numIssueMissing = numIssueTotal - numIssueFound
                try:
                    maxDays = df['Days Between Issues'].max()
                except:
                    maxDays = 'Unknown'
                summaryString = 'Reading list has ' + str(numIssueMissing) + ' unidentified issues out of ' + str(numIssueTotal) + ' total issues. Maximum days between consecutive issues: ' + str(maxDays)
                
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
                            print(uniqueseries)
                            uniqueSeriesWarnings.append('\n' + outputfile + '\n     ' + uniqueseries + '\n          ' + str(seriestemp.SeriesID.unique()) +'\n')
       

                
                #.set_caption(summaryString)
                dfe = df
                df = df.style.set_table_styles(
                [{"selector": "", "props": [("border", "1px solid grey")]},
                {"selector": "tbody td", "props": [("border", "1px solid grey")]},
                {"selector": "th", "props": [("border", "1px solid grey")]}
                ]).set_caption(summaryString).applymap(color_cels).format({'CV Issue URL': make_clickable})#.to_html(outputhtmlfile)#,formatters={'CV Cover Image': image_formatter}, escape=False)
                df.to_html(outputhtmlfile)
            #FIX    dfe['CoverDate'] = pd.to_datetime(dfe['CoverDate']).dt.date
                dfe['CV Cover Image'] = ' '
                dfe.to_csv(outputcsvfile)
                dfe = dfe.style.set_table_styles(
                [{"selector": "", "props": [("border", "1px solid grey")]},
                {"selector": "tbody td", "props": [("border", "1px solid grey")]},
                {"selector": "th", "props": [("border", "1px solid grey")]}
                ]).applymap(color_cels).format({'CV Issue URL': make_clickable})#.to_html(outputhtmlfile)#,formatters={'CV Cover Image': image_formatter}, escape=False)
                dfe.to_excel(outputfile)
                
                print(outputfile)
                print(summaryString)
                summaryResults.append(inputfile + '\n' + outputfile + '\n' + summaryString + '\n')
                if not numIssueMissing == 0:
                    problemResults.append(inputfile + '\n' + outputfile + '\n' + summaryString + '\n')
                if numIssueMissing == 0:
                    try:
                        cblData = getCBLData(df.data,inputfile,numIssueFound)
                        with open(outputcblfile, 'w') as f:
                            f.writelines(cblData)
                    except:
                        problemResults.append('\n     -- CBL Export Failed --    ' + inputfile + '\n' + outputfile + '\n' + '\n')
                    # cblData = getCBLData(df.data,inputfile,numIssueFound)
                    # with open(outputcblfile, 'w') as f:
                    #     f.writelines(cblData)
                

                    
                
    with open(resultsFile, 'w') as f:
        f.writelines(summaryResults)
    with open(problemsFile, 'w') as f:
        f.writelines(problemResults)
    with open(uniqueSeriesFile, 'w') as f:
        f.writelines(uniqueSeriesWarnings)
    
'''







