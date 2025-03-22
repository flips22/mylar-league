import configparser
import os
from urllib.parse import urlparse
#import requests
import json
import xml.etree.ElementTree as ET
import sys
import subprocess

try:
    import requests  # Try importing requests
except ImportError:
    print("requests module not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    print("requests installed successfully!")
    import requests  # Import again after installation

# If you have add all missing issues automatically when you add a series you can set this to False.
# Setting to True will mark all missing issues as wanted that are in the CBL file.
# Default setting is False, can be udpated in the config.ini file.
ANALYZE_ISSUES = False

# User configurable:
# Setting issues to Wanted will only be done on the issueStatusNOK list
issueStatusOK = ['Wanted','Downloaded', 'Archived']
issueStatusNOK = ['Skipped','Ignored','Failed']




config = configparser.ConfigParser(allow_no_value=True)

if os.path.exists('configDnD.ini'): 
    config.read('configDND.ini')
else:
    noconfig=True

#File prefs
rootDirectory = os.getcwd()


CONFIG_FILE = "configDND.ini"

def load_config():
    config = configparser.ConfigParser()
    
    # Check if file exists and is not empty
    if os.path.exists(CONFIG_FILE) and os.path.getsize(CONFIG_FILE) > 0:
        config.read(CONFIG_FILE)
        return config
    else:
        return None

def get_user_input():
    while True:
        http_address = input("Enter your mylar server address (e.g., http://example.com:8080): ").strip()
        parsed_url = urlparse(http_address)

        if parsed_url.scheme and parsed_url.hostname and parsed_url.port:
            break
        else:
            print("Invalid address. Please enter a valid HTTP address with a port.")

    api_key = input("Enter you mylar API key, found in settings, web interface: ").strip()

    return parsed_url.scheme, parsed_url.hostname, parsed_url.port, api_key

def save_config(scheme, server, port, api_key):
    baseurl = scheme + '://' + server + ':'+ str(port) +'/'
    print(baseurl)
    config = configparser.ConfigParser()
    config["mylar"] = {
        "mylarbaseurl": baseurl,
        "mylarapi": api_key
    }

    with open(CONFIG_FILE, "w") as configfile:
        config.write(configfile)

    print("Configuration saved successfully.")

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

    config = load_config()
    
    if config is None:
        print("No valid config file found. Setting up a new configuration.")
        scheme, server, port, api_key = get_user_input()
        save_config(scheme, server, port, api_key)
        config = load_config()
        print(config)
    mylarAPI = config['mylar']['mylarapi']
    mylarBaseURL = config['mylar']['mylarbaseurl']
    print(mylarAPI)
    print(mylarBaseURL)
    global mylarAddURL
    global mylarCheckURL
    global mylarViewURL 
    global mylarIssueCheckURL
    global mylarIssueWanted

    mylarAddURL = mylarBaseURL + 'api?apikey=' + mylarAPI + '&cmd=addComic&id='
    mylarCheckURL = mylarBaseURL + 'api?apikey=' + mylarAPI + '&cmd=getComic&id='
    mylarViewURL = mylarBaseURL + 'comicDetails?ComicID='
    mylarIssueCheckURL = mylarBaseURL + 'api?apikey=' + mylarAPI + '&cmd=getIssueInfo&id='
    mylarIssueWanted = mylarBaseURL + 'api?apikey=' + mylarAPI + '&cmd=queueIssue&id='

    


    try:
        filename = sys.argv[1]  # Get the first argument (the dropped file)

        print("Parsing %s" % (filename))
        cblIDList = parseCBLIDsOnly(filename)
        
        cblSeriesList = list(set(cblIDList[0]))
        cblIssueList = list(set(cblIDList[1]))
        #print(cblSeriesList)
        #print(cblIssueList)
        numCBLfiles +=1

    except:
        print("Unable to process file")
        input("Press Enter to exit...")


    for seriesID in cblSeriesList:

        seriesInMylar = isSeriesInMylar(seriesID)
        if not seriesInMylar:
            missingSeriesIDs.append(seriesID)
        else:
            OKSeriesIDs.append(seriesID)

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

    input("Press Enter to exit...")

 

if __name__ == "__main__":
    main()
