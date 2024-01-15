'''
This script will create an HTML file to allow you to see what series you have in mylar and which you are missing given a .CBL file.
Installation:
1) Download & install this package (required for searching the comicvine api):
   https://github.com/Metron-Project/Simyan
1b) Install all other requirements from the requirements.txt file as needed.
2) Create a folder called 'ReadingLists' in the same directory as the script and add any CBL files you want to process into this folder
3) In config.ini replace [MYLAR API KEY] with your Mylar3 api key
4) In config.ini replace [MYLAR SERVER ADDRESS] with your server in the format: http://servername:port/  (make sure to include the slash at the end)
5) In config.ini replace [CV API KEY] with your comicvine api key

'''

import requests
import json

import os

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
import base64
import pandas as pd
from PIL import Image
from io import BytesIO
from IPython.display import HTML
import datetime

from bs4 import BeautifulSoup as Soup



#HTML Format:
#From Search:
#Comic Name
#Publisher
#Year
#Issues
#Type (new)
#Add / Already in Library

#From This Week:
#Publisher
#Comic
# #  (number)
#Status
#Options
#red wanted
#green downloaded





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
dataDirectory = os.path.join(rootDirectory, "ReadingList-DB")
if not os.path.isdir(dataDirectory): os.mkdir(dataDirectory)

cvCacheFile = os.path.join(dataDirectory, "CV.db")
CACHE_RETENTION_TIME = 120 #days

IMAGE_DIR = os.path.join(rootDirectory, "CVCoverImages")
if not os.path.isdir(IMAGE_DIR): os.mkdir(IMAGE_DIR)



#Comic Vine:
CV_API_KEY = config['comicVine']['cv_api_key']


#Mylar prefs
mylarAPI = config['mylar']['mylarapi']
mylarBaseURL = config['mylar']['mylarbaseurl']


mylarAddURL = mylarBaseURL + 'api?apikey=' + mylarAPI + '&cmd=addComic&id='
mylarCheckURL = mylarBaseURL + 'api?apikey=' + mylarAPI + '&cmd=getComic&id='
mylarViewURL = mylarBaseURL + 'comicDetails?ComicID='

numNewSeries = 0
numExistingSeries = 0
numCBLSeries = 0

#Initialise counters
mylarExisting = 0
mylarMissing = 0
CVFound = 0
CVNotFound = 0
searchCount = 0



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
            book = {'seriesName':entry.attrib['Series'],'seriesYear':entry.attrib['Volume'],'issueNumber':entry.attrib['Number']}#,'issueYear':entry.attrib['Year']}
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

        #bookSet.add((curSeriesName,curSeriesYear,curIssueNumber))
        finalBookList.append([curSeriesName,curSeriesYear,curIssueNumber])
    #df = pd.DataFrame(bookSet, columns =['seriesName', 'seriesYear', 'issueNumber'])
    df = pd.DataFrame(finalBookList, columns =['seriesName', 'seriesYear', 'issueNumber'])
    df = df.drop('issueNumber', axis=1)
    #print(df)
    
    #df['issueID'] = 0
    #df.fillna({'issueNumber':0, 'issueID':0}, inplace=True)
    #df = df.astype({'issueNumber':str,'issueID':int})#.fillna(0)#,errors='ignore')#.fillna(0)#,'IssueID':'int'})


    df.rename(columns={'seriesName': 'SeriesName', 'seriesYear': 'SeriesStartYear'}, inplace=True)#, 'issueNumber': 'IssueNum', 'issueID':'IssueID'}, inplace=True)
    
    df['CV Cover Image'] = ''
    df['Number of Issues']
    df['Type']
    df['Publisher']
    
    return (df)




def parseCBLfilesIDsOnly():
    series_list = []
    print("Checking CBL files in %s" % (READINGLIST_DIR))
    for root, dirs, files in os.walk(READINGLIST_DIR):
        for file in files:
            if file.endswith(".cbl"):
                try:
                    filename = os.path.join(root, file)

                    print("Parsing %s" % (filename))
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
                except:
                    print("Unable to process file at %s" % ( os.path.join(str(root), str(file)) ))
    print(series_list)
    return series_list

