#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
This script will export data from mylar through its API to a CSV file that can be imported into "My Collection" at League of Comic Geeks (leagueofcomicgeeks.com)

See the readme at: https://github.com/flips22/mylar-league for more information.

1) Edit the config.ini file and change the following:
2) Replace [MYLAR API KEY] with your Mylar3 api key
3) Replace [MYLAR SERVER ADDRESS] with your server in the format: http://servername:port/  (make sure to include the slash at the end)

Usage:
    python3 mylarCollectionExport.py
    Import the files labeled IMPORT into the league of coimc geeks web site.

'''

import requests
import json
import time
import os
import re
import csv
import configparser


masterFile = 'mylarcollection.csv'

timeStamp = time.strftime("%Y%m%d-%H%M%S")
deltaFile = 'mylarcollectionDelta-' + timeStamp + '.csv'
newIssueCounter = 0

#Decide to run update or new master file
if os.path.exists(masterFile):
    firstRun = False
    collectionFile = deltaFile
    LOCGinputFile = deltaFile.strip('.csv') + '-IMPORT-All' + '.csv'

else:
    firstRun = True
    collectionFile = masterFile
    LOCGinputFile = masterFile.strip('.csv') + '-IMPORT-All' + '.csv'


config = configparser.ConfigParser(allow_no_value=True)

if os.path.exists('configPRIVATE.ini'): # an attempt to prevent me from sharing my api keys (again) :)
    config.read('configPRIVATE.ini')
else:
    config.read('config.ini')

mylarAPI = config['mylar']['mylarapi']
mylarBaseURL = config['mylar']['mylarbaseurl']

mylarCheckURL = mylarBaseURL + 'api?apikey=' + mylarAPI + '&cmd=getComic&id='
mylarGetAllURL = mylarBaseURL + 'api?apikey=' + mylarAPI + '&cmd=getIndex'

#number of lines for import files to locg
chunk_size = config.getint('leagueOfComicGeeks', 'chunk_size')


def getAllSeries():
    global newIssueCounter
    print("         Pulling all series data from mylar")
    
    try :
        mylarAllData = requests.get(mylarGetAllURL).text
    except requests.exceptions.RequestException as e:
        print('Exiting...   Something wrong with mylar API config')
        raise SystemExit(e)

    jsonAllData = json.loads(mylarAllData)
    
    # Don't use headers, but might at a later date
    #headers = ['ComicID', 'Publisher Name', 'Series Name', 'Series Year Begins', 'Issue Number']
    
    if firstRun:
        f = csv.writer(open(masterFile, 'w', encoding='utf-8'), delimiter=';', lineterminator='\n')
        
    #set default
    addIssue = False
    for line in range(len(jsonAllData['data'])):
    #for line in range(10): #for testing the first X number of series

        if line % 100 == 0: print("         Progress: %s series of %s pulled from mylar" % (line,len(jsonAllData['data'])))    

        mylarAllData = requests.get(mylarGetAllURL).text
        jsonAllData = json.loads(mylarAllData)
        comicID =  jsonAllData['data'][line]['id']
       
        comicCheckURL = "%s%s" % (mylarCheckURL, str(comicID))
       
        mylarIssueData = requests.get(comicCheckURL).text
        jsonIssueData = json.loads(mylarIssueData)

        for issue in range(len(jsonIssueData['data']['issues'])):
            if jsonIssueData['data']['issues'][issue]['status'] == "Downloaded" or jsonIssueData['data']['issues'][issue]['status'] == "Archived":
                if firstRun:
                    f.writerow([jsonIssueData['data']['issues'][issue]['id'],
                               jsonIssueData['data']['comic'][0]['publisher'],
                               jsonIssueData['data']['comic'][0]['name'],
                               jsonIssueData['data']['comic'][0]['year'],
                               jsonIssueData['data']['issues'][issue]['number'],
                               jsonIssueData['data']['issues'][issue]['releaseDate'],
                               jsonIssueData['data']['issues'][issue]['issueDate']])
                
                else:
                    
                    issueIDsearch = jsonIssueData['data']['issues'][issue]['id'] + ';'
                    addIssue = True
                    with open(masterFile, 'r', encoding='utf-8') as searchfile:
                        for line in searchfile:

                            if issueIDsearch in line:
                                addIssue = False
                                break
                            
                    if addIssue:
                        f = csv.writer(open(masterFile, 'a', encoding='utf-8'), delimiter=';', lineterminator='\n')    
                        f_delta = csv.writer(open(deltaFile, 'a', encoding='utf-8'), delimiter=';', lineterminator='\n')
                        newIssueCounter += 1
                        print('Adding new issue of ' + jsonIssueData['data']['comic'][0]['name'] +  ' to delta file and master file')
                        f_delta.writerow([jsonIssueData['data']['issues'][issue]['id'],
                            jsonIssueData['data']['comic'][0]['publisher'],
                            jsonIssueData['data']['comic'][0]['name'],
                            jsonIssueData['data']['comic'][0]['year'],
                            jsonIssueData['data']['issues'][issue]['number'],
                            jsonIssueData['data']['issues'][issue]['releaseDate'],
                            jsonIssueData['data']['issues'][issue]['issueDate']])
                            
                        f.writerow([jsonIssueData['data']['issues'][issue]['id'],
                            jsonIssueData['data']['comic'][0]['publisher'],
                            jsonIssueData['data']['comic'][0]['name'],
                            jsonIssueData['data']['comic'][0]['year'],
                            jsonIssueData['data']['issues'][issue]['number'],
                            jsonIssueData['data']['issues'][issue]['releaseDate'],
                            jsonIssueData['data']['issues'][issue]['issueDate']])


    return()

def leagueify():
    f_out = csv.writer(open(LOCGinputFile, 'w', encoding='utf-8'), delimiter=';', lineterminator='\n')
    
    with open(collectionFile,'r', encoding='utf-8') as f:
        collection_list = list(csv.reader(f, delimiter=";", lineterminator='\n'))
        for line in range(len(collection_list)):
            if not re.match('^0', collection_list[line][5]):#prefer release date, if zeros, fall back to issue date
                date = collection_list[line][5]
            else:
                date = collection_list[line][6]
            fulltitle = collection_list[line][2] + " #" + collection_list[line][4]
            f_out.writerow([collection_list[line][1],
                            collection_list[line][2],
                            fulltitle,
                            date])
            #if title starts with "The" also add a title that doesn't start with "The" for better matching
            if re.match('^The ',fulltitle):
                fulltitlenothe = re.sub('^The ','',fulltitle)
                f_out.writerow([collection_list[line][1],
                            collection_list[line][2],
                            fulltitlenothe,
                            date])
        filelength = len(f.readlines())


def chunkify():
    print("         Splitting files for import...")
    with open(LOCGinputFile, "r", encoding='utf-8') as f_all:
        count = 0
        #header = f_all.readline()
        lines = []
        for line in f_all:
            count += 1
            lines.append(line)
            if count % chunk_size == 0:
                write_chunk(count // chunk_size, lines)
                lines = []
        # write remainder
        if len(lines) > 0:
            write_chunk((count // chunk_size) + 1, lines)


def write_chunk(part, lines):
    
    with open(collectionFile.strip('.csv') + '-IMPORT-'+ str(part) +'.csv', 'w', encoding='utf-8') as f_out:
        #f_out.write(header)
        f_out.writelines(lines)
    return()


def main():
    if firstRun:
        print("       First run of export starting...")
        getAllSeries()
        leagueify()
        with open(LOCGinputFile, "r", encoding='utf-8') as f_length:
            if(len(f_length.readlines())) >= chunk_size:
                chunkify()
    else:
        print("       Delta run of export starting...")
        getAllSeries()
        
        if not newIssueCounter == 0:
            leagueify()
            print('         Found ' + str(newIssueCounter) + ' issues')
            with open(LOCGinputFile, "r", encoding='utf-8') as f_length:
                if(len(f_length.readlines())) >= chunk_size:
                    chunkify()
        else:
            print('         Found no new issues. No import files created.')

main()
