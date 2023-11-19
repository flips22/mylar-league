import sqlite3
import pandas as pd
import os
import re

rootDirectory = os.getcwd()
dataDirectory = os.path.join(rootDirectory, "ReadingList-DB")
readingListDirectory = os.path.join(rootDirectory, "ReadingList-CBRO")


cbrodbfile = os.path.join(dataDirectory, "ripcbro.db")

#cbrodbfile = 'ripcbro.db'

dfOrderList = ['SeriesName', 'SeriesStartYear', 'IssueNum', 'IssueType', 'CoverDate', 'Name', 'SeriesID', 'IssueID', 'CV Series Name', 'CV Series Year', 'CV Issue Number', 'CV Series Publisher', 'CV Cover Image', 'CV Issue URL', 'Days Between Issues']


MERGE_EVENTS = True

try:
    sqliteConnection = sqlite3.connect(cbrodbfile,detect_types=sqlite3.PARSE_DECLTYPES)
    cursor = sqliteConnection.cursor()


except sqlite3.Error as error:
    print("Error while connecting to sqlite", error)


#truthMatch = cursor.execute(
#                            "SELECT * FROM comics WHERE SeriesName = ? AND SeriesStartYear = ? AND IssueNum = ?",
#                            (seriesName,seriesStartYear,dbissueNum),
#                            ).fetchall()


#df = pd.read_sql_query("SELECT * from comics WHERE ", sqliteConnection)

#dfRLs = pd.read_sql_query("SELECT * from ReadingListsView", sqliteConnection)
#print(dfRLs)

readingLists = cursor.execute(
                            "SELECT * FROM ReadingListsView",
                            ).fetchall()
print(type(readingLists))
print(readingLists[1][1])

#df = pd.DataFrame(columns = ['hrnum', 'pubdate', 'title', 'series', 'start_year', 'issue','story'])