def parseCBLIDsOnly(filename):
    series_list = []
    
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

    #print(series_list)
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
        print("         Match found for %s in Mylar" % (comicID))
        mylarExisting += 1
        return True
    else:
        print("         No match found for %s in Mylar" % (comicID))
        mylarMissing += 1
        return False

    #In the event of if else failure
    return False


def getVolumeDetails(seriesID):
    cvSeriesName = ''
    cvSeriesYear = ''
    cvSeriesPublisher = ''
    cvNumberIssues = ''
    cvFirstIssueID = ''
    cvDescription = ''
    cvDeck = ''

    if seriesID.isnumeric():

        try:
            print("     Searching for %s volume details on CV" % (str(seriesID)))
            #time.sleep(CV_API_RATE)
            session = Comicvine(api_key=CV_API_KEY, cache=SQLiteCache(cvCacheFile,CACHE_RETENTION_TIME))
            response = session.get_volume(seriesID)
            cvSeriesName = response.name
            cvSeriesYear = response.start_year
            cvSeriesPublisher = response.publisher.name
            cvNumberIssues = response.issue_count
            cvFirstIssueID = response.first_issue.id
            cvDescription = response.description
            cvDeck = response.summary

            

        except Exception as e:
            print("     There was an error processing %s" % (str(seriesID)))
            print(repr(e))


    return[cvSeriesName, cvSeriesYear, cvSeriesPublisher, cvNumberIssues,cvFirstIssueID, cvDescription, cvDeck]

def getIssueDetails(issueID):

    cvImageURL = ''
    cvIssueURL = ''
    coverDate = ''
    cvIssueNum = ''

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

def add_hyperlink_image(url,imagesrc):
    # target _blank to open new window
    return '<a target="_blank" href="{}">{}</a>'.format(url, imagesrc)

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
    try:
        if 'Add to mylar' in value:
            color = 'red'
        elif value == '':
            color = 'red'
        else:
            color = 'white'
    except:
        color= 'white'

    return 'background-color: %s' % color





def drophtml(html):
    if html is not None:
        soup = Soup(html, "html.parser")

        text_parts = soup.findAll(string=True)
        #print ''.join(text_parts)
        return ''.join(text_parts)
    else:
        return ''


def today():
    today = datetime.date.today()
    yyyymmdd = datetime.date.isoformat(today)
    return yyyymmdd


def findType(deckchunk, descchunk, number_issues, volumeYear):
    
    if deckchunk == None:
        deckchunk = 'None'
    if descchunk == None:
        descchunk = 'None'


