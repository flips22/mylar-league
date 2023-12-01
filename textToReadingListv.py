
import re
import os
import pandas as pd
import sqlite3


# Code doesn't handle something like: Captain America (2004) #1 – #9, #11 – #14

rootDirectory = os.getcwd()
dataDirectory = os.path.join(rootDirectory, "ReadingList-DB")
readingListDirectory = os.path.join(rootDirectory, "ReadingLists-Text")

#truthDB = os.path.join(dataDirectory, "truthDB2.db")
#truthDB = os.path.join(dataDirectory, "CMRO.db")
truthDB = os.path.join(dataDirectory, "dbTruthTable-230312173308.db")

inputFile = 'inputtest.txt'
dbFile = 'cmrolistgood.db'

yearPattern = '\(([0-9]{4})\)'
yearRemovalString = ' \([0-9]{4}\)'

seedYearPattern = '^[0-9]{4}$'

fromToPattern = '#?\d+\s?(?:-|–)\s?#?\d+'
fromToPatternBeg = '^#?\d+\s?(?:-|–)\s?#?\d+'
fromToPatternEnd = '#?\d+\s?(?:-|–)\s?#?\d+$'


#oneCommaPattern = '\s?,\s?#?\d+'
oneCommaPatternBeg = '^#?\d+\s?,\s?'
oneCommaPatternEnd= '\s?,\s?#?\d+$'


twoCommaPattern = '#?\d+\s?,\s?#?\d+'
twoCommaPatternBeg = '^#?\d+\s?,\s?#?\d+'
twoCommaPatternEnd= '#?\d+\s?,\s?#?\d+$'

threeCommaPattern = '#?\d+\s?,\s?#?\d+,\s?#?\d+'
threeCommaPatternBeg = '^#?\d+\s?,\s?#?\d+,\s?#?\d+'
threeCommaPatternEnd= '#?\d+\s?,\s?#?\d+,\s?#?\d+$'




dfOrderList = ['SeriesName', 'SeriesStartYear', 'IssueNum', 'IssueType', 'CoverDate', 'Name', 'SeriesID', 'IssueID', 'CV Series Name', 'CV Series Year', 'CV Issue Number', 'CV Series Publisher', 'CV Cover Image', 'CV Issue URL', 'Days Between Issues']
index = 0

def getRange(issuerange):
    numbers = re.findall(r'\d+', issuerange)

    # Convert the numbers to integers and extract the range
    num_range = list(range(int(numbers[0]), int(numbers[1])+1))
    
    return num_range

useSeedYears = True
seedStartYear = input("Enter seed start year, return for none: ")
seedEndYear = input("Enter seed end year, return for none: ")
print(re.match(seedYearPattern,seedStartYear))
print(re.match(seedYearPattern,seedEndYear))
if not re.match(seedYearPattern,seedStartYear) or not re.match(seedYearPattern,seedEndYear):
    print('Invalid entry, not using seed years')
    useSeedYears = False