def main():

    for lists in readingLists:
        olnum = lists[0]
        print(olnum)
        listname = lists[1]
        listname = listname.replace(':','')
        listname = listname.replace('/','-')
        listname = listname.replace("???","'")
        listname = listname.replace("?","")
        
        if 'Marvel' in listname:
            listname = listname.replace('Marvel Events ','')
            listname = '[Marvel] ' + listname + ' (WEB-CBRO)'
        if 'DC' in listname:
            listname = listname.replace('DC Events ','')
            listname = '[DC Comics] ' + listname + ' (WEB-CBRO)'
        if 'New 52' in listname:
            listname = '[DC Comics] ' + listname
            
        inputfile = listname
        inputFile = os.path.join(readingListDirectory, inputfile)
        print('Processing %s'%(inputfile))
        #outputfile = file.replace('.txt', '-USER.xlsx')
        outputfile = inputfile + '.xlsx'
        outputFile = os.path.join(readingListDirectory, outputfile)
        touchjsonfile = outputfile.replace('.xlsx','') + '.json'
        touchjsonFile = os.path.join(readingListDirectory, touchjsonfile)
        
        issueList = cursor.execute(
                                "SELECT * FROM ReadingListDetailsView WHERE olistnum = ?",
                            (olnum,),
                                ).fetchall()
        comicList = []

        #hrnum = []
        pubdate = []
        title = []
        series = []
        startyear = []
        issuenum = []
        story = []
        hrnum = []
        hrnumsheet =[]
        #hrnumevent = []
        '''
        for issue in issueList:
            #dfRL = pd.read_sql_query("SELECT * from ComicsView WHERE hrnum = ?",(issue) sqliteConnection)
            hrnum = issue[1]
            
            #dfRL = pd.read_sql_query("SELECT * from ComicsView WHERE hrnum = ?", sqliteConnection, params=[hrnum])

            comic = cursor.execute(
                            "SELECT * FROM ComicsView WHERE hrnum = ?",
                            (hrnum,),
                            ).fetchall()
            comic = [item for t in comic for item in t]
            #print(comic[3])
            #print(hrnum,)
            #print(comic[0][0])
            
            try:
                
                hrnum.append(comic[0])
                pubdate.append(comic[1])
                title.append(comic[2])
            # print(pubdate)
                series.append(comic[3])
                startyear.append(comic[4])
                issuenum.append(comic[5])
                story.append(comic[6])
                #print(title)
            except:
                continue


            #print(comic[0][5])
            comicList.append(comic)
            print(comicList)
            #dfRL = pd.DataFrame(comicList,columns=['hrnum', 'pubdate', 'title', 'series', 'start_year', 'issue','story'])
            #print(dfRL)

        '''

        for issue in issueList:
            hrnum.append(issue[1])

        # Query for comics using hrnum and fetch the data
        for hrnum_val in hrnum:
            comic = cursor.execute("SELECT * FROM ComicsView WHERE hrnum = ?", (hrnum_val,)).fetchone()
            #print(comic[0])

            if comic:
                '''
                if comic[0]:
                    hrnumsheet.append(comic[0])
                    #print(hrnumsheet)
                else:
                    hrnumsheet.append(None)
                if comic[1]:
                    pubdate.append(comic[1])
                else:
                    pubdate.append(None)
                if comic[2]:
                    title.append(comic[2])
                else:
                    title.append(None)
                if comic[3]:
                    series.append(comic[3])
                else:
                    series.append(None)
                if comic[4]:
                    startyear.append(comic[4])
                else:
                    startyear.append(None)
                if comic[5]:
                    issuenum.append(comic[5])
                else:
                    issuenum.append(None)
                if comic[6]:
                    story.append(comic[6])
                else:
                    story.append(None)
                '''
                if "@231" in comic[3]:
                    print('found you')
                
                if '@' in comic[3] and MERGE_EVENTS:
                    print('event time')
                    hrnumevent=[]
                    eventmerge = comic[3].replace('@','')
                    eventissueList = cursor.execute(
                                "SELECT * FROM ReadingListDetailsView WHERE olistnum = ?",
                            (eventmerge,),
                                ).fetchall()
                    for eventissues in eventissueList:
                        hrnumevent.append(eventissues[1])
                    for hrnum_event in hrnumevent:
                        eventcomic = cursor.execute("SELECT * FROM ComicsView WHERE hrnum = ?", (hrnum_event,)).fetchone()
                        #print(comic[0])

                        if '@' in eventcomic[3] and MERGE_EVENTS:
                            print('embeddednevent time')
                            hrnumevent2=[]
                            eventmerge2 = eventcomic[3].replace('@','')
                            eventissueList2 = cursor.execute(
                                        "SELECT * FROM ReadingListDetailsView WHERE olistnum = ?",
                                    (eventmerge2,),
                                        ).fetchall()
                            for eventissues2 in eventissueList2:
                                hrnumevent2.append(eventissues2[1])
                            for hrnum_event2 in hrnumevent2:
                                eventcomic2 = cursor.execute("SELECT * FROM ComicsView WHERE hrnum = ?", (hrnum_event2,)).fetchone()
                                #print(comic[0])

                                if eventcomic2[4]:
                                    hrnumsheet.append(eventcomic2[0])
                                    pubdate.append(eventcomic2[1])
                                    title.append(eventcomic2[2])
                                    eventseriesclean =_cleanSeriesName(eventcomic2[3])
                                    series.append(eventseriesclean)
                                    #series.append(eventcomic2[3])
                                    startyear.append(eventcomic2[4])
                                    issuenum.append(eventcomic2[5])
                                    story.append(eventcomic2[6])

                        if eventcomic[4]:
                            hrnumsheet.append(eventcomic[0])
                            pubdate.append(eventcomic[1])
                            title.append(eventcomic[2])
                            eventseriesclean =_cleanSeriesName(eventcomic[3])
                            series.append(eventseriesclean)
                            #series.append(eventcomic[3])
                            startyear.append(eventcomic[4])
                            issuenum.append(eventcomic[5])
                            story.append(eventcomic[6])
                        
                 
                if comic[4]:
                    hrnumsheet.append(comic[0])
                    pubdate.append(comic[1])
                    title.append(comic[2])
                    seriesclean =_cleanSeriesName(comic[3])
                    series.append(seriesclean)
                    #series.append(comic[3])

                    startyear.append(comic[4])
                    issuenum.append(comic[5])
                    story.append(comic[6])
            

                #print(series)
        #df['hrnum'] = series
        # Create the DataFrame
        #print(len(hrnum))
    #    df = pd.DataFrame({
    #        'hrnum': hrnumsheet,
    #        'pubdate': pubdate,
    #        'title': title,
    #        'series': series,
    #        'start_year': startyear,
    #        'issue': issuenum,
    #        'story': story
    #    })

        #dfOrderList = ['SeriesName', 'SeriesStartYear', 'IssueNum', 'IssueType', 'CoverDate', 'Name', 'SeriesID', 'IssueID', 'CV Series Name', 'CV Series Year', 'CV Issue Number', 'CV Series Publisher', 'CV Cover Image', 'CV Issue URL', 'Days Between Issues']

        df = pd.DataFrame(
            {
            #'hrnum': hrnumsheet,
            #'pubdate': pubdate,
            #'title': title,
            'SeriesName': series,
            'SeriesStartYear': startyear,
            'IssueNum': issuenum,
            #'story': story
            },columns=dfOrderList)



        

        #print(df)

        df.fillna({'SeriesStartYear':0}, inplace=True)
        df.fillna({'IssueNum':0}, inplace=True)
        #df = df.astype({'IssueNum':int, 'SeriesStartYear':int})
        df = df.astype({'SeriesStartYear':int})
        

        #print(df)
        df.to_excel(outputFile)
        
        open(touchjsonFile, 'w').close()


    
    '''
        for line in comicList:
            #print(line)
            linelist = [item for t in line for item in t]
            print(line[0][0])



            #print(title)
            #print(series)
            #df['series'] = series
            #print(df)
        #print(comicList)
        
        dfRL = pd.DataFrame(comicList,columns=['hrnum', 'pubdate', 'title', 'series', 'start_year', 'issue','story'])
        #print(dfRL)
        exit()
        #print(len(comicList))

    '''
    sqliteConnection.close()


def _cleanSeriesName(seriesName: str):
    volPattern = r'(?P<seriesName>.*?) *(Vol(ume)?\.?) *\(?(?P<volumeNum>\d+)?\)?$'
    patterns = {
        'volume': volPattern + '$',
        'volumeAnnual': volPattern + r' *(?P<annualTag>Annual)$',
        'year': r'(?P<seriesName>.*?) *\(?(?P<seriesYear>19[2-9]\d|20[0-4]\d|\'\d{2})\)?$'
    }

    newSeriesName = seriesName
    
    if seriesName is not None and isinstance(seriesName, str):
        # Regex to strip annual, volume, year etc. from name
        for type, pattern in patterns.items():
            match = re.search(pattern, seriesName, re.IGNORECASE)
            if match:
                matchDict = match.groupdict()
                # Regex match found
                newSeriesName = matchDict['seriesName']
                if 'annualTag' in matchDict:
                    newSeriesName += matchDict['annualTag']

                break
    
    newSeriesName =newSeriesName.replace("???","'")
    return newSeriesName

main()