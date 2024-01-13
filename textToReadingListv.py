
import re
import os
import pandas as pd
#import sqlite3


# Code doesn't handle something like: Captain America (2004) #1 – #9, #11 – #14

rootDirectory = os.getcwd()
#dataDirectory = os.path.join(rootDirectory, "ReadingList-DB")
readingListDirectory = os.path.join(rootDirectory, "ReadingLists-Text")

#truthDB = os.path.join(dataDirectory, "truthDB2.db")
#truthDB = os.path.join(dataDirectory, "CMRO.db")
#truthDB = os.path.join(dataDirectory, "dbTruthTable-230312173308.db")

#SearchDB = False

#inputFile = 'inputtest.txt'
#dbFile = 'cmrolistgood.db'

yearPattern = r'\(([0-9]{4})\)'
yearRemovalString = r' \([0-9]{4}\)'
noteRemovalString = r'\([^)]*\)'

seedYearPattern = r'^[0-9]{4}$'

fromToPattern = r'#?\d+\s?(?:-|–)\s?#?\d+'
fromToPatternBeg = r'^#?\d+\s?(?:-|–)\s?#?\d+'
fromToPatternEnd = r'#?\d+\s?(?:-|–)\s?#?\d+$'


#oneCommaPattern = '\s?,\s?#?\d+'
oneCommaPatternBeg = r'^#?\d+\s?,\s?'
oneCommaPatternEnd= r'\s?,\s?#?\d+$'

twoCommaPattern = r'#?\d+\s?,\s?#?\d+'
twoCommaPatternBeg = r'^#?\d+\s?,\s?#?\d+'
twoCommaPatternEnd= r'#?\d+\s?,\s?#?\d+$'

threeCommaPattern = r'#?\d+\s?,\s?#?\d+,\s?#?\d+'
threeCommaPatternBeg = r'^#?\d+\s?,\s?#?\d+,\s?#?\d+'
threeCommaPatternEnd= r'#?\d+\s?,\s?#?\d+,\s?#?\d+$'




dfOrderList = ['SeriesName', 'SeriesStartYear', 'IssueNum', 'IssueType', 'CoverDate', 'Name', 'SeriesID', 'IssueID', 'CV Series Name', 'CV Series Year', 'CV Issue Number', 'CV Series Publisher', 'CV Cover Image', 'CV Issue URL', 'Days Between Issues']
index = 0

def getRange(issuerange):
    numbers = re.findall(r'\d+', issuerange)

    # Convert the numbers to integers and extract the range
    num_range = list(range(int(numbers[0]), int(numbers[1])+1))
    
    return num_range

#useSeedYears = True
#seedStartYear = input("Enter seed start year, return for none: ")
#seedEndYear = input("Enter seed end year, return for none: ")
#print(re.match(seedYearPattern,seedStartYear))
#print(re.match(seedYearPattern,seedEndYear))
#if not re.match(seedYearPattern,seedStartYear) or not re.match(seedYearPattern,seedEndYear):
#    print('Invalid entry, not using seed years')
#    useSeedYears = False

for root, dirs, files in os.walk(readingListDirectory):
        for file in files:
            if file.endswith(".txt"):
                inputfile = file
                print (file)
                inputFile = os.path.join(readingListDirectory, inputfile)
                print('Processing %s'%(inputfile))
                outputfile = file.replace('.txt', '.xlsx')
                outputFile = os.path.join(readingListDirectory, outputfile)
