'''
This script will search you wishlist at league of comic geeks, and then add each series to mylar. If you add one issue for a series, it will
just add the series (and search for missing issues if you have that setting selected in mylar)
The URL for your wishlist is: https://leagueofcomicgeeks.com/profile/[username]/wish-list
I think it is possible to change to use your collection instead, by changing the wishlistURL, but I haven't testing that much.  Ideally, it would pull your 
pull list, but the page layout for that is more complicated as each week is a page. If you upgrade to pro for $2 a month, your pull list will auto add to either wishlist or 
your collection, but I haven't tested that either.
This script was based on TheMadman's script also listed here in the gist. The biggest change was that it now uses the simyan to search the comicvine api.  It works 
much better than the old design. TheMadman has a way deluxe implementation of simyan for his project at:
https://github.com/themadman0980/ReadingListManager
This script doesn't have near the error handling and everything, so I'm positive it won't work as well, but it does work from a small bit of testing I've done.
It does rely on the series title in leagueofcomicgeeks to exactly (case insensitive) match the series title in comicvine.  I've seen some that don't, and I'm
sure there are special characters that I haven't handled (I only did &).
The reading list function is still in place, it is just commented out.
is an updated script from TheMadman which adds a ton of functionality to my script and also cleans up the code. Here's a description from him:
It will import all the CBL files in a subfolder called 'ReadingLists' and store the data in a csv file to keep track of changes. It will keep a register 
of series name and year (as found in your readinglists), and lookup the CV id and publisher which match (allowing for preferred and blacklisted publishers). 
It will then check/add to Mylar based on user preference.
If you add new files to your readinglist folder and re-run the script, it will merge the new series it finds with the existing data from previous runs rather
than potentially double handling the same series every time you read a cbl file.
Only issue I've found is that sometimes there are 2 matches for a series with the same year found in CV (both with Marvel as publisher) so it's impossible to 
know which comicID is correct without more info.
Installation:
1) Download & install this package (required for searching the comicvine api):
   https://github.com/Metron-Project/Simyan
2) Only necessary if also doing reading list: Create a folder called 'ReadingLists' in the same directory as the script and add any CBL files you want to process into this folder
3) In config.ini replace [MYLAR API KEY] with your Mylar3 api key
4) In config.ini replace [MYLAR SERVER ADDRESS] with your server in the format: http://servername:port/  (make sure to include the slash at the end)
5) In config.ini replace [CV API KEY] with your comicvine api key
6) Optional - Modify the following options:
    - PUBLISHER_BLACKLIST : List of publishers to ignore during CV searching
    - PUBLISHER_PREFERRED : List of publishers to prioritise when multiple CV matches are found
    - ADD_NEW_SERIES_TO_MYLAR : Automatically add CV search results to Mylar as new series
    - CV_SEARCH_LIMIT : Set a limit on the number of CV API calls made during this processing.
                        This is useful for large collections if you want to break the process into smaller chunks.
Usage:
    python3 mylarCBLimport.py
Results are output to "CBL-Output.csv" in the same directory as the script
Notes:
    - Series are found based on series name and year match.
    - If multiple results are found, any matches of the preferred publisher will be prioritised.
    - For multiple matches, this script will output the last result found.
    - CV api calls are limited to once every 2 seconds, so this script can take a while for large collections.
        It is not recommended to reduce this, however you can modify the rate using the CV_API_RATE var.
    - If you mess anything up, you can simply delete the output.csv or force a re-run using the Mylar & CV FORCE_RECHECK vars.
'''

import requests
import json
import time
import os
from enum import IntEnum
import xml.etree.ElementTree as ET
from glob import glob
from sys import argv
import numpy as np
import re
from simyan.comicvine import Comicvine
from simyan.sqlite_cache import SQLiteCache
import configparser

config = configparser.ConfigParser(allow_no_value=True)

if os.path.exists('configPRIVATE.ini'): # an attempt to prevent me from sharing my api keys (again) :)
    config.read('configPRIVATE.ini')
else:
    config.read('config.ini')


leagueUserName = config['leagueOfComicGeeks']['leagueusername']

### DEV OPTIONS
#Enable verbose output
VERBOSE = True
#Prevent overwriting of main CSV data file
TEST_MODE = False

#File prefs
SCRIPT_DIR = os.getcwd()
READINGLIST_DIR = os.path.join(SCRIPT_DIR, "ReadingLists")
DATA_FILE = os.path.join(SCRIPT_DIR, "CBL-Output.csv")

