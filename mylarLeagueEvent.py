import requests
import os
from enum import IntEnum
import xml.etree.ElementTree as ET
from glob import glob
from sys import argv
import numpy as np
import re
from simyan.comicvine import Comicvine
from simyan.sqlite_cache import SQLiteCache
import pandas as pd


#League of comic geeks config
#wishlistURL = 'https://leagueofcomicgeeks.com/profile/' + leagueUserName + '/wish-list'
#wishlistURL = 'https://leagueofcomicgeeks.com/comics/event/14215/knight-terrors'
#wishlistURL = 'https://leagueofcomicgeeks.com/profile/ash10r/lists/11972/krakoan-era-x-men-reading-list'
#wishlistURL = 'https://leagueofcomicgeeks.com/comics/event/14375/avengers-assemble'
#wishlistURL = 'https://leagueofcomicgeeks.com/comics/event/14372/gang-war'
#wishlistURL = 'https://leagueofcomicgeeks.com/comics/event/14308/atlantis-attacks'
#wishlistURL = 'https://leagueofcomicgeeks.com/comics/event/14277/annihilation-conquest'
#outputFile = 'avengers_assemble.xlsx'
wishlistURL = input("Enter League of Comic Geeks Event URL: ")


series_pat_str = r'(?<=data-sorting=")(.+?(?="))'
volume_pat_str = r'(?<="series" data-begin=")(.+?(?="))'
yearRangePattern = r'(?<=&nbsp;&nbsp;·&nbsp;&nbsp; )(\d{4} - \d{4}|[0-9]{4} - Present|\d{4})'
yearPattern = r'\(([0-9]{4})\)'
yearRemovalString = r' \([0-9]{4}\)'
#yearRangePattern = '([0-9]{4} - [0-9]{4}|[0-9]{4} - Present)'
#yearRangePresentPattern = '[0-9]{4} - Present'
titlePattern = r'<title>(.*?)<\/title>'

dfOrderList = ['SeriesName', 'SeriesStartYear', 'IssueNum', 'IssueType', 'CoverDate', 'Name', 'SeriesID', 'IssueID', 'CV Series Name', 'CV Series Year', 'CV Issue Number', 'CV Series Publisher', 'CV Cover Image', 'CV Issue URL', 'Days Between Issues']
df = pd.DataFrame(columns=dfOrderList)

def parseWishlist():
    series_list = []
    wishlistData = requests.get(wishlistURL).text
    #print(wishlistData)
    print("Checking Wishlist at %s"% (wishlistURL))

    series_pattern = re.compile(series_pat_str)
    volume_pattern = re.compile(volume_pat_str)
    #year_pattern = re.compile(year_html_pat_str)

    series_result = series_pattern.findall(wishlistData)
    volume_result = volume_pattern.findall(wishlistData)
    #year_result = year_pattern.findall(wishlistData)
    global yearRange
    matchyearRange = re.findall(yearRangePattern, wishlistData)
    if matchyearRange:

        yearRange = matchyearRange[0]
    else:
        yearRange = '0000 - 0000'

    global title
    matchTitle = re.findall(titlePattern, wishlistData)
    title = matchTitle[0].replace(' Event Reading Order & Checklist', '').replace(':','')
    #year1 = matchyearRange[0]
    #year2 = matchyearRange[1]
    print(title)
    for i in range(len(series_result)):
        series_result[i] = series_result[i].replace('amp;','')
        #series_list.append([series_result[i], volume_result[i]])
        series_list.append(series_result[i])
        
    return series_list



def main():

    #Process Wishlist
    cblSeriesList = parseWishlist()
    #print(cblSeriesList)
    index = 0
    
    for line in cblSeriesList:
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
            
            allnums = re.findall(r'\d+',issuerange)
            #print(len(allnums))
            #print(df)
            issuenumber = allnums[0]
            df.loc[index, 'IssueNum'] = issuenumber
            df.loc[index, 'SeriesName'] = series
            df.loc[index,'SeriesStartYear'] = year
            index += 1
    #df.fillna({'SeriesStartYear':0}, inplace=True)
    #df = df.astype({'IssueNum':int, 'SeriesStartYear':int})

    fileNamePat = r'\/([^\/]+)$'

    # Use re.search() to find the matching substring
    match = re.search(fileNamePat, wishlistURL)

    if match:
        # Extract the matched substring
        readinglistName = match.group(1)
    #outputFile = '[' + yearRange.replace(' ', '') + '] ' + readinglistName +'.xlsx'
    outputFile = '[' + yearRange.replace(' ', '') + '] ' + title +'.xlsx'

    #print(df)
    df.to_excel(outputFile)
    
    #open(touchjsonFile, 'w').close()

main()
