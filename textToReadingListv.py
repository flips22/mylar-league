
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

def parse_issueline(ti):
    ttit = []
    comment = []
    
    incom = False
    ename = None
    title = ''
    issue_number = 0
    year = 0



    pat = re.search(r'\((\d{4})\)', ti)
    issuepat = re.search(r'#(\w+(\.?\w+)?)',ti)
    titlepat = re.search(r'(^.*) #',ti)
    if pat:
        year = pat.group(1)
    if issuepat:
        issue_number = issuepat.group(1)
    if titlepat:
        title = titlepat.group(1)
        
    
    return (title, issue_number, year, comment)


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
                if 'CBRO' in file:
                    CBRO_MODE = True
                    print('CBRO file detected. Starting CBRO mode...')
                else:
                    CBRO_MODE = False
                outputfile = file.replace('.txt', '.xlsx')
                outputFile = os.path.join(readingListDirectory, outputfile)
#                touchjsonfile = outputfile.replace('.xlsx','') + '.json'
#                touchjsonFile = os.path.join(readingListDirectory, touchjsonfile)
                if not os.path.exists(outputFile) and CBRO_MODE:


                    df = pd.DataFrame(columns=dfOrderList)
                    with open (inputFile, mode='r', encoding='utf-8') as file:

                    
                        for line in file:
                            if not line.strip():
                                continue
                            #line = 'Archer & Armstrong Vol. 2 #14'
                            seriespattern = re.compile(r' Vol\. \d+',re.IGNORECASE)

                            # Use sub to replace the pattern with an empty string
                            
                            title, issue_number, year, comment = parse_issueline(line)
                            #titleclean = re.sub( Vol)
                            print(title)
                            print(year)
                            titleClean = re.sub(seriespattern, '', title)
                            print(titleClean)
                            
                            if title is not None and year is None:
                                year = 0
                            df.loc[index, 'IssueNum'] = issue_number
                            df.loc[index, 'SeriesName'] = titleClean
                            df.loc[index,'SeriesStartYear'] = year
                            index += 1
                        title_years = {}

                        # Iterate through the DataFrame and update the years
                        for indexyear, row in df.iterrows():
                            title = row['SeriesName']
                            year = row['SeriesStartYear']
                            if year != 0:
                                title_years[title] = year
                            else:
                            # Check if the title has been encountered before
                                if title in title_years:
                                    # Update the year if it was initially set to 0
                                    
                                    df.at[indexyear, 'SeriesStartYear'] = title_years[title]

                    df.fillna({'SeriesStartYear':0}, inplace=True)
                    df = df.astype({'IssueNum':str, 'SeriesStartYear':int})

                    print(df)
                    df.to_excel(outputFile)
                
                if not os.path.exists(outputFile) and not CBRO_MODE:


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
                    


def parse_issueline(ti):
    ttit = []
    comment = []
    issue_number = year = None
    incom = False
    ename = None

    '''    
    pat = self.evre.search(ti)
    if pat is not None:
        ename = pat.group(1)
        ptp = self.make_likearg(ename)
        
        sql = 'SELECT olistid FROM olists WHERE title LIKE ?;'
        tlink = (ename, )
        linkid = None
        for row in self.con.execute(sql, tlink):
            linkid = row[0]

        if linkid is None:
            pat = re.search(r'(.+) \((\d{4})\)', ename)
            if pat is not None:
                ename2, year = pat.groups()
                sql = 'SELECT olistid FROM olists WHERE title LIKE ? AND start_year=?;'
                tlink = (ename2, year)
                print("Looking for linkid for sql params: %s AND %s IN %s" % (ename2, year, ename))
                for row in self.con.execute(sql, tlink):
                    linkid = row[0]
            
        if linkid is None:
            tlink = (ptp, )
            sql = 'SELECT olistid FROM  olists WHERE title LIKE ?;'
            for row in self.con.execute(sql, tlink):
                linkid = row[0]
                
        if linkid is None:
            print("Cannot locate event: %s ti: %s" % (tlink, ti))
            return (None, None, None, None)
        return (f'@{linkid}', None, None, None)
    '''
    for ti in ti.split(' '):
        if ti[0] == '-':
            incom = True
            
        if incom:
            if year is not None or issue_number is not None:
                comment.append(ti)
        else:
            if ti[0] == '#':
                issue_number = ti[1:]
            elif ti[0] == '(' and ti[-1] == ')' and len(ti) == 6:
                year = int(ti[1:5], 10)
                continue
            else:
                if year is not None or issue_number is not None:
                    comment.append(ti)
                else:
                    ttit.append(ti)
    
    title = ' '.join(ttit)
    if len(comment) > 0:
        comment = ' '.join(comment)
    else:
        comment = None
    
    return (title, issue_number, year, comment)

