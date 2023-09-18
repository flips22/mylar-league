# CBL Generation

## CBLgenerator
This is a first pass as a way to create CBL files outside of ComicRack.

The program looks for a XLSX file in the ReadingList-ImportExport and then searches using the first few colums in comicvine. If it finds a match it will add the information for the rest of the rows. If it doesn't find a proper match it will wait for you to open the XLSX file and put in the series ID manually.  There is a hyperlink to help you search comicvine. If it finds the wrong match delese all the old information and then put in the correct volume ID. If you don't delete the old information the script doesn't know that you updated the volume id.

Along with the xlsx file, there's a csv, json file and html file created which are view only files. Changing the csv won't change the end result.  The HTML has the images embedded in the text file so you share that file outisde of your installation.

At the start of this project the JSON file was used as the first input from another script.  The code still expects it so you need to have the file there even if it is blank.  I want to remove that code, but I haven't gotten to it yet.

Directory Explaintion:
CVCoverImages: cache location where all covers images are downlaoded so they can be encoded for the html file.
ReadingList-DB: Location of a sqlite database collecting all the matches. Created using a script I haven't published yet.

ReadingList-ImportExport: The working folder for your excel files.
ReadidngList-Output: Where the CBLs are output
ReadingList-Results: Text files of summary of results for each run.

### Installation

There are some prerequsites that you should identify on the first run. also after it runs it should create all the proper folders. If I have a chance I will create a requirements file. From there you can put in your excel file. Or fill in what is in the template folder.

Once all the issues are identified a CBL is created.  The logic on the days between issue has to be run a second time after you complete the list.

My typical workflow, is run the script find the missing volume IDs.  Locate those volume ids from the webpage of the volume on comicvine. For example in this case the volume ID is 2127
https://comicvine.gamespot.com/the-amazing-spider-man/4050-2127/

After those are manually updated (I use use the auto filters to group the volumes together). I run the script again. If all the issue information is complete (no red) then I run it one last time and check that all the days between issues make sense.

## textToReadingList:
This script takes a text file with a basic written reading list and creates an xlsx file to feed into the CBLgenerator. I'm sure the logic could be imporoved, but way it is currently written works like this:


For example:
  The Amazing Spider-Man (1963) #1-#12
  Web of Spider-Man #1, 6-10

This should set the year and the volume name when listed as (YEAR). The # sign must be there as those are the only lines it looks at.  There is a method to also check a sqlite database which will use the seed start and end year to find the year of the issue and then the corresponding volume start year.  I need to fine tune that a bit, so I haven't posed the db generator yet. Also, only the regular dash works at the momemnt. It won't work with a fancy dash. I need to fix that in the code. For now you have to do a find replace in a text editor.




# Mylar / Komga / Comic Geeks  Integration Tools
This is a collection of various tools to aid in the integration of mylar and komga with leagueofcomicgeeks.com.
- Adding comics to mylar from the comic geeks wishlist
- Adding comics from mylar to the comic geeks collection
- Syncing read progress from komga to the comic geeks collection
- Adding comics to mylar from CBL files

## Installation

1. For the scripts that utilize comicvine (wishlist sync and CBL import), you need to install download & install this package:
   https://github.com/Metron-Project/Simyan
2. For CBL importing create a folder called 'ReadingLists' in the same directory as the script and add any CBL files you want to process into this folder
3. Edit config.ini and fill in required information, removing the two  ' as well. If you don't intend to use a specific app then you can keep the default
  - Replace '[MYLAR API KEY]' with your Mylar3 api key
  - Replace '[MYLAR SERVER ADDRESS]' with your server in the format: http://servername:port/  (make sure to include the slash at the end)
  - Replace '[leagueofcomicgeeks.com username]' with your username. Your wishlist is publicly viewable so no password is needed.
  - Replace '[CV API KEY]' with your comicvine api key
  - Replace '[KOMGA USER NAME]' with your komga login that you want to export reading progress. Reading progress is user dependent.
  - Repalce '[KOMGA PASSWORD]' with our komga password. Yes, it is stored in plain text. If that's an issue for people, perhaps I can create a user prompt so you enter it each time.
  - Replace '[KOMGA SERVER ADDRESS]' with your server in the format: http://servername:port/  (make sure to include the slash at the end)
4. Optional: Rename (or copy) config.ini to configPRIVATE.ini Especially if you are cloning so you don't get your config.ini wiped out in an update.
5. Optional - Modify the following options in the wishlist or CBL import script:
    - PUBLISHER_BLACKLIST : List of publishers to ignore during CV searching, defaults seem to work well for me.
    - PUBLISHER_PREFERRED : List of publishers to prioritise when multiple CV matches are found, defaults seem to work well for me.
    - ADD_NEW_SERIES_TO_MYLAR : Automatically add CV search results to Mylar as new series, default will add to mylar
    - CV_SEARCH_LIMIT : Set a limit on the number of CV API calls made during this processing.
                        This is useful for large collections if you want to break the process into smaller chunks.

## mylarCollectionExport
### Use:
- Running the script the first time will create a mylarcollection.csv master file.
- At the end of the script a csv in the comic geeks website format will be created as mylarcollection-IMPORT-All.csv
- If that export is more than 10k lines it will be broken up into multiple files IMPORT-1, IMPORT-2, etc...
- Log into leagueofcomicsgeeks.com and go to the Comics drop down and then select Bulk Import / Export
- Select the League of Comic Geeks (Default) format and select your IMPORT file.
- Subsequent runs will pull everything from mylar again and then check for changes.
- The output this time will be a file will be: mylarcollectionDelta-[TIMESTAMP]-IMPORT-All.csv (or chunked if your update file is more than 10k lines)
## Notes:
 - The matching isn't perfect. For about 55K issues, it matches about 45k.
 - If the Series title starts with "The", I add the original series title with a title without "The" to the import file. This helped improve the matching a bit.
 - The matching seems to rely only on series name and release date. If there are ideas on how to improve the matching let me know. Perhaps we could have a look up file with the comicvine series compared to the league series name.
 - After I was about 95% done I realized that this all should of been done in a sqlite file.  Perhaps some day I will change that. I apologize in advance for the length of time it takes to run on large collections.

## komgaProgressExport
### Use:
- Running the script will create a komgareadprogress-[TIMESTAMP].csv file 
- At the end of the script a csv in the comic geeks website format will be created as komgareadprogress-[TIMESTAMP]-IMPORT.csv
- Log into leagueofcomicsgeeks.com and go to the Comics drop down and then select Bulk Import / Export
- Select the League of Comic Geeks (Default) format and select your IMPORT file.
- The import will add the title to your collection and mark as read.
## Notes:
 - The original plan was that I was going to add this feature to the collection export script, but it was simpler to just seperate the two. Perhaps when I change to a DB file as the masterfile I will do that.
 - In theory  instead of using mylar to export the collection I could write a script to add everything from komga. For my set up the two are mirrors so it doesn't really matter to me. If that's a desire let me know.
 

## mylarLeagueWishlist.py
### Use:
- Running the script will pull your wishlist, parse out the titles, attempt to find them on comicvine and then add the series to mylar.
### Notes:
- If you want to see the results you can review that in the Wishlist-Output.csv file
- The script will look at that CSV file and won't re-search those series by default. That can change in the script options or by just deleting the .csv file.

## mylarCBLimport
### Use:
- Running the script will parse all the .cbl files in the 'ReadingLists' folder parse out the titles, attempt to find them on comicvine and then add the series to mylar.
### Notes:
- If you want to see the results you can review that in the CBL-Output.csv file
- The script will look at that CSV file and won't re-search those series by default. That can change in the script options or by just deleting the .csv file.


## Comments and Thanks
- The mylar Wishlist and mylar CBL import scripts are nearly identical.
- I created a CBL import script a while back, and TheMadman made a bunch of improvements (Thank You!), and used much better programming techniques than I. This script is based on his, with the main change to use the Simyan comicvine wrapper.
- I should add that I'm not a software engineer and really don't have any training in python or any other language, so I know there are places where things could be better or what I copied off stack overflow wasn't really correct.  I'm welcome to comments, issues, pull requests or any other help you can provide.
- I hope others find these useful. Find me on discord @filps in the mylar or komga servers for support.