#[Following code stolen from mylar3 :)]
#try:
    
    #used by the 'add a story arc' option to individually populate the Series Year for each series within the given arc.
    #series year is required for alot of functionality.
    #series = dom.getElementsByTagName('volume')
    #tempseries = {}
    

    '''
    # we need to know # of issues in a given series to force the type if required based on number of issues published to date.
    number_issues = dm.getElementsByTagName('count_of_issues')[0].firstChild.wholeText
    try:
        totids = len(dm.getElementsByTagName('id'))
        idc = 0
        while (idc < totids):
            if dm.getElementsByTagName('id')[idc].parentNode.nodeName == 'volume':
                tempseries['ComicID'] = dm.getElementsByTagName('id')[idc].firstChild.wholeText
            idc+=1
    except:
        logger.warn('There was a problem retrieving a comicid for a series within the arc. This will have to manually corrected most likely.')
        tempseries['ComicID'] = 'None'

    tempseries['Series'] = 'None'
    tempseries['Publisher'] = 'None'
    try:
        totnames = len(dm.getElementsByTagName('name'))
        namesc = 0
        while (namesc < totnames):
            if dm.getElementsByTagName('name')[namesc].parentNode.nodeName == 'volume':
                tempseries['Series'] = dm.getElementsByTagName('name')[namesc].firstChild.wholeText
                tempseries['Series'] = tempseries['Series'].strip()
            elif dm.getElementsByTagName('name')[namesc].parentNode.nodeName == 'publisher':
                tempseries['Publisher'] = dm.getElementsByTagName('name')[namesc].firstChild.wholeText
            namesc+=1
    except:
        logger.warn('There was a problem retrieving a Series Name or Publisher for a series within the arc. This will have to manually corrected.')

    try:
        tempseries['SeriesYear'] = dm.getElementsByTagName('start_year')[0].firstChild.wholeText
    except:
        logger.warn('There was a problem retrieving the start year for a particular series within the story arc.')
        tempseries['SeriesYear'] = '0000'

    #cause you know, dufus'...
    if tempseries['SeriesYear'][-1:] == '-':
        tempseries['SeriesYear'] = tempseries['SeriesYear'][:-1]
    '''
    desdeck = 0
    #the description field actually holds the Volume# - so let's grab it
    desc_soup = None

    try:
        #descchunk = dm.getElementsByTagName('description')[0].firstChild.wholeText
        #descchunk = comic_desc
        desc_soup = Soup(descchunk, "html.parser")
        desclinks = desc_soup.findAll('a')
        comic_desc = drophtml(descchunk)
        desdeck +=1
    except:
        comic_desc = 'None'
    
    #sometimes the deck has volume labels
    try:
        #deckchunk = dm.getElementsByTagName('deck')[0].firstChild.wholeText
        comic_deck = deckchunk
        desdeck +=1
    except:
        comic_deck = 'None'

    #comic['ComicDescription'] = comic_desc
    '''
    try:
        tempseries['Aliases'] = dm.getElementsByTagName('aliases')[0].firstChild.wholeText
        tempseries['Aliases'] = re.sub('\n', '##', tempseries['Aliases']).strip()
        if tempseries['Aliases'][-2:] == '##':
            tempseries['Aliases'] = tempseries['Aliases'][:-2]
        #logger.fdebug('Aliases: ' + str(aliases))
    except:
        tempseries['Aliases'] = 'None'
    '''
    volumeFound = 'None' #noversion'
    
    #figure out if it's a print / digital edition.
    volumeType = 'None'
    if comic_deck != 'None':
        if any(['print' in comic_deck.lower(), 'digital' in comic_deck.lower(), 'paperback' in comic_deck.lower(), 'one shot' in re.sub('-', '', comic_deck.lower()).strip(), 'hardcover' in comic_deck.lower()]):
            if all(['print' in comic_deck.lower(), 'reprint' not in comic_deck.lower()]):
                volumeType = 'Print'
            elif 'digital' in comic_deck.lower():
                volumeType = 'Digital'
            elif 'paperback' in comic_deck.lower():
                volumeType = 'TPB'
            elif 'graphic novel' in comic_deck.lower():
                volumeType = 'GN'
            elif 'hardcover' in comic_deck.lower():
                volumeType = 'HC'
            elif 'TPB' in comic_deck.lower():
                volumeType = 'HC'    
            elif 'oneshot' in re.sub('-', '', comic_deck.lower()).strip():
                volumeType = 'One-Shot'

            else:
                volumeType = 'Print'

    if comic_desc != 'None' and volumeType == 'None':
        if 'print' in comic_desc[:60].lower() and all(['also available as a print' not in comic_desc.lower(), 'for the printed edition' not in comic_desc.lower(), 'print edition can be found' not in comic_desc.lower(), 'reprints' not in comic_desc.lower()]):
            volumeType = 'Print'
        elif all(['digital' in comic_desc[:60].lower(), 'graphic novel' not in comic_desc[:60].lower(), 'digital edition can be found' not in comic_desc.lower()]):
            volumeType = 'Digital'
        elif all(['paperback' in comic_desc[:60].lower(), 'paperback can be found' not in comic_desc.lower()]) or all(['hardcover' not in comic_desc[:60].lower(), 'collects' in comic_desc[:60].lower()]):
            volumeType = 'TPB'
        elif all(['graphic novel' in comic_desc[:60].lower(), 'graphic novel can be found' not in comic_desc.lower()]):
            volumeType = 'GN'
        elif 'hardcover' in comic_desc[:60].lower() and 'hardcover can be found' not in comic_desc.lower():
            volumeType = 'HC'
        
        
        
        elif any(['one-shot' in comic_desc[:60].lower(), 'one shot' in comic_desc[:60].lower()]) and any(['can be found' not in comic_desc.lower(), 'following the' not in comic_desc.lower()]):
            i = 0
            volumeType = 'One-Shot'
            avoidwords = ['preceding', 'after the special', 'following the', 'continued from']
            while i < 2:
                if i == 0:
                    cbd = 'one-shot'
                elif i == 1:
                    cbd = 'one shot'
                tmp1 = comic_desc[:60].lower().find(cbd)
                if tmp1 != -1:
                    for x in avoidwords:
                        tmp2 = comic_desc[:tmp1].lower().find(x)
                        if tmp2 != -1:
                            #logger.fdebug('FAKE NEWS: caught incorrect reference to one-shot. Forcing to Print')
                            volumeType = 'Print'
                            i = 3
                            break
                i+=1
        else:
            volumeType = 'Print'

    if all([comic_desc != 'None', 'trade paperback' in comic_desc[:30].lower(), 'collecting' in comic_desc[:40].lower()]):
        #ie. Trade paperback collecting Marvel Team-Up #9-11, 48-51, 72, 110 & 145.
        #logger.info('comic_desc: %s' % comic_desc)
        #logger.info('desclinks: %s' % desclinks)
        issue_list = []
        micdrop = []
        if desc_soup is not None:
            #if it's point form bullets, ignore it cause it's not the current volume stuff.
            test_it = desc_soup.find('ul')
            if test_it:
                for x in test_it.findAll('li'):
                    if any(['Next' in x.findNext(text=True), 'Previous' in x.findNext(text=True)]):
                        mic_check = x.find('a')
                        micdrop.append(mic_check['data-ref-id'])

        for fc in desclinks:
            try:
                fc_id = fc['data-ref-id']
            except Exception:
                continue

            if fc_id in micdrop:
                continue
            fc_name = fc.findNext(text=True)
            if fc_id.startswith('4000'):
                fc_cid = None
                fc_isid = fc_id
                iss_start = fc_name.find('#')
                issuerun = fc_name[iss_start:].strip()
                fc_name = fc_name[:iss_start].strip()
            elif fc_id.startswith('4050'):
                fc_cid = fc_id
                fc_isid = None
                issuerun = fc.next_sibling
                try: #added flips
                    if issuerun is not None:
                        lines = re.sub("[^0-9]", ' ', issuerun).strip().split(' ')
                        if len(lines) > 0:
                            for x in sorted(lines, reverse=True):
                                srchline = issuerun.rfind(x)
                                if srchline != -1:
                                    try:
                                        if issuerun[srchline+len(x)] == ',' or issuerun[srchline+len(x)] == '.' or issuerun[srchline+len(x)] == ' ':
                                            issuerun = issuerun[:srchline+len(x)]
                                            break
                                    except Exception as e:
                                        #logger.warn('[ERROR] %s' % e)
                                        continue
                    else:
                        iss_start = fc_name.find('#')
                        issuerun = fc_name[iss_start:].strip()
                        fc_name = fc_name[:iss_start].strip()

                    if issuerun.endswith('.') or issuerun.endswith(','):
                        #logger.fdebug('Changed issuerun from %s to %s' % (issuerun, issuerun[:-1]))
                        issuerun = issuerun[:-1]
                    if issuerun.endswith(' and '):
                        issuerun = issuerun[:-4].strip()
                    elif issuerun.endswith(' and'):
                        issuerun = issuerun[:-3].strip()
                except: #added flips
                    continue
            else:
                continue
                #    except:
                #        pass
            issue_list.append({'series':   fc_name,
                                'comicid':  fc_cid,
                                'issueid':  fc_isid,
                                'issues':   issuerun})

        #logger.info('Collected issues in volume: %s' % issue_list)
#        tempseries['Issue_List'] = issue_list
#    else:
#        tempseries['Issue_List'] = 'None'

    volume_found = None
    while (desdeck > 0):
        if desdeck == 1:
            if comic_desc == 'None':
                comicDes = comic_deck[:30]
            else:
                #extract the first 60 characters
                comicDes = comic_desc[:60].replace('New 52', '')
        elif desdeck == 2:
            #extract the characters from the deck
            comicDes = comic_deck[:30].replace('New 52', '')
        else:
            break

        i = 0
        looped_once = False
        while (i < 2):
            if 'volume' in comicDes.lower():
                #found volume - let's grab it.
                v_find = comicDes.lower().find('volume')

                if all([comicDes.lower().find('annual issue from') > 0, volume_found is not None, looped_once is False]):
                    #logger.fdebug('wrong annual declaration found previously. Attempting to correct')
                    cd_find = comic_desc.lower().find('annual issue from') + 17
                    comicDes = comic_desc[cd_find:cd_find+30]
                    if 'volume' in comicDes.lower():
                        v_find = comicDes.lower().find('volume') #_desc[cd_find:cd_find+45].lower().find('volume')
                        if i == 1:
                            i = 0
                        looped_once = True
                        volume_found = None

                #arbitrarily grab the next 10 chars (6 for volume + 1 for space + 3 for the actual vol #)
                #increased to 10 to allow for text numbering (+5 max)
                #sometimes it's volume 5 and ocassionally it's fifth volume.
                if i == 0:
                    vfind = comicDes[v_find:v_find +15]   #if it's volume 5 format
                    basenums = {'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10', 'i': '1', 'ii': '2', 'iii': '3', 'iv': '4', 'v': '5'}
                    #logger.fdebug('volume X format - %s: %s' % (i, vfind))
                else:
                    vfind = comicDes[:v_find]   # if it's fifth volume format
                    basenums = {'zero': '0', 'first': '1', 'second': '2', 'third': '3', 'fourth': '4', 'fifth': '5', 'sixth': '6', 'seventh': '7', 'eighth': '8', 'nineth': '9', 'tenth': '10', 'i': '1', 'ii': '2', 'iii': '3', 'iv': '4', 'v': '5'}
                    #logger.fdebug('X volume format - %s: %s' % (i, vfind))
                for nums in basenums:
                    if nums in vfind.lower():
                        sconv = basenums[nums]
                        vfind = re.sub(nums, sconv, vfind.lower())
                        break

                #now we attempt to find the character position after the word 'volume'
                if i == 0:
                    volthis = vfind.lower().find('volume')
                    volthis = volthis + 6  # add on the actual word to the position so that we can grab the subsequent digit
                    vfind = vfind[volthis:volthis + 4]  # grab the next 4 characters ;)
                elif i == 1:
                    volthis = vfind.lower().find('volume')
                    vfind = vfind[volthis - 4:volthis]  # grab the next 4 characters ;)

                if '(' in vfind:
                    #bracket detected in versioning'
                    vfindit = re.findall('[^()]+', vfind)
                    vfind = vfindit[0]
                vf = re.findall('[^<>]+', vfind)
                try:
                    ledigit = re.sub("[^0-9]", "", vf[0])
                    if ledigit != '' and volume_found is None:
                        volume_found = ledigit
                        volumeFound = ledigit
                        #logger.fdebug("Volume information found! Adding to series record : volume %s" % volume_found)
                except:
                    pass

                i += 1
            else:
                i += 1
        volumeFound = volume_found

        if volumeFound == 'None':
            #logger.fdebug('tempseries[Volume]: %s' % volumeFound)
            desdeck -= 1
        else:
            break
    
    if all([int(number_issues) == 1, str(volumeYear) < today()[:4], volumeType != 'One-Shot', volumeType != 'TPB', volumeType != 'HC', volumeType != 'GN']):
    
        booktype = 'One-Shot'
    else:
        booktype = volumeType
        #added flips
    if 'value priced reprint' in comic_desc[:60].lower() or 'digest book which reprints' in comic_desc[:60].lower() or 'epic collection' in comic_desc[:60].lower():
        booktype = 'Reprint'

    #except:
    #    booktype = 'Unknown'
    '''
    serieslist.append({"ComicID":    tempseries['ComicID'],
                        "ComicName":  tempseries['Series'],
                        "SeriesYear": tempseries['SeriesYear'],
                        "Publisher":  tempseries['Publisher'],
                        "Volume":     volumeFound,
                        "Aliases":    tempseries['Aliases'],
                        "Type":       booktype})
    '''
    #print(booktype)
    if booktype == 'None':
        booktype = 'Unknown'
        
    return volumeType










def main():
    global numExistingSeries
    global numCBLSeries
    global numNewSeries
    
    
    countFile = 0
    
    print("Checking CBL files in %s" % (READINGLIST_DIR))
    for root, dirs, files in os.walk(READINGLIST_DIR):
        for file in files:
            if file.endswith(".cbl"):
                try:
                    filename = os.path.join(root, file)

                    print("Parsing %s" % (filename))
                    cblSeriesList = parseCBLIDsOnly(filename)
                    cblSeriesList = list(set(cblSeriesList))


                except:
                    print("Unable to process file at %s" % ( os.path.join(str(root), str(file)) ))

    
                #cblSeriesList = parseCBLfilesIDsOnly()
                #inputfile = filename
                outputhtmlfile = os.path.join(READINGLIST_DIR, file.replace('.cbl','') + '.html')

                #cblSeriesList = set(cblSeriesList)
                countFile += 1
                
                df = pd.DataFrame(columns =['SeriesID', 'CoverImage', 'Volume', 'Type', 'Number of Issues', 'Publisher', 'Release Date', 'Add to Mylar'])
                df['SeriesID'] = cblSeriesList
                CoverImage = []
                Volume = []
                Type = []
                Publisher = []
                ReleaseDate = []
                AddToMylar = []
                numberIssues = []
                missingSeriesIDs = []

                countSeries = 0
                countInMylar = 0
                countNotInMylar = 0

                for seriesID in cblSeriesList:
                    countSeries += 1
                # return[cvSeriesName, cvSeriesYear, cvSeriesPublisher, cvNumberIssues,cvFirstIssueID, cvDescription, cvDeck]

                    volumedetails = getVolumeDetails(seriesID)
                    #print (volumedetails)
                    cvSeriesName = volumedetails[0]
                    cvSeriesYear = volumedetails[1]
                    cvSeriesPublisher = volumedetails[2]
                    cvNumberIssues = volumedetails[3]
                    cvFirstIssueID = volumedetails[4]
                    cvDescription = volumedetails[5]
                    cvDeck = volumedetails[6]
                    volumeString = ''
                    volumeString = cvSeriesName + ' (' + str(cvSeriesYear) +')'
                    cvURL = 'https://comicvine.gamespot.com/volume/4050-' + str(seriesID) + '/'
                    titleLink = '<a target="_blank" href="{}">{}</a>'.format(cvURL, volumeString)
                    #Volume.append(volumeString)
                    Volume.append(titleLink)
                    Publisher.append(cvSeriesPublisher)



                    cvIssueDetails = getIssueDetails(cvFirstIssueID)
                    cvImageURL = cvIssueDetails[0]
                    cvIssueURL = cvIssueDetails[1]
                    coverDate = cvIssueDetails[2]
                    cvIssueNum = cvIssueDetails[3]

                    numberIssues.append(cvNumberIssues)
                    #def findType(deckchunk, descchunk, number_issues, volumeYear):
                    seriesType = findType(cvDeck, cvDescription, cvNumberIssues, cvSeriesYear)
                    Type.append(seriesType)


                    ReleaseDate.append(coverDate)

                    imageFileName = str(cvFirstIssueID) + '.jpg'
                    imageFilePath = os.path.join(IMAGE_DIR, imageFileName)

                    try:
                        imageFilePath = getcvimage(cvFirstIssueID,cvImageURL)
                        coverImage = get_thumbnail(imageFilePath)
                        coverImage = image_formatter(imageFilePath)
                    except:
                        #imageFilePath = 'bork'
                        print('Not able to load issueID image from %s'%(imageFilePath))




                    # #print(imageFilePath)
                    # if os.path.exists(imageFilePath):
                    #     try: 
                    #         coverImage = get_thumbnail(imageFilePath)
                    #         coverImage = image_formatter(imageFilePath)
                    #         #print('image exists')
                    #     except:
                    #         print('Not able to load issueID image from %s'%(imageFilePath))
                    # else:
                    #     try: 
                    #         # cvIssueDetails = getIssueDetails(issueID)
                    #         # cvImageURL = cvIssueDetails[0]
                    #         # cvIssueURL = cvIssueDetails[1]
                    #         # coverDate = cvIssueDetails[2]
                    #         # cvIssueNum = cvIssueDetails[3]
                    #         imageFilePath = getcvimage(cvFirstIssueID,cvImageURL)
                    #         print('image doesnt exist')
                    #         coverImage = get_thumbnail(imageFilePath)
                    #         coverImage = image_formatter(imageFilePath)
                            
                    #     except:
                    #         print('Not able to load issueID image from %s'%(imageFilePath))

                    coverImage = add_hyperlink_image(cvImageURL,coverImage)
                    
                    CoverImage.append(coverImage)

                    seriesInMylar = isSeriesInMylar(seriesID)
                    if seriesInMylar:
                        countInMylar += 1
                        mylarURL = mylarViewURL+ str(seriesID)
                        mylarURLHTML = '<a target="_blank" href="{}">{}</a>'.format(mylarURL, 'View in mylar')

                    else:
                        countNotInMylar += 1
                        comicAddURL = "%s%s" % (mylarAddURL, str(seriesID))
                        mylarURLHTML = '<a target="_blank" href="{}">{}</a>'.format(comicAddURL, 'Add to mylar')
                        missingSeriesIDs.append(seriesID)
                
                    AddToMylar.append(mylarURLHTML)




                            

                df['Volume'] = Volume
                df['Publisher'] = Publisher
                df['Release Date'] = ReleaseDate
                
                df['CoverImage'] = CoverImage
                df['Add to Mylar'] = AddToMylar
                df['Type'] = Type
                df['Number of Issues'] = numberIssues

                df.sort_values('Release Date')
                
                if len(missingSeriesIDs) == 0:
                    mylarURLaddAllHTML ='  [All series in mylar]'
                
                else:
                    mylarURLaddAllHTML = '<button onclick="openMultipleLinks()">Add all missing to mylar</button>\n  <script>\nfunction openMultipleLinks() {\nvar urls = [\n'
                    for missingID in missingSeriesIDs:
                        mylarURLaddAllHTML = mylarURLaddAllHTML + '\'' + mylarAddURL + missingID + '\',\n'
                    pattern = re.compile(r',$')    
                    mylarURLaddAllHTML = re.sub(pattern, '      \n];\nurls.forEach(function(url) {\nwindow.open(url, \'_blank\');\n});\n}\n</script>', mylarURLaddAllHTML)




                    #missingSeriesIDString = ','.join(str(item) for item in missingSeriesIDs)
                    #comicAddAllURL = "%s%s" % (mylarAddURL, missingSeriesIDString)
                    #mylarURLaddAllHTML = '<a target="_blank" href="{}">{}</a>'.format(comicAddAllURL, 'Add all missing series to mylar')


                summaryText = 'Total Series: ' + str(countSeries) + '  |   In mylar: ' + str(countInMylar) + '  |   Missing in mylar: ' + str(countNotInMylar) + '    ' + mylarURLaddAllHTML
                #print(df)
                df = df.style.set_table_styles(
                            [{"selector": "", "props": [("border", "1px solid grey")]},
                            {"selector": "tbody td", "props": [("border", "1px solid grey")]},
                            {"selector": "th", "props": [("border", "1px solid grey")]}
                            ]).set_caption(summaryText).map(color_cels)#.format({'CV Issue URL': make_clickable})#.to_html(outputhtmlfile)#,formatters={'CV Cover Image': image_formatter}, escape=False)
                df.to_html(outputhtmlfile)




'''
    #Check for new comicIDs
    if not comicIDExists or FORCE_RECHECK_CV:
        #Self-imposed search limit to prevent hitting limits
        if searchCount < CV_SEARCH_LIMIT:
            #sleeping at least 1 second is what comicvine reccomends. If you are more than 450 requests in 15 minutes (900 seconds) you will be rate limited. So if you are going to be importing for a straight 15 minutes (wow), then you would want to changet this to 2.
            #if searchCount > 0: time.sleep(CV_API_RATE)#removed and using Simyan's rate limiting.

            #Update field in data list
            cv_data = findVolumeDetails(series,year)
            mergedData[rowIndex][Column.PUBLISHER] = cv_data[0]
            mergedData[rowIndex][Column.COMICID] = cv_data[1]

            #update vars for use elsewhere
            publisher = str(cv_data[0])
            comicID = str(cv_data[1])

    #Check if series exists in mylar
    if inMylar == True:
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
    if not ADD_NEW_SERIES_TO_MYLAR:
        print("ADD_NEW_SERIES_TO_MYLAR set to false, no series added to mylar. Below are only simulated results:")
    print("Total Number of Series From CSV File: %s, New Series Added From CBL Files: %s,  Existing Series (Mylar): %s,  Missing Series (Mylar): %s,  New Matches (CV): %s, Unfound Series (CV): %s" % (numExistingSeries,numNewSeries,mylarExisting,mylarMissing,CVFound,CVNotFound))

    ## TODO: Summarise list of publishers in results
'''

main()