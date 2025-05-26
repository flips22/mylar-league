import os
import re
import pandas as pd
from glob import glob

# HTML and Output Directory
html_folder = "ReadingList-HTML-League"

#Create folder if needed
if not os.path.isdir(html_folder): os.makedirs(html_folder)

series_pat_str = r'(?<=data-sorting=")(.+?(?="))'
volume_pat_str = r'(?<="series" data-begin=")(.+?(?="))'
yearRangePattern = r'(?<=&nbsp;&nbsp;·&nbsp;&nbsp; )(\d{4} - \d{4}|[0-9]{4} - Present|\d{4})'
yearPattern = r'\(([0-9]{4})\)'
yearRemovalString = r' \([0-9]{4}\)'
titlePattern = r'<title>(.*?)<\/title>'

dfOrderList = ['SeriesName', 'SeriesStartYear', 'IssueNum', 'IssueType', 'CoverDate', 'Name', 'SeriesID', 'IssueID', 'CV Series Name', 'CV Series Year', 'CV Issue Number', 'CV Series Publisher', 'CV Cover Image', 'CV Issue URL', 'Days Between Issues']
df = pd.DataFrame(columns=dfOrderList)

def clean_filename(filename, replacement='_'):
    # Define invalid characters (Windows: \ / : * ? " < > |)
    return re.sub(r'[\\/*?:"<>|]', replacement, filename)

def parseWishlist(html_data):
    series_list = []
    
    series_pattern = re.compile(series_pat_str)
    volume_pattern = re.compile(volume_pat_str)

    global yearRange
    matchyearRange = re.findall(yearRangePattern, html_data)
    yearRange = matchyearRange[0] if matchyearRange else '0000 - 0000'

    global title
    matchTitle = re.findall(titlePattern, html_data)
    title = matchTitle[0].replace(' Event Reading Order & Checklist', '').replace(':','').replace('?','').replace('/','-')

    series_result = series_pattern.findall(html_data)
    volume_result = volume_pattern.findall(html_data)

    for item in series_result:
        item = item.replace('amp;', '')
        series_list.append(item)
        
    return series_list

def main():
    html_files = glob(os.path.join(html_folder, '*.html'))

    for html_file in html_files:
        with open(html_file, 'r', encoding='utf-8') as file:
            html_data = file.read()
        
        cblSeriesList = parseWishlist(html_data)

        index = len(df)
        for line in cblSeriesList:
            if '#' in line:
                yearReSearch = re.search(yearPattern, line)
                year = 0
                if yearReSearch:
                    year = yearReSearch.group(1)
                    line = re.sub(yearRemovalString, '', line)

                titleNumSplit = line.split(' #', 1)
                series = titleNumSplit[0].strip()
                series = series.replace("–", "-")

                issuerange = titleNumSplit[1].strip()
                allnums = re.findall(r'\d+', issuerange)

                if allnums:
                    issuenumber = allnums[0]
                    df.loc[index, 'IssueNum'] = issuenumber
                    df.loc[index, 'SeriesName'] = series
                    df.loc[index, 'SeriesStartYear'] = year
                    index += 1
        # Drop duplicates before writing to Excel
        #print (df)
        df.drop_duplicates(inplace=True)
        df.reset_index(drop=True, inplace=True)
        #print(df)
        output_filename = f"[{yearRange.replace(' ', '')}] {title}.xlsx"
        output_filename = clean_filename(output_filename)
        output_path = os.path.join(html_folder, output_filename)
        df.to_excel(output_path, index=True)
        print(f"Saved Excel file: {output_path}")

main()