if not os.path.exists(READINGLIST_DIR):
    print('Reading directory not found. Create folder called ReadingLists and try again.')
    raise SystemExit()

if TEST_MODE:
    #Create new file instead of overwriting data file
    OUTPUT_FILE = os.path.join(SCRIPT_DIR, "CBL-Output_new.csv")
else:
    OUTPUT_FILE = DATA_FILE

CSV_HEADERS = ["Series","Year","Publisher", "ComicID","InMylar"]
class Column(IntEnum):
    SERIES = 0
    YEAR = 1
    PUBLISHER = 2
    COMICID = 3
    INMYLAR = 4

#CV prefs
CV_SEARCH_LIMIT = 10000 #Maximum allowed number of CV API calls
CV_API_KEY = config['comicVine']['cv_api_key']
CV_API_RATE = 2 #Seconds between CV API calls
FORCE_RECHECK_CV = False
PUBLISHER_BLACKLIST = ["Panini Comics","Editorial Televisa","Planeta DeAgostini","Unknown"]
PUBLISHER_PREFERRED = ["Marvel","DC Comics"] #If multiple matches found, prefer this result
#CV = None

#Mylar prefs
mylarAPI = config['mylar']['mylarapi']
mylarBaseURL = config['mylar']['mylarbaseurl']

FORCE_RECHECK_MYLAR_MATCHES = False
ADD_NEW_SERIES_TO_MYLAR = True

mylarAddURL = mylarBaseURL + 'api?apikey=' + mylarAPI + '&cmd=addComic&id='
mylarCheckURL = mylarBaseURL + 'api?apikey=' + mylarAPI + '&cmd=getComic&id='

numNewSeries = 0
numExistingSeries = 0
numCBLSeries = 0

#Initialise counters
mylarExisting = 0
mylarMissing = 0
CVFound = 0
CVNotFound = 0
searchCount = 0

#League of comic geeks config
wishlistURL = 'https://leagueofcomicgeeks.com/profile/' + leagueUserName + '/wish-list'
series_pat_str = '(?<=data-sorting=")(.+?(?="))'
volume_pat_str = '(?<="series" data-begin=")(.+?(?="))'


def parseWishlist():
    series_list = []
    wishlistData = requests.get(wishlistURL).text

    print("Checking Wishlist at %s"% (wishlistURL))

    series_pattern = re.compile(series_pat_str)
    volume_pattern = re.compile(volume_pat_str)

    series_result = series_pattern.findall(wishlistData)
    volume_result = volume_pattern.findall(wishlistData)
    
    for i in range(len(series_result)):
        series_result[i] = series_result[i].replace('amp;','')
        series_list.append([series_result[i], volume_result[i]])
    
    return series_list

def parseCBLfiles():
    series_list = []

    print("Checking CBL files in %s" % (READINGLIST_DIR))
    for root, dirs, files in os.walk(READINGLIST_DIR):
        for file in files:
            if file.endswith(".cbl"):
                try:
                    filename = os.path.join(root, file)
                    #print("Parsing %s" % (filename))
                    tree = ET.parse(filename)
                    fileroot = tree.getroot()

                    cblinput = fileroot.findall("./Books/Book")
                    for series in cblinput:
                        line = series.attrib['Series'].replace(",",""),series.attrib['Volume']
                        series_list.append(list(line))
                except:
                    print("Unable to process file at %s" % ( os.path.join(str(root), str(file)) ))

    return series_list

def isSeriesInMylar(comicID):
    found = False
    global mylarExisting
    global mylarMissing

    #print("Checking if comicID %s exists in Mylar" % (comicID))

    if comicID.isnumeric():
        comicCheckURL = "%s%s" % (mylarCheckURL, str(comicID))
        mylarData = requests.get(comicCheckURL).text
        jsonData = json.loads(mylarData)
        #jsonData = mylarData.json()
        mylarComicData = jsonData['data']['comic']

        if not len(mylarComicData) == 0:
            found = True
    elif comicID != "Unknown":
        print("         Mylar series status unknown - invalid ComicID:%s" % (comicID))

    if found:
        if VERBOSE: print("         Match found for %s in Mylar" % (comicID))
        mylarExisting += 1
        return True
    else:
        if VERBOSE: print("         No match found for %s in Mylar" % (comicID))
        mylarMissing += 1
        return False

    #In the event of if else failure
    return False;

