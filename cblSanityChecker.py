# Runs a number of checks against CBL files to look for possible mistakes that can be investigated and rectified
# - Top level book counts not accurate (will skip this check if no NumIssues entry)
# - Repetition of books (likely from CBRO event merging)
# - Sudden negative time jumps in issue dates (good indicator of wrong volme) with a configurable threshold
#
# Can be run against a folder of CBLs recursively, or against individual files
# Should probably be re-written as a generic module for use in other CBL generation tools ...
import argparse
import os
from pathlib import Path
from bs4 import BeautifulSoup 

def checkFile(filePath, bookcount=True, duplicates=True, timeJumps=True, timeThreshold=2):
    with open(filePath, 'r') as fileHandle:
        data = fileHandle.read()
        cbl = BeautifulSoup(data, "xml")

        books = cbl.find_all("Book")
        numissues = cbl.find_all("NumIssues")

        print(f"Checking file: {filePath}")

        if len(books) == 0:
            print("No Book entries found in CBL")
            return

        if (bookcount):
            if (len(numissues) != 0):
                if (int(numissues[0].text) != len(books)):
                    print(f"\tMismatch between NumIssues ({numissues[0].text}) and count of Books ({len(books)})")
        
        if (duplicates):
            for i in range(0, len(books)):
                for j in range(i+1,len(books)):
                    if books[i] == books[j]:
                        try:
                            print(f"\tPossible Duplication for {books[i].attrs['Series']} ({books[i].attrs['Volume']}) #{books[i].attrs['Number']}")
                        except:
                            print(f"\tException thrown while trying to compare entries: {''.join(str(books[i]).splitlines())} | {''.join(str(books[j]).splitlines())}")

        
        
        lastYear = 0
        try:
            lastYear = int(books[0].attrs['Year'])
        except:
            print(f"Ran into problem parsing year for the first book")
            print(f"\t\t{''.join(str(books[0]).splitlines())}")

        print(lastYear)

        if (timeJumps):            
            for i in range(1, len(books)):
                try:
                    thisYear = int(books[i].attrs['Year'])
                except:
                    print(f"\tCould not find an integer year for entry number {i}: ")
                    print(f"\t\t{''.join(str(books[i]).splitlines())}")
                else:
                    if  lastYear - thisYear >= timeThreshold:
                        try:
                            print(f"\tGreat Scott!  It looks like we tried to jump back in time from "
                                f"{books[i-1].attrs['Series']} ({books[i-1].attrs['Volume']}) #{books[i-1].attrs['Number']} in {lastYear} "
                                f"to {books[i].attrs['Series']} ({books[i].attrs['Volume']}) #{books[i].attrs['Number']} in {thisYear}")
                
                        except:
                            print(f"\tThere was an error getting the attributes of entry {i}: ")
                            print(f"\t\t{''.join(str(books[i]).splitlines())}")
                lastYear = thisYear

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='CBL Sanity Checker',
                    description='Reviews Comic Book Lists for potential issues')
    parser.add_argument('target', help='Either a folder containing CBL files or a single CBL file to analyse')
    parser.add_argument('-xc', help='Disable book count checks', action='store_true')
    parser.add_argument('-xd', help='Disable duplicate issue checks', action='store_true')
    parser.add_argument('-xt', help='Disable time jump checks', action='store_true')
    parser.add_argument('-tt', '--time-threshold', metavar='NN', required=False, help='The number of years that an issue must jump back in time to be sus', type=int, default=2)
    args = parser.parse_args()

    # Either single file processing, or multi-file processing
    root = Path(args.target)
    
    if not root.exists():
        print(f"Error: {args.target} does not exist")
        exit()

    if root.is_file() :
        checkFile(root, bookcount = not args.xc, duplicates = not args.xd, timeJumps= not args.xt, timeThreshold = args.time_threshold)
    elif root.is_dir():
        
        cblFiles = root.rglob("*.cbl")

        for cblFile in cblFiles:
            checkFile(cblFile, bookcount = not args.xc, duplicates = not args.xd, timeJumps= not args.xt, timeThreshold = args.time_threshold)