#                touchjsonfile = outputfile.replace('.xlsx','') + '.json'
#                touchjsonFile = os.path.join(readingListDirectory, touchjsonfile)
                if not os.path.exists(outputFile):


                    df = pd.DataFrame(columns=dfOrderList)
                    with open (inputFile, mode='r', encoding='utf-8') as file:

                        for line in file:
                            print(line)
                            if '#' in line:
                                yearReSearch = re.search(yearPattern,line)
                                year = 0
                                yearintext = False
                                if yearReSearch:
                                    
                                    year = re.search(yearPattern,line).group(1)
                                    
                                    line = re.sub(yearRemovalString,'',line)
                                    yearintext = True
                                #print(line)
                                line = re.sub(noteRemovalString,'',line)
                                titleNumSplit = line.split(' #',1)
                                series = titleNumSplit[0]
                                #print(series)
                                issuerange = titleNumSplit[1]
                                issuerange = issuerange.strip()
                                #print(issuerange)
                                issueNumPattern = r'\d+(\.\d+)?'
                                #issueNumPattern = r'\d+'
                                allnums = re.findall(issueNumPattern ,issuerange)
                                #print(len(allnums))

                                if len(allnums) == 1:
                                    df.loc[index, 'IssueNum'] = allnums[0]
                                    df.loc[index, 'SeriesName'] = series
                                    df.loc[index,'SeriesStartYear'] = year
                                    index += 1

                                if len(allnums) == 2:
                                    #print(re.search(fromToPattern,issuerange))
                                    if re.search(fromToPattern,issuerange):
                                        issuerangelist = getRange(issuerange)
                                        for issue in issuerangelist:
                                            print(series)
                                            print(issue)
                                            df.loc[index,'SeriesName'] = series
                                            df.loc[index,'IssueNum'] = issue
                                            df.loc[index,'SeriesStartYear'] = year
                                            index += 1
                                    if re.search(twoCommaPattern,issuerange):
                                        issuelist = re.findall(issueNumPattern, issuerange)
                                        for issue in issuelist:
                                            print(series)
                                            print(issue)
                                            df.loc[index,'SeriesName'] = series
                                            df.loc[index,'IssueNum'] = issue
                                            df.loc[index,'SeriesStartYear'] = year
                                            index += 1
                                if len(allnums) == 3:
                                    if re.search(fromToPatternBeg, issuerange) and re.search(twoCommaPatternEnd, issuerange):
                                        issueFromTo = re.sub(oneCommaPatternEnd,'', issuerange)
                                        issuerangelist = getRange(issueFromTo)
                                        for issue in issuerangelist:
                                            print(series)
                                            print(issue)
                                            df.loc[index,'SeriesName'] = series
                                            df.loc[index,'IssueNum'] = issue
                                            df.loc[index,'SeriesStartYear'] = year
                                            index += 1
                                        issuelist = re.findall(issueNumPattern, issuerange)
                                        df.loc[index,'SeriesName'] = series
                                        df.loc[index,'IssueNum'] = issuelist[2]
                                        df.loc[index,'SeriesStartYear'] = year
                                        index += 1
                                    if re.search(fromToPatternEnd, issuerange) and re.search(twoCommaPatternBeg, issuerange):
                                        issueFromTo = re.sub(oneCommaPatternBeg,'', issuerange)
                                        issuelist = re.findall(issueNumPattern, issuerange)
                                        print(series)
                                        print(issue)
                                        df.loc[index,'SeriesName'] = series
                                        df.loc[index,'IssueNum'] = issuelist[0]
                                        df.loc[index,'SeriesStartYear'] = year
                                        index += 1
                                        issuerangelist = getRange(issueFromTo)
                                        for issue in issuerangelist:
                                            print(series)
                                            print(issue)
                                            df.loc[index,'SeriesName'] = series
                                            df.loc[index,'IssueNum'] = issue
                                            df.loc[index,'SeriesStartYear'] = year
                                            index += 1
                                if len(allnums) == 4:
                                    print('length really is 4')
                                    print(issuerange)
                                    print(re.search(r"#?\d+\s?,\s?#?\d+", "119 – #120, #130, #121"))
                                    print(re.search(fromToPatternBeg, issuerange))
                                    
                                    if re.search(fromToPatternBeg, issuerange) and re.search(threeCommaPatternEnd, issuerange):
                                        print('4 fromtobeg, 3coma end')
                                        print(issuerange)
                                        issueFromTo = re.sub(twoCommaPatternEnd,'',issuerange)
                                        print(issueFromTo)
                                        issuerangelist = getRange(issueFromTo)
                                        for issue in issuerangelist:
                                            print(series)
                                            print(issue)
                                            df.loc[index,'SeriesName'] = series
                                            df.loc[index,'IssueNum'] = issue
                                            df.loc[index,'SeriesStartYear'] = year
                                            index += 1
                                        issuelist = re.findall(r'\d+', issuerange)
                                    
                                        print(series)
                                        print(issue)
                                        df.loc[index,'SeriesName'] = series
                                        df.loc[index,'IssueNum'] = issuelist[2]
                                        df.loc[index,'SeriesStartYear'] = year
                                        index += 1
                                        df.loc[index,'SeriesName'] = series
                                        df.loc[index,'IssueNum'] = issuelist[3]
                                        df.loc[index,'SeriesStartYear'] = year
                                        index += 1
                                        
                                    if re.search(fromToPatternEnd, issuerange) and re.search(threeCommaPatternBeg, issuerange):
                                        issueFromTo = re.sub(twoCommaPatternBeg,'', issuerange)
                                        issuelist = re.findall(r'\d+', issueFromTo)
                                        print(series)
                                        print(issue)
                                        df.loc[index,'SeriesName'] = series
                                        df.loc[index,'IssueNum'] = issuelist[0]
                                        df.loc[index,'SeriesStartYear'] = year
                                        index += 1
                                        df.loc[index,'SeriesName'] = series
                                        df.loc[index,'IssueNum'] = issuelist[1]
                                        df.loc[index,'SeriesStartYear'] = year
                                        index += 1
                                        issuerangelist = getRange(issueFromTo)
                                        for issue in issuerangelist:
                                            print(series)
                                            print(issue)
                                            df.loc[index,'SeriesName'] = series
                                            df.loc[index,'IssueNum'] = issue
                                            df.loc[index,'SeriesStartYear'] = year
                                            index += 1
                    
                    df.fillna({'SeriesStartYear':0}, inplace=True)
                    df = df.astype({'IssueNum':str, 'SeriesStartYear':int})

                    print(df)
                    df.to_excel(outputFile)
                    


'''
                    #try:
                    #    sqliteConnection = sqlite3.connect(truthDB,detect_types=sqlite3.PARSE_DECLTYPES)
                    #    cursor = sqliteConnection.cursor()

                    #except sqlite3.Error as error:
                    #    print("Error while connecting to sqlite", error)
                    for index, row in df.iterrows():
                        seriesName = row['SeriesName']
                        seriesStartYear = row['SeriesStartYear']
                        issueNum = row['IssueNum']
                        print(seriesName)
                        print(issueNum)
                        print(seriesStartYear)
                        if sqliteConnection and seriesStartYear == 0 and SearchDB:
                            # try:
                            yearSearch = cursor.execute(
                            "SELECT SeriesStartYear, CoverDate FROM comics WHERE SeriesName = ? AND IssueNum = ?",
                            (seriesName,issueNum),
                            ).fetchall()
                            yearSearch = cursor.execute(
                            'SELECT "CV Series Year", CoverDate FROM comics WHERE "CV Series Name" = ? AND "CV Issue Number" = ?',
                            (seriesName,issueNum),
                            ).fetchall()

                            print(type(yearSearch))
                            if len(yearSearch)  == 0:
                                
                                yearSearch = cursor.execute(
                                "SELECT SeriesStartYear, CoverDate FROM comics WHERE SeriesName = ? AND IssueNum = ?",
                                (seriesName,issueNum),
                                ).fetchall()
                                if len(yearSearch)  == 0:
                                    print('No match found in DB file')

                            if len(yearSearch) == 1:
                                seriesStartYear = yearSearch[0][0]
                                print('Match found in DB file')
                                print(seriesStartYear)
                                df.loc[index,'SeriesStartYear'] = seriesStartYear

                            if len(yearSearch) > 1:
                                print("Multiple Matches found...")
                                i = 0
                                for match in yearSearch:
                                    print(type(yearSearch[i][0]))
                                    print(yearSearch[i][0])
                                    if int(seedStartYear) <= int(yearSearch[i][1].year) <= int(seedEndYear):
                                        seriesStartYear = yearSearch[i][0]
                                    i += 1
                                df.loc[index,'SeriesStartYear'] = seriesStartYear
                                print(seriesName)
                                print(yearSearch)
                                
                                
                                
                                
                                
                                
                                
                                #  if useSeedYears:
                                #     for i in range(yearSearch:
                                #         if yearSearch[i] 
                                # seriesStartYear = yearSearch[0][0]
                                # print(seriesStartYear)
                                
                            # else:
                            #     seriesStartYear = yearSearch[0][0]
                            #     print(seriesStartYear)
                            #     df.loc[index,'SeriesStartYear'] = seriesStartYear

                            # except:
                            #     print('No match found in DB file')
'''

                    #open(touchjsonFile, 'w').close()

  