def addSeriesToMylar(comicID):
    if comicID.isnumeric():
        if VERBOSE: print("         Adding %s to Mylar" % (comicID))
        comicAddURL = "%s%s" % (mylarAddURL, str(comicID))
        mylarData = requests.get(comicAddURL).text

        ## Check result of API call
        jsonData = json.loads(mylarData)
        #jsonData = mylarData.json()
        #mylarComicData = jsonData['data']['comic']

        if jsonData['success'] == "true":
            return True
        else:
            return False
    else:
        return False

def findVolumeDetails(series,year):
    found = False
    comicID = "Unknown"
    publisher = "Unknown"
    global searchCount
    global CVNotFound
    global CVFound
    #global CV

    if isinstance(series,str):
        searchCount += 1

        result_matches = 0
        preferred_matches = 0
        result_publishers = []
        result_matches_blacklist = 0
        issueCounter = 0

        series_matches = []
        publisher_blacklist_results = set()

        try:
            if VERBOSE: print("     Searching for %s (%s) on CV" % (series,year))
            
            session = Comicvine(api_key=CV_API_KEY, cache=SQLiteCache())
            searchparam = "name:" + series

            response = session.volume_list(params={"filter": searchparam})

            if len(response) == 0:
                print("     No results found for %s (%s)" % (series,year))
            else: #Results were found
                for result in response: #Iterate through CV results
                    #If exact series name and year match
                    if result.name.lower() == series.lower() and str(result.start_year) == year:

                        publisher_temp = result.publisher.name
                        result_publishers.append(publisher_temp)

                        series_matches.append(result)

                        if publisher_temp in PUBLISHER_BLACKLIST:
                            result_matches_blacklist += 1
                            publisher_blacklist_results.add(publisher_temp)
                        else:
                            found = True
                            result_matches += 1
                            publisher = publisher_temp
                            if publisher in PUBLISHER_PREFERRED: preferred_matches += 1
                            comicID = result.id_
                            numIssues = result.issue_count
                            print("         Found on comicvine: %s - %s (%s) : %s (%s issues)" % (publisher, series, year, comicID, numIssues))

                    #Handle multiple publisher matches
                if result_matches > 1:
                    print("             Warning: Multiple valid matches found! Publishers: %s" % (", ".join(result_publishers)))

                    #set result to preferred publisher
                    for item in series_matches:
                        if item['publisher']['name'] in PUBLISHER_PREFERRED or preferred_matches == 0:
                            numIssues = item['count_of_issues']
                            if numIssues > issueCounter:
                                #Current series has more issues than any other preferred results!
                                publisher = item['publisher']['name']
                                comicID = item['id']
                                issueCounter = numIssues
                                ## TODO: Remove "preferred text labels"
                                print("             Selected series from multiple results: %s - %s (%s issues)" % (publisher,comicID,numIssues))
                            else:
                                #Another series has more issues
                                print("             Skipped Series : %s - %s (%s issues) - another preferred series has more issues!" % (item['publisher']['name'],item['id'],numIssues))

                if len(response) == 0: # is this going to work?
                    print("         No results found for %s (%s)" % (series,year))

                if result_matches_blacklist > 0 and result_matches == 0:
                    #Only invalid results found
                    print("             No valid results found for %s (%s). %s blacklisted results found with the following publishers: %s" % (series,year,result_matches_blacklist, ",".join(publisher_blacklist_results)))
        except Exception as e:
            print("     There was an error processing %s (%s)" % (series,year))
            print(repr(e))

    #Update counters
    if not found:
        CVNotFound += 1
    else:
        CVFound += 1

    return [publisher,comicID]

def readExistingData():
    print("Reading data from %s" % (DATA_FILE))

    dataList = []

    if os.path.exists(DATA_FILE):
        #Import raw csv data as lines
        with open(DATA_FILE, mode='r') as csv_file:
            data = csv_file.readlines()
            #Parse csv data and strip whitespace
            for i in range(len(data)):
                if not i == 0: #Skip header row
                    fields = [x.strip() for x in data[i].split(",")]
                    dataList.append(fields)

    return dataList

def outputData(data):
    print("Exporting data to %s" % (OUTPUT_FILE))
    with open(OUTPUT_FILE, mode='w') as output_file:
        output_file.write("%s\n" % (",".join(CSV_HEADERS)))
        #Check if list contains multiple columns
        if len(data[0]) == 1:
            output_file.writelines(data)
        else:
            for row in data:
                output_file.write("%s\n" % (",".join(map(str,row))))

def index_2d(myList, v):
    for i, x in enumerate(myList):
        if v[0] == x[0] and v[1] == x[1]:
            return (i)

