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


rootDirectory = os.getcwd()
dataDirectory = os.path.join(rootDirectory, "ReadingList-DB")
cvSeriesDB = os.path.join(dataDirectory, "yearInReview-Type.db")
YearInReviewDirectory = os.path.join(rootDirectory, "ReadingList-YearInReview")
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


def main():

    mylarIDs = getAllSeries()
    print(len(mylarIDs))

    try:
        sqliteConnection = sqlite3.connect(cvSeriesDB,detect_types=sqlite3.PARSE_DECLTYPES)
        cur = sqliteConnection.cursor()
        
    except sqlite3.Error as error:
        print("Error while connecting to sqlite", error)


    for pubid in PubIDs:
        print('now working on publisher %s' % (pubid))




        yearChart = []
        totalChart = []
        haveChart = []
        missingChart = []

        publisherChart = ''

        for year in range (minYear, maxYear):
            print('now working on %s' % (year))
            
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


            allSeries = cur.execute(
                'SELECT * FROM volumes WHERE "CV Series PublisherID" = ? AND "CV Series Year" = ?',
                (pubid, year),
                ).fetchall()

            if not len(allSeries) == 0:
                countAllSeries = len(allSeries)
                lines = []
                y = 0
                publisherChart = allSeries[0][5]
                publisherChart = publisherChart.replace("/", "-")  # Replace "/" with "-"
                file = '[' + publisherChart + '] ' + str(year) + '.html'
                yearChart.append(year)
                outputhtmlfile = os.path.join(YearInReviewDirectory, file)

                
                for x in allSeries:
                    #print(allSeries)
                    #print(allSeries[y][12])
                    if allSeries[y][12] in KeepTypes:
                        countSeries +=1
                        #lines.append (str(allSeries[y][1]) +';' + str(allSeries[y][7]) + '\n')
                        seriesID = allSeries[y][1]
                        seriesName = allSeries[y][2]
                        seriesYear = allSeries[y][3]
                        seriesPublisher = allSeries[y][5]
                        
                        seriesIssueCount = allSeries[y][6]
                        seriesType = allSeries[y][12]
                        cover = allSeries[y][17]
                        try:
                            cover_date = allSeries[y][18]
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


                summaryText = 'Total Series: ' + str(countSeries) + '  |   In mylar: ' + str(countInMylar) + '  |   Missing in mylar: ' + str(countNotInMylar) + '    ' + mylarURLaddAllHTML
                resultsSingleLine = f'{allSeries[0][5]};{str(year)};{str(countSeries)};{str(countInMylar)};{str(countNotInMylar)}'
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



        with open(resultsFile, 'w', encoding='utf-8') as f:
            f.writelines(resultsLines)


main()
