
![logo_cropped](https://github.com/flips22/mylar-league/assets/1898114/547788db-bcbe-470c-9e45-968f041b8753)

Welcome to a collection (or more of a menagerie) of various apps for comic book tools, regarding reading lists, mylar, komga, kavita, league of comic geeks.
A lot of the tools supplement the great CBL collection at:
https://github.com/DieselTech/CBL-ReadingLists
I really don't have a background in programming, so don't expect perfection. I am welcome PRs, and I appreciate all those that helped me though PRs and advice and direction.
# CBL Generation
A set of tools to create comic book reading lists in the format of a .CBL file.
### **CBLgenerator.py**

Create a CBL file from an xlsx file. The xlsx file can be updated to make manual matches to comicvine, or search based on title and dates.

### **textToReadingList.py**
Convert a text file to an xlsx file that can then be used to create a CBL

### **dbTruthTableGenerator.py**
Creates a sqlite DB file from multiple xlsx files so a future list can use the same matching logic.


# Year In Review
A script that will compare you mylar instance to all volumes on comicvine for each year and each publisher.
### **YearInReview.py**
This script looks at all the new volumes on comicvine for for a given year and compares to your mylar instance. The output are HTML files for each publisher, each year as well as an interactive chart (also in HTML). The yearly HTML files show you the cover images, and provides link to view on comicvine and view in mylar or add to mylar. The 
### **pubidtoconfig.py**
Created to inject publisher ids from the text file to config.ini

# Installation:
See detailed tutorial at: [CBLtoolsInstallation.md](CBLtoolsInstallation.md)

    
# CBL Import
## Usage
1. **Create Folders**
    - On the first run of either the `mylarCBLimportHTML.py` or the `mylarCBLimportQuick.py` multiple folders will be created, including a `ReadingLists` folder.
2. **Copy CBL files**
    - Copy the CBL files that you would like to compare to your mylar installation to the `ReadingLists` folder.
3. **mylarCBLimportHTML.py**
    - The most fully featured script of the HTML version. This will run though each CBL file, and create an HTML file which includes information about all the volumes found in the CBL file, including the cover image of the first issue for the volume. 
    - There is a link for each volume to either view the series in mylar, or add the series to mylar, if it is not found in mylar.  There is also a button at the top of the page to add all missing volumes to mylar at once.
    - To get the information required for the HTML file, there are many comicvine api calls made, so it can take a bit to create for large CBL files.
4. **mylarCBLimportQuick.py**
    - If you want to just add all missing volumes to mylar without any information or API calls this is the script to use. 
    - It will run and analyze all the CBLs in your `ReadingLists` folder and will show you a summary at the end giving you the option to add all missing series.
    - The default behavior assumes that you set mylar to track all issues when you add a new series. If you prefer to only track issues, set the option in the `config.ini` file called `analyzeIssues` to True.

# CBL Generation
## Theory of Operation
### CBLgenerator.py
This is a first pass as a way to create CBL files outside of ComicRack.

The program looks for a XLSX file in the `ReadingList-ImportExport` and then searches using the first few columns in comicvine. If it finds a match it will add the information for the rest of the rows. If the file name has a year range such as (2020-2022) it will check that each issue calls withing the range with 1 additional year on each end of the range (2019 to 2023) to account for cover date to store date mismatches.

If it doesn't find a proper match you can open the XLSX file (I use LibreOffice) and put in the series ID manually. There is a hyperlink on each row open a search at comicvine. If it finds the wrong match delete all the old information and then put in the correct volume ID. If you don't delete the old information the script doesn't know that you updated the volume id.

Along with the xlsx file, there's a csv and html file created which are view only files. Changing the csv won't change the end result.  The HTML has the images embedded in the text file so you share view the reading list in a more human readable format.

Directory Explanation:
CVCoverImages: Cache location where all covers images are downloaded so they can be encoded for the html file.
ReadingList-DB: Location of a sqlite database caching the searches at comicvine using Simyan. Also, using `dbTruthTableGenerator.py` you can create a db file using a set of xlsx files so the next time you run a new list it 'remembers' the match.
ReadingList-ImportExport: The working folder for your excel files.
ReadingList-Output: Where the CBLs are output
ReadingList-Results: Text files of summary of results for each run.


Once all the issues are identified a CBL is created. There is a setting in the `CBLgenerator.py` file `forceCreateCBL` which will create the CBL file even if all the matches are not made. The logic on the days between issue has to be run a second time after you complete the list.

My typical workflow, is run the script find the missing volume IDs.  Locate those volume ids from the webpage of the volume on comicvine. For example in this case the volume ID is 2127
https://comicvine.gamespot.com/the-amazing-spider-man/4050-2127/

After those are manually updated (I use use the auto filters to group the volumes together). I run the script again. If all the issue information is complete (no red) then I run it one last time and check that all the days between issues make sense.

## textToReadingList:


This script takes a text file with a basic written reading list and creates an xlsx file to feed into the CBLgenerator. If the source of the text is CBRO, put CBRO somewhere in the file name.

I know the logic isn't perfect, but it will try to handle a typically written reading list.

For example:
  The Amazing Spider-Man (1963) #1-#12
  Web of Spider-Man #1, 6-10

This should set the year and the volume name when listed as (YEAR). The # sign must be there as those are the only lines it looks at.  Also, only the regular dash works at the moment. It won't work with a fancy dash. I need to fix that in the code. For now you have to do a find replace in a text editor.


# Year In Review
This script looks at all the new volumes on comicvine for for a given year and compares to your mylar instance.  The output are HTML files for each publisher, each year as well as an interactive chart (also in HTML). The yearly HTML files show you the cover images, and provides link to view on comicvine and view in mylar or add to mylar.

There is an effort made to try to classify each series release. The code, which was "borrowed" from mylar and then made a bit more restrictive in a number of ways looks at the description and deck for each volume and the first issue of the series (if that answer can't be gained by parsing the volume). You can see the different volume types listed and which are kept. By default any reprinted or TPB/HCs are removed from the analysis. I'm sure this isn't perfect so if you see some issues, let me know.

Unfortunately there isn't a way to precisely query CV for a year and a publisher, so you aren't able to even check a single year and single publisher without the 280,000 API calls. Because of this I included my own cache file of all the API calls. I felt like a typical user would not have wanted to spend more than 2 months, running the script 24/7 to get this output. Now it takes just a couple of minutes to analyze 90 years of comics for the two big publishers.
The file is too large to host here on github, so I have it saved here:
https://mega.nz/folder/7tAjxTKY#DcDOp4wv8Gk8jWUKnEPYWA


# Additional Mylar / Komga / Comic Geeks  Integration Tools
- Adding comics to mylar from the comic geeks wishlist
- Adding comics from mylar to the comic geeks collection
- Syncing read progress from komga to the comic geeks collection


## mylarLeagueEvent
### Use:
- Run the script and paste in a hyperlink for an event.
## Notes:
 - The xlsx file will output and then can be used with the CBL generator script.


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
 - The original plan was that I was going to add this feature to the collection export script, but it was simpler to just separate the two. Perhaps when I change to a DB file as the master file I will do that.
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
- This was the first iteration. I feel that the mylarCBLimportHTML and mylarCBLimportQuick to be a bit more user friendly.

## Comments and Thanks
- I created a CBL import script a while back, and TheMadman made a bunch of improvements (Thank You!), and used much better programming techniques than I. This script is based on his, with the main change to use the Simyan comicvine wrapper.
- I should add that I'm not a software engineer and really don't have any training in python or any other language, so I know there are places where things could be better or what I copied off stack overflow wasn't really correct.  I'm welcome to comments, issues, pull requests or any other help you can provide.
- I hope others find these useful. Find me on discord: https://discord.gg/DQmHfzFdGG for support.

## Recent Updates
Updates through March 31, 2024
 - Config options for YearInReview now all located in the config.ini, this includes PubIDs, year span, and book types. All options for book types listed in config.ini comment.
 - Publisher IDs for the above are all located in two places. pubids.txt is a starter set of 100+ western comic focused publishers with a large span of genre an interest. superpubids.txt is every pubid within the DB.
 - This has been tested with over 450 publishers at once with a full span and a custom span. Large queries like this will take longer to generate so pick and choose from the superpubids.txt rather than feed directly into your config.
 - Speaking of your config.ini, there is a new injector from pubids.txt to your config.ini called pubidstoconfig.py, run this when you have your pubids.txt as you would like for the search. 

## Previous Updates

Update Feb 3, 2024
 - Updated API logic to handle the recent change to the comicvine API limits
Update Dec 16, 2023
 - Made a number of updates to the searching logic. It now checks if it has searched for the series previously. Also if there is no year, it uses the filename to find the year range, and then looks to see if the cover date of the issue is between that range (+/-1). The filename format needs to be [2022-2023].  I have done quite a bit of testing, but there's a risk that I missed something, if so, let me know.

Update Dec 10, 2023:
  - Removed the need to have a matching json file. I disabled json import as there isn't big demand for this at the time being. If this changes I can improve the json implementation at that time.
  - Added the search for a volume if there is no year defined.  There's a tendency to find multiple matches. At the moment it picks the series with the largest number of issues. In the future, I will try to make this smarter using the filename as the year range.