def mergeDataLists(list1, list2):
    # list1 = Main list with rows of 4 items
    # list2 = Import list with rows of 2 items
    print("Merging data lists")

    mainDataList = list1
    dataToMerge = list2
    global numExistingSeries
    global numCBLSeries
    global numNewSeries

    mainDataTitles = []
    mergedTitleSet = ()
    finalMergedList = []

    #Extract first 2 row elements to modified list
    for row in mainDataList:
        mainDataTitles.append([row[Column.SERIES], row[Column.YEAR]])

    mergedTitleList = mainDataTitles + dataToMerge
    mergedTitleList.sort()

    numExistingSeries = len(mainDataList)
    numCBLSeries = len(mergedTitleList)

    mergedTitleSet = set(tuple(map(tuple,mergedTitleList)))

    for row in mergedTitleSet:
        if list(row) in mainDataTitles:
          #Find index of exact match in mainDataSet
          match_row = index_2d(mainDataList,row)
          #if VERBOSE: print("Merged row: %s found in main data at row %s" % (list(row),match_row))

          finalMergedList.append(mainDataList[match_row])
          #Removing
          #if VERBOSE: print("Removing %s from mainDataList" % (list(row)))
          mainDataList.pop(match_row)

        else:
          #if VERBOSE: print("Merged row: %s NOT found in main data" % (list(row)))
          #Use the list with only
          newData = [row[Column.SERIES],row[Column.YEAR],"Unknown","Unknown",False]
          finalMergedList.append(newData)

    numNewSeries = len(finalMergedList) - numExistingSeries

    return finalMergedList


def main():
    global numExistingSeries
    global numCBLSeries
    global numNewSeries

    #Extract list from existing csv
    importData = readExistingData()

    #Process CBL files
    cblSeriesList = parseCBLfiles()
    
    #Process Wishlist
    #cblSeriesList = parseWishlist()

    
    #Merge csv data with cbl data
    mergedData = mergeDataLists(importData, cblSeriesList)
    mergedData.sort()

    print("Found %s series in CSV, %s new series in CBLs" % (numExistingSeries,numNewSeries))

    #Run all data checks in CV & Mylar
    for rowIndex in range(len(mergedData)):
        series = mergedData[rowIndex][Column.SERIES]
        year = mergedData[rowIndex][Column.YEAR]
        publisher = mergedData[rowIndex][Column.PUBLISHER]
        comicID = mergedData[rowIndex][Column.COMICID]
        inMylar = mergedData[rowIndex][Column.INMYLAR]
        checkMylar = False
        comicIDExists = comicID.isnumeric()

        #Check for new comicIDs
        if not comicIDExists or FORCE_RECHECK_CV:
            #Self-imposed search limit to prevent hitting limits
            if searchCount < CV_SEARCH_LIMIT:
                #sleeping at least 1 second is what comicvine reccomends. If you are more than 450 requests in 15 minutes (900 seconds) you will be rate limited. So if you are going to be importing for a straight 15 minutes (wow), then you would want to changet this to 2.
                if searchCount > 0: time.sleep(CV_API_RATE)

                #Update field in data list
                cv_data = findVolumeDetails(series,year)
                mergedData[rowIndex][Column.PUBLISHER] = cv_data[0]
                mergedData[rowIndex][Column.COMICID] = cv_data[1]

                #update vars for use elsewhere
                publisher = str(cv_data[0])
                comicID = str(cv_data[1])

        #Check if series exists in mylar
        if inMylar == "True":
            #Match exists in mylar
            if FORCE_RECHECK_MYLAR_MATCHES:
                #Force recheck anyway
                checkMylar = True
            else:
                checkMylar = False
        else:
            #No mylar match found
            checkMylar = True

        if checkMylar:
            #Update field in data list
            inMylar = isSeriesInMylar(comicID)
            mergedData[rowIndex][Column.INMYLAR] = inMylar

        #Add new series to Mylar
        if not inMylar and ADD_NEW_SERIES_TO_MYLAR:
            mergedData[rowIndex][Column.INMYLAR] = addSeriesToMylar(comicID)


    #Write modified data to file
    outputData(mergedData)

    #Print summary to terminal
    print("Total Number of Series From CSV File: %s, New Series Added From CBL Files: %s,  Existing Series (Mylar): %s,  Missing Series (Mylar): %s,  New Matches (CV): %s, Unfound Series (CV): %s" % (numExistingSeries,numNewSeries,mylarExisting,mylarMissing,CVFound,CVNotFound))

    ## TODO: Summarise list of publishers in results

main()