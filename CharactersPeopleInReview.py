import requests
import json
import time
import os
import re
import csv
import configparser
import sqlite3
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

#charID = 1780 #Aunt May
#charID = 58731 #Norah?

rootDirectory = os.getcwd()
dataDirectory = os.path.join(rootDirectory, "ReadingList-DB")
cvSeriesDB = os.path.join(dataDirectory, "yearInReview-Type.db")
charPeopleDB = os.path.join(dataDirectory, "charactersPeopleDB.db")

YearInReviewDirectory = os.path.join(rootDirectory, "ReadingList-CharPeopleReview")
if not os.path.isdir(YearInReviewDirectory): os.makedirs(YearInReviewDirectory)
resultsLines = []
resultsLines.append(f'Publisher;Year;Total Series;In Mylar;Missing\n')

timeString = datetime.today().strftime("%y%m%d%H%M%S")
resultsFile = os.path.join(YearInReviewDirectory, "results-%s.csv" % (timeString))

df = pd.DataFrame()   

config = configparser.ConfigParser(allow_no_value=True)

if os.path.exists('configPRIVATE.ini'): # an attempt to prevent me from sharing my api keys (again) :)
    config.read('configPRIVATE.ini')
else:
    config.read('config.ini')

PUBLISHER_BLACKLIST = ["Panini Comics","Editorial Televisa","Planeta DeAgostini","Unknown","Urban Comics","Dino Comics","Ediciones Zinco","Abril","Panini Verlag","Panini España","Panini France","Panini Brasil","Egmont Polska","ECC Ediciones","RW Edizioni","Titan Comics","Dargaud","Federal", "Marvel UK/Panini UK","Grupo Editorial Vid","JuniorPress BV","Pocket Books", "Caliber Comics", "Panini Comics","Planeta DeAgostini","Newton Comics","Atlas Publishing","Panini Rus"]

minYear = config['yearinreview']['startyear']
maxYear = config['yearinreview']['endyear']
minYear = int(minYear)
maxYear = int(maxYear)
KeepTypes = config['yearinreview']['booktypes'].split(',')
PubIDs = config['yearinreview']['pubidsetting'].split(',')
mylarAPI = config['mylar']['mylarapi']
mylarBaseURL = config['mylar']['mylarbaseurl']

mylarCheckURL = mylarBaseURL + 'api?apikey=' + mylarAPI + '&cmd=getComic&id='
mylarGetAllURL = mylarBaseURL + 'api?apikey=' + mylarAPI + '&cmd=getIndex'
mylarAddURL = mylarBaseURL + 'api?apikey=' + mylarAPI + '&cmd=addComic&id='
mylarViewURL = mylarBaseURL + 'comicDetails?ComicID='


def getAllSeries():
    IDlist = []
    global newIssueCounter
    print("         Pulling all series data from mylar")
    print(f'         API URL:{mylarGetAllURL}')
    try :
        mylarAllData = requests.get(mylarGetAllURL).text
    except requests.exceptions.RequestException as e:
        print('Exiting...   Something wrong with mylar API config')
        raise SystemExit(e)

    jsonAllData = json.loads(mylarAllData)
    print(f"         Found {len(jsonAllData['data'])} series in mylar") 
    # Don't use headers, but might at a later date
    #headers = ['ComicID', 'Publisher Name', 'Series Name', 'Series Year Begins', 'Issue Number']
    
    for line in range(len(jsonAllData['data'])):
        comicID =  jsonAllData['data'][line]['id']
        IDlist.append(comicID)
    return(IDlist)

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
def get_search_mode():
    while True:
        mode = input("Enter C to search Character IDs, enter P to search PeopleIDs: ").strip().upper()
        if mode == 'C':
            return 'character'
        elif mode == 'P':
            return 'people'
        else:
            print("Invalid input. Please enter 'C' for Character IDs or 'P' for PeopleIDs.")

def get_textID_mode():
    while True:
        mode = input("Enter C to search Character IDs, enter P to search PeopleIDs: ").strip().upper()
        if mode == 'C':
            return 'character'
        elif mode == 'P':
            return 'people'
        else:
            print("Invalid input. Please enter 'C' for Character IDs or 'P' for PeopleIDs.")

def get_id(prompt):
    while True:
        user_input = input(prompt).strip()
        if user_input.isdigit():
            return user_input
        else:
            print("Invalid input. Please enter a numeric ID.")


def main():

    cpMode = get_search_mode()
    print(f"Search mode set to: {cpMode}")

    textOrID = 0
    charID = get_id(f"Enter {cpMode} ID to search: ")

    mylarIDs = getAllSeries()
    #print(len(mylarIDs))

    try:
        sqliteConnection = sqlite3.connect(cvSeriesDB,detect_types=sqlite3.PARSE_DECLTYPES)
        cur = sqliteConnection.cursor()
        print("Loaded Volume DB")

    except sqlite3.Error as error:
        print("Error while connecting to sqlite", error)

    update_query = f"""
        UPDATE volumes
        SET "CV Series Year" = TRIM("CV Series Year")
    """

    cur.execute(update_query)

    try:
        sqliteConnectionCP = sqlite3.connect(charPeopleDB,detect_types=sqlite3.PARSE_DECLTYPES)
        curCP = sqliteConnectionCP.cursor()
        print("Loaded Character People DB")
        
    except sqlite3.Error as error:
        print("Error while connecting to sqlite", error)





    yearChart = []
    totalChart = []
    haveChart = []
    missingChart = []

    publisherChart = ''



    #for year in range (minYearPub, maxYearPub+1):
    print('Now working on %s:' % (charID))
    
    df = pd.DataFrame(columns =['SeriesID', 'CoverImage', 'Volume', 'Type', 'Number of Issues', 'Publisher', 'Release Date', 'Add to Mylar'])
    CoverImage = []
    Volume = []
    Type = []
    Publisher = []
    ReleaseDate = []
    AddToMylar = []
    numberIssues = []
    missingSeriesIDs = []
    seriesIDList = []

    countSeries = 0
    countInMylar = 0
    countNotInMylar = 0

    if cpMode == 'character':
            
        charVolumes = curCP.execute(
            'SELECT * FROM characters WHERE "charid" = ?',
            (charID,),
            ).fetchall()
        charName = curCP.execute(
            'SELECT * FROM characterIDs WHERE "charid" = ?',
            (charID,),
            ).fetchone()
        cvLink = 'https://comicvine.gamespot.com/character/4005-' + charID + '/'
    if cpMode == 'people':
        charVolumes = curCP.execute(
            'SELECT * FROM people WHERE "personid" = ?',
            (charID,),
            ).fetchall()

        charName = curCP.execute(
            'SELECT * FROM peopleIDs WHERE "charid" = ?',
            (charID,),
            ).fetchone()

        cvLink = 'https://comicvine.gamespot.com/person/4040-' + charID + '/'
    print(charName[1])
    file = str(charName[1]) +' (' + str(charName[0]) + ')' + '.html'
    #yearChart.append(year)
    outputhtmlfile = os.path.join(YearInReviewDirectory, file)
    for x in charVolumes:
        #print(allSeries)
        #print(allSeries[y][12])
        #print(x)
        allSeries = cur.execute(
            'SELECT * from volumes WHERE SeriesID = ?',
            (x[0],),
            ).fetchone()
        #print(volType)


        if not len(allSeries) == 0:
            countAllSeries = len(allSeries)
            lines = []
            y = 0
            #publisherChart = allSeries[0][5]
            #publisherChart = publisherChart.replace("/", "-")  # Replace "/" with "-"


            #print(allSeries[12])

            
            

            if allSeries[12] in KeepTypes and not allSeries[5] in PUBLISHER_BLACKLIST:
                countSeries +=1
                #lines.append (str(allSeries[y][1]) +';' + str(allSeries[y][7]) + '\n')
                seriesID = allSeries[1]
                #print(seriesID)
                seriesName = allSeries[2]
                #print(seriesName)
                seriesYear = allSeries[3]
                seriesPublisher = allSeries[5]
                
                seriesIssueCount = allSeries[6]
                seriesType = allSeries[12]
                cover = allSeries[18]
                try:
                    cover_date = allSeries[17]
                except:
                    cover_date = ''
                volumeString = seriesName + ' (' + str(seriesYear) +')'
                cvURL = 'https://comicvine.gamespot.com/volume/4050-' + str(seriesID) + '/'
                #titleLink = '<a target="_blank" href="{}">{}</a>'.format(cvURL, volumeString)
                titleLink = '<a href="{}">{}</a>'.format(cvURL, volumeString)

                if str(seriesID) in mylarIDs:

                    countInMylar += 1
                    mylarURL = mylarViewURL+ str(seriesID)
                    mylarURLHTML = '<a href="{}">{}</a>'.format(mylarURL, 'View in mylar')
                    #print('Found in mylar')

                else:
                    countNotInMylar += 1
                    comicAddURL = "%s%s" % (mylarAddURL, str(seriesID))
                    mylarURLHTML = '<a href="{}">{}</a>'.format(comicAddURL, 'Add to mylar')
                    missingSeriesIDs.append(seriesID)
            
                AddToMylar.append(mylarURLHTML)
                volumeString = seriesName + ' (' + str(seriesYear) +')'
                cvURL = 'https://comicvine.gamespot.com/volume/4050-' + str(seriesID) + '/'
                titleLink = '<a href="{}">{}</a>'.format(cvURL, volumeString)
                #titleLink = '<a target="_blank" href="{}">{}</a>'.format(cvURL, volumeString)

                #Volume.append(volumeString)
                Volume.append(titleLink)
                Publisher.append(seriesPublisher)
                numberIssues.append(seriesIssueCount)
                Type.append(seriesType)
                CoverImage.append(cover)
                ReleaseDate.append(cover_date)
                seriesIDList.append(seriesID)

            y = y + 1

                
    df['SeriesID'] = seriesIDList
    df['Volume'] = Volume
    df['Publisher'] = Publisher
    df['Release Date'] = ReleaseDate
    df['Release Date'] = pd.to_datetime(df['Release Date'])
    df['Release Date'] = df['Release Date'].dt.date
    
    df['CoverImage'] = CoverImage
    df['Add to Mylar'] = AddToMylar
    df['Type'] = Type
    df['Number of Issues'] = numberIssues

    df = df.sort_values('Release Date')
    
    if len(missingSeriesIDs) == 0:
        mylarURLaddAllHTML ='  [All series in mylar]'
    
    else:
        mylarURLaddAllHTML = '<button onclick="openMultipleLinks()">Add all missing to mylar</button>\n  <script>\nfunction openMultipleLinks() {\nvar urls = [\n'
        for missingID in missingSeriesIDs:
            mylarURLaddAllHTML = mylarURLaddAllHTML + '\'' + mylarAddURL + str(missingID) + '\',\n'
        pattern = re.compile(r',$')    
        mylarURLaddAllHTML = re.sub(pattern, '      \n];\nurls.forEach(function(url) {\nwindow.open(url, \'_blank\');\n});\n}\n</script>', mylarURLaddAllHTML)




        #missingSeriesIDString = ','.join(str(item) for item in missingSeriesIDs)
        #comicAddAllURL = "%s%s" % (mylarAddURL, missingSeriesIDString)
        #mylarURLaddAllHTML = '<a target="_blank" href="{}">{}</a>'.format(comicAddAllURL, 'Add all missing series to mylar')

    cvlinkhtml = '<a href = ' + cvLink + '>'+ charID + '</a>'
    #print(cvlinkhtml)
    summaryText = str(charName[1]) + ' (' + cvlinkhtml + ')' + ': Total Series: ' + str(countSeries) + '  |   In mylar: ' + str(countInMylar) + '  |   Missing in mylar: ' + str(countNotInMylar) + '    ' + mylarURLaddAllHTML
    resultsSingleLine = f'{charName[1]};{str(countSeries)};{str(countInMylar)};{str(countNotInMylar)}'
    totalChart.append(countSeries)
    haveChart.append(countInMylar)
    missingChart.append(countNotInMylar)
    #f'Publisher;Year;Total Series;In Mylar;Missing')
    #resultsLines.append(f'Publisher: {allSeries[0][5]}\n{str(year)}\n')
    resultsLines.append(f'{resultsSingleLine}\n')

    #print(df)
    df = df.style.set_table_styles(
                [{"selector": "", "props": [("border", "1px solid grey")]},
                {"selector": "tbody td", "props": [("border", "1px solid grey")]},
                {"selector": "th", "props": [("border", "1px solid grey")]}
                ]).set_caption(summaryText).map(color_cels)#.format({'CV Issue URL': make_clickable})#.to_html(outputhtmlfile)#,formatters={'CV Cover Image': image_formatter}, escape=False)
    df.to_html(outputhtmlfile)
    print(f'HTML file exported to`: {outputhtmlfile}')
    '''
    publisherChart = publisherChart.replace("/", "-")
    chartfilename = '[' + publisherChart + '] Summary Chart.html'
    chartTitle = publisherChart + ' Summary ' + datetime.today().strftime("%Y-%B-%d")
    outputchartfile = os.path.join(YearInReviewDirectory, chartfilename)

    
    fig = go.Figure(data=[
        go.Bar(name='Total Series', x=yearChart, y=totalChart),
        
        #go.Bar(name='Missing', x=yearList, y=missing),
        go.Bar(name='In Mylar', x=yearChart, y=haveChart)
    ])
    # Change the bar mode
    fig.update_layout(barmode='overlay', title=chartTitle)
    #fig.show()
    fig.write_html(outputchartfile, auto_open=False)


    '''
    with open(resultsFile, 'w', encoding='utf-8') as f:
        f.writelines(resultsLines)


main()