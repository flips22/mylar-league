import requests
import json
import time
import os
import csv
import configparser
from requests.auth import HTTPBasicAuth
import re

config = configparser.ConfigParser(allow_no_value=True)

if os.path.exists('configPRIVATE.ini'): # an attempt to prevent me from sharing my api keys (again) :)
    config.read('configPRIVATE.ini')
else:
    config.read('config.ini')

komgaBaseURL = config['komga']['komgabaseurl']
komgaUser = config['komga']['komgauser']
komgaPass = config['komga']['komgapass']

timeStamp = time.strftime("%Y%m%d-%H%M%S")

komgaFile = 'komgareadprogress-' + timeStamp + '.csv'
komgaInputFile = 'komgareadprogress-IMPORT-' + timeStamp + '.csv'

komgaSeriesReadProgURL = komgaBaseURL + 'api/v1/series?read_status=READ&read_status=IN_PROGRESS'

try :
    komgaAllRead = requests.get(komgaSeriesReadProgURL, auth=HTTPBasicAuth(komgaUser, komgaPass)).text
except requests.exceptions.RequestException as e:
        print('Exiting...   Something wrong with komga API config')
        raise SystemExit(e)

jsonAllData = json.loads(komgaAllRead)

f = csv.writer(open(komgaFile, 'w', encoding='utf-8'), delimiter=';', lineterminator='\n')
finp = csv.writer(open(komgaInputFile, 'w', encoding='utf-8'), delimiter=';', lineterminator='\n')
print("         Pulling read progress from komga...") 

for line in range(len(jsonAllData['content'])):

    komgaAllRead = requests.get(komgaSeriesReadProgURL, auth=HTTPBasicAuth(komgaUser, komgaPass)).text
    jsonAllData = json.loads(komgaAllRead)
    
    seriesID =  jsonAllData['content'][line]['id']
    komgaIssuesURL = komgaBaseURL + 'api/v1/series/' + str(seriesID) + '/books?read_status=READ'
       
    komgaIssueData = requests.get(komgaIssuesURL, auth=HTTPBasicAuth(komgaUser, komgaPass)).text
    jsonIssueData = json.loads(komgaIssueData)

    for issue in range(len(jsonIssueData['content'])):
        seriesName = re.sub(' \([0-9][0-9][0-9][0-9]\)','', jsonAllData['content'][line]['name'])
        seriesYear = re.findall('\(([0-9][0-9][0-9][0-9])\)',jsonAllData['content'][line]['name'])

        f.writerow([jsonIssueData['content'][issue]['id'],
                    jsonAllData['content'][line]['metadata']['publisher'],
                    seriesName,
                    seriesYear[0],
                    jsonIssueData['content'][issue]['number'],
                    jsonIssueData['content'][issue]['metadata']['releaseDate']])

        fullTitle = seriesName + ' #' + str(jsonIssueData['content'][issue]['number'])

        finp.writerow([jsonAllData['content'][line]['metadata']['publisher'],
                    seriesName,
                    fullTitle,
                    jsonIssueData['content'][issue]['metadata']['releaseDate'],
                    1, #in collection
                    0, #in wishlist
                    1]) #read                      
