'''
This script will quickly import the IDs from the CBL files with minimal API calls.
Installation:
1) Install all the requirements from requirements.txt file as needed.
2) Create a folder called 'ReadingLists' in the same directory as the script and add any CBL files you want to process into this folder
3) In config.ini replace [MYLAR API KEY] with your Mylar3 api key
4) In config.ini replace [MYLAR SERVER ADDRESS] with your server in the format: http://servername:port/  (make sure to include the slash at the end)

'''

import requests
import json
import os
import xml.etree.ElementTree as ET
import configparser

# If you have add all missing issues automatically when you add a series you can set this to False.
# Setting to True will mark all missing issues as wanted that are in the CBL file.
ANALYZE_ISSUES = False

# User configurable:
# Setting issues to Wanted will only be done on the issueStatusNOK list
issueStatusOK = ['Wanted','Downloaded', 'Archived']
issueStatusNOK = ['Skipped','Ignored','Failed']



config = configparser.ConfigParser(allow_no_value=True)

if os.path.exists('configPRIVATE.ini'): # an attempt to prevent me from sharing my api keys (again) :)
    config.read('configPRIVATE.ini')
else:
    config.read('config.ini')

#File prefs
rootDirectory = os.getcwd()

#SCRIPT_DIR = os.getcwd()
READINGLIST_DIR = os.path.join(rootDirectory, "ReadingLists")
if not os.path.isdir(READINGLIST_DIR): os.mkdir(READINGLIST_DIR)


#Mylar prefs
mylarAPI = config['mylar']['mylarapi']
mylarBaseURL = config['mylar']['mylarbaseurl']


mylarAddURL = mylarBaseURL + 'api?apikey=' + mylarAPI + '&cmd=addComic&id='
mylarCheckURL = mylarBaseURL + 'api?apikey=' + mylarAPI + '&cmd=getComic&id='
mylarViewURL = mylarBaseURL + 'comicDetails?ComicID='
mylarIssueCheckURL = mylarBaseURL + 'api?apikey=' + mylarAPI + '&cmd=getIssueInfo&id='
mylarIssueWanted = mylarBaseURL + 'api?apikey=' + mylarAPI + '&cmd=queueIssue&id='


def parseCBLIDsOnly(filename):
    series_list = []
    issue_list = []
    tree = ET.parse(filename)
    fileroot = tree.getroot()
    cblinput = fileroot.findall("./Books/Book")
    for series in cblinput:
        try:
            cblseries = series[0].attrib['Series']
        except:
            cblseries = 'Unknown'
        #line = series.attrib['Series'].replace(",",""),series.attrib['Volume'],'Unknown',cblseries
        line = cblseries
        #series_list.append(list(line))
        series_list.append(line)

        try:
            cblissue = series[0].attrib['Issue']
        except:
            cblissue = 'Unknown'
        #line = series.attrib['Series'].replace(",",""),series.attrib['Volume'],'Unknown',cblseries
        lineissue = cblissue
        #series_list.append(list(line))
        issue_list.append(lineissue)


    #print(series_list)
    return [series_list, issue_list]


def isSeriesInMylar(comicID):
    found = False

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
        print("         Match found for %s in Mylar" % (comicID))
        return True
    else:
        print("         No match found for %s in Mylar" % (comicID))
        return False

    #In the event of if else failure
    return False


def isIssueInMylar(comicID):
 

    #print("Checking if comicID %s exists in Mylar" % (comicID))

    if comicID.isnumeric():
        comicCheckURL = "%s%s" % (mylarIssueCheckURL, str(comicID))
        #print(comicCheckURL)
        mylarData = requests.get(comicCheckURL).text
        jsonData = json.loads(mylarData)
        #jsonData = mylarData.json()
        mylarComicData = jsonData
        
        if not mylarComicData['success']:
            issueStatus = 'Missing'
        else:
            issueStatus = mylarComicData['data'][0]['status']


    #In the event of if else failure
    return issueStatus

def addSeriesToMylar(comicID):
    if comicID.isnumeric():
        print("         Adding %s to Mylar" % (comicID))
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

def watchIssueMMylar(comicID):
    if comicID.isnumeric():
        print("         Setting %s to Wanted" % (comicID))
        comicAddURL = "%s%s" % (mylarIssueWanted, str(comicID))
        mylarData = requests.get(comicAddURL).text

        ## Check result of API call
        #jsonData = json.loads(mylarData)
        #jsonData = mylarData.json()
        #mylarComicData = jsonData['data']['comic']

        if mylarData == 'OK':
            return True
        else:
            return False
    else:
        return False