for root, dirs, files in os.walk(readingListDirectory):
        for file in files:
            if file.endswith(".txt"):
                inputfile = file
                print (file)
                inputFile = os.path.join(readingListDirectory, inputfile)
                print('Processing %s'%(inputfile))
                outputfile = file.replace('.txt', '.xlsx')
                outputFile = os.path.join(readingListDirectory, outputfile)
                touchjsonfile = outputfile.replace('.xlsx','') + '.json'
                touchjsonFile = os.path.join(readingListDirectory, touchjsonfile)
                if not os.path.exists(outputFile):


                    df = pd.DataFrame(columns=dfOrderList)
                    with open (inputFile, mode='r', encoding='utf-8') as file:

                        for line in file:
                            if '#' in line:
                                yearReSearch = re.search(yearPattern,line)
                                year = 0
                                yearintext = False
                                if yearReSearch:
                                    
                                    year = re.search(yearPattern,line).group(1)
                                    
                                    line = re.sub(yearRemovalString,'',line)
                                    yearintext = True
                                #print(line)
                                titleNumSplit = line.split(' #',1)
                                series = titleNumSplit[0]
                                #print(series)
                                issuerange = titleNumSplit[1]
                                issuerange = issuerange.strip()
                                #print(issuerange)
                                
                                allnums = re.findall('\d+',issuerange)
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
                                        issuelist = re.findall(r'\d+', issuerange)
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
                                        issuelist = re.findall(r'\d+', issuerange)
                                        df.loc[index,'SeriesName'] = series
                                        df.loc[index,'IssueNum'] = issuelist[2]
                                        df.loc[index,'SeriesStartYear'] = year
                                        index += 1
                                    if re.search(fromToPatternEnd, issuerange) and re.search(twoCommaPatternBeg, issuerange):
                                        issueFromTo = re.sub(oneCommaPatternBeg,'', issuerange)
                                        issuelist = re.findall(r'\d+', issuerange)
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

                    try:
                        sqliteConnection = sqlite3.connect(truthDB,detect_types=sqlite3.PARSE_DECLTYPES)
                        cursor = sqliteConnection.cursor()

                    except sqlite3.Error as error:
                        print("Error while connecting to sqlite", error)

                    for index, row in df.iterrows():
                        seriesName = row['SeriesName']
                        seriesStartYear = row['SeriesStartYear']
                        issueNum = row['IssueNum']
                        print(seriesName)
                        print(issueNum)
                        print(seriesStartYear)
                        if sqliteConnection and seriesStartYear == 0:
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

                    df.fillna({'SeriesStartYear':0}, inplace=True)
                    df = df.astype({'IssueNum':int, 'SeriesStartYear':int})

                    print(df)
                    df.to_excel(outputFile)
                    
                    open(touchjsonFile, 'w').close()

                        
                                    

'''                                
                                
                                if ', ' in issuerange:
                                    titlecommasplit = line.split(', ')
                                    print(titlecommasplit[0])
                                    print(titlecommasplit[1])
                                    for issuerangeChunk in titlecommasplit:
                                        if '–' in issuerangeChunk:
                                            print(issuerangeChunk)
                                            issuerangelist = getRange(issuerangeChunk)
                                            for issue in issuerangelist:
                                                #print(series)
                                                #print(issue)
                                                # if isinstance(issue, float):
                                                #     issue = f'{issue:g}'
                                                #issue = str(issue).replace('.0','')
                                                #print(issue)
                                                df.loc[index,'SeriesName'] = series
                                                df.loc[index,'IssueNum'] = issue
                                                index += 1
                                        if '#' in issuerangeChunk and not '–' in issuerangeChunk:
                                            issue = re.findall(r'\d+', issuerangeChunk)
                                            df.loc[index,'SeriesName'] = series
                                            df.loc[index,'IssueNum'] = issue[0]
                                            index += 1
                                    break
                                if '–' in issuerange:
                                    issuerangelist = getRange(issuerange)
                                    for issue in issuerangelist:
                                        print(series)
                                        print(issue)
                                        df.loc[index,'SeriesName'] = series
                                        df.loc[index,'IssueNum'] = issue
                                        index += 1
                                else:    
                                    #if '#' in issuerange and not '–' in issuerange:
                                    issue = re.findall(r'\d+', issuerange)
                                    df.loc[index,'SeriesName'] = series
                                    df.loc[index,'IssueNum'] = issue[0]
                                    index += 1
                                # if '#' in line and not '–' in line:
                                #     #print(line)
                                #     titleNumSplit = line.split(' #')
                                #     series = titleNumSplit[0]
                                #     #issue = titleNumSplit[1]
                                #     print(series)
                                #     #print(issue)
                                #     df.loc[index,'SeriesName'] = series
                                #     issue = re.findall(r'\d+', titleNumSplit[1])
                                #     df.loc[index,'IssueNum'] = issue[0]
                                #     index += 1
                                # if '–' in line:
                                #     print('yep')
                                #     # Define the input string
                                #     titleNumSplit = line.split(' #')
                                #     series = titleNumSplit[0]
                                #     issuerangelist = getRange(titleNumSplit[1])
                                    
                                #     # # Use regular expression to find all numbers in the range
                                #     # numbers = re.findall(r'\d+', line)

                                #     # # Convert the numbers to integers and extract the range
                                #     # num_range = list(range(int(numbers[0]), int(numbers[1])+1))

                                #     # # Print the range of numbers
                                #     print(issuerangelist)
                                #     for issue in issuerangelist:
                                #         print(series)
                                #         print(issue)
                                #         df.loc[index,'SeriesName'] = series
                                #         df.loc[index,'IssueNum'] = issue
                                #         index += 1

'''