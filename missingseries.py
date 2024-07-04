import configparser
import sqlite3
import csv
import os

config = configparser.ConfigParser()

config_file = 'configPRIVATE.ini' if os.path.exists('configPRIVATE.ini') else 'config.ini'

config.read(config_file)
pubidsetting = config.get('yearinreview', 'pubidsetting')
pubid_list = pubidsetting.split(',')

db_path = 'ReadingList-DB/yearInReview-Type.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

query = """
SELECT SeriesID, [CV Series Name], [CV Series Year], [CV Series PublisherName]
FROM volumes
WHERE [CV Series PublisherID] IN ({})
""".format(','.join('?' for _ in pubid_list))
cursor.execute(query, pubid_list)
results = cursor.fetchall()

filtered_results = [
    row for row in results
    if row[2] is None or not (row[2].startswith('19') or row[2].startswith('20')) or len(row[2]) != 4
]

csv_filename = 'filtered_volumes.csv'
with open(csv_filename, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(['SeriesID', 'CV Series Name', 'CV Series Year', 'CV Series PublisherName'])
    csvwriter.writerows(filtered_results)


conn.close()

print(f"Filtered data has been written to {csv_filename}")