# Function to ask a yes/no question with a default answer
def ask_yes_no_question(question, default_answer):
    while True:
        user_input = input(f"{question} [{default_answer}]: ").upper()
        if user_input in ['Y', 'N']:
            return user_input
        elif not user_input:
            return default_answer
        else:
            print("Please enter Y for Yes or N for No.")



def main():
    global numExistingSeries
    global numCBLSeries
    global numNewSeries
    
    missingSeriesIDs = []
    OKSeriesIDs = []
    errorSeriesIDs = []
    missingIssueIDs = []
    OKIssueIDs = []
    NOKIssueIDs = []
    errorIssueIDs = []
    numCBLfiles = 0

    
    
    print("Checking CBL files in %s" % (READINGLIST_DIR))
    for root, dirs, files in os.walk(READINGLIST_DIR):
        for file in files:
            if file.endswith(".cbl"):
                
                try:
                    filename = os.path.join(root, file)

                    print("Parsing %s" % (filename))
                    cblIDList = parseCBLIDsOnly(filename)
                    
                    cblSeriesList = list(set(cblIDList[0]))
                    cblIssueList = list(set(cblIDList[1]))
                    #print(cblSeriesList)
                    #print(cblIssueList)
                    numCBLfiles +=1

                except:
                    print("Unable to process file at %s" % ( os.path.join(str(root), str(file)) ))

    

                for seriesID in cblSeriesList:

                    seriesInMylar = isSeriesInMylar(seriesID)
                    if not seriesInMylar:
                        missingSeriesIDs.append(seriesID)
                    else:
                        OKSeriesIDs.append(seriesID)
                if ANALYZE_ISSUES:
                    
                    for issueID in cblIssueList:
                        issue_status = isIssueInMylar(issueID)
                        if issue_status == 'Missing':
                            missingIssueIDs.append(issue_status)
                        if issue_status in issueStatusNOK:
                            NOKIssueIDs.append(issueID)
                        if issue_status in issueStatusOK:
                            OKIssueIDs.append(issueID)
                        else:
                            errorIssueIDs.append(issueID)
                
    print(f'Analyzed: {numCBLfiles} CBL files')
    seriesNumTotal = len(missingSeriesIDs) + len(OKSeriesIDs)
    issueNumTotal = len(OKIssueIDs) + len(NOKIssueIDs) + len(missingIssueIDs)
    print(f'Total Series IDs Found: {seriesNumTotal}')
    print(f'     Series IDs Missing in Mylar: {len(missingSeriesIDs)}')
    if ANALYZE_ISSUES:
        print(f'Total Issue IDs Foud: {issueNumTotal}')
        print(f'     Issue IDs Unmonitored in Mylar: {len(NOKIssueIDs)}')
        print(f'     Issue IDs Missing in Mylar: {len(missingIssueIDs)}')
    
    if not len(missingSeriesIDs) == 0:
        add_series = ask_yes_no_question("Add all missing series to mylar?", "Y")
    
        if add_series =='Y':
            for id in missingSeriesIDs:
                addSeriesToMylar(id)
                if not addSeriesToMylar:
                    print(f'Error adding {id} to mylar.')
        else:
            print(f'No changes made')
    if len(missingSeriesIDs) == 0:
        print(f'All Series already in mylar, nothing added.')
  

    if ANALYZE_ISSUES and not len(NOKIssueIDs) == 0:
        add_issues = ask_yes_no_question("Set all unmonitored issues to Wanted?", "Y")
        if add_issues =='Y':
            for id in NOKIssueIDs:
                watchIssueMMylar(id)
                if not watchIssueMMylar:
                    print(f'Error setting {id} to wanted.')
        else:
            print(f'No changes made')          
    if ANALYZE_ISSUES and len(NOKIssueIDs) == 0 and len(missingIssueIDs) == 0:
        print(f'All issues already monitored in mylar, nothing changed.')
    if ANALYZE_ISSUES and not len(missingIssueIDs) ==0:
        print(f'Re-run the script to add the {len(missingIssueIDs)} missing issues after waiting for mylar to add and the missing series.')

main()