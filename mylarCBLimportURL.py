'''
This script will add the missing volumes from a CBL file to your mylar instance.
Find the CBL on github, click on the raw button and then paste in the URL when prompted.


1) In config.ini replace [MYLAR API KEY] with your Mylar3 api key
2) In config.ini replace [MYLAR SERVER ADDRESS] with your server in the format: http://servername:port/  (make sure to include the slash at the end)
'''

import requests
import json
import os
from enum import IntEnum
import xml.etree.ElementTree as ET
from glob import glob
from sys import argv
import configparser

config = configparser.ConfigParser(allow_no_value=True)

if os.path.exists('configPRIVATE.ini'): # an attempt to prevent me from sharing my api keys (again) :)
    config.read('configPRIVATE.ini')
else:
    config.read('config.ini')

VERBOSE = True
#Mylar prefs
mylarAPI = config['mylar']['mylarapi']
mylarBaseURL = config['mylar']['mylarbaseurl']

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

def getCBLURL():
    cblUrl = input('Enter in CBL URL from github [RAW]:')
    return cblUrl


def parseCBLfiles(URL):
    series_list = []

    response = requests.get(URL)
    #print (response.content)
    open('temp.cbl', 'wb').write(response.content)

    tree = ET.parse('temp.cbl')
    fileroot = tree.getroot()
    cblinput = fileroot.findall("./Books/Book")
    for series in cblinput:
        
        cblseries = series[0].attrib['Series']
        
        line = series.attrib['Series'].replace(",",""),series.attrib['Volume'],cblseries
        series_list.append(list(line))

    series_list_nodup = []
    for item in series_list:
        if item not in series_list_nodup:
            series_list_nodup.append(item)
    return series_list_nodup

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
    return False

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




def main():
    global numExistingSeries
    global numCBLSeries
    global numNewSeries
    missingSeriesList =[]
    cblURL = getCBLURL()

    #Process CBL files
    cblSeriesList = parseCBLfiles(cblURL)
    print(cblSeriesList)
    #Process Wishlist
    #cblSeriesList = parseWishlist()

    for series in cblSeriesList:
        print (series[2])
        inMylar = isSeriesInMylar(series[2])
        if not inMylar:
            missingSeriesList.append([series])
    print(missingSeriesList)
    addYN = input('Add missing series to mylar? (Y/N)')
    if addYN == 'Y' or addYN == 'y':
        for line in missingSeriesList:
            print(line[0][2]) 
            addSeriesToMylar(line[0][2])

main()