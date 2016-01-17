#!/usr/local/bin/ python
"""
This script creates a timestamped database backup,
and cleans backups older than a set number of dates

"""    
## based on code at http://codereview.stackexchange.com/questions/78643/create-sqlite-backups

import sqlite3
import shutil
import time
import os
import sys

DESCRIPTION = """
              Create a timestamped SQLite database backup, and
              clean backups older than a defined number of days
              """

# How old a file needs to be in order
# to be considered for being removed
NO_OF_DAYS = 7

FILE_TO_BACKUP = os.path.join(os.path.dirname(os.path.abspath(__file__)),'bikeandwalk.sqlite')
BACKUP_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)),'db_backups')

MINIMUM_BACKUPS = 3

def sqlite3_backup(dbfile=FILE_TO_BACKUP, backupdir=BACKUP_DIRECTORY):
    """Create timestamped database copy"""

    if not os.path.isdir(backupdir):
        print('Creating Backup Directory')
        os.makedirs(backupdir)

    if(os.path.isfile(dbfile)):
        backup_file = os.path.join(backupdir, os.path.basename(dbfile) +
                                   time.strftime("-%Y%m%d-%H%M%S"))

        connection = sqlite3.connect(dbfile)
        cursor = connection.cursor()

        # Lock database before making a backup
        cursor.execute('begin immediate')
        # Make new backup file
        shutil.copyfile(dbfile, backup_file)
        print ("\nCreating {}...".format(backup_file))
        # Unlock database
        connection.rollback()
    else:
        print(os.path.basename(dbfile) + ' Does not exist')
        sys.exit(0)


def clean_data(dbfile=FILE_TO_BACKUP, backupdir=BACKUP_DIRECTORY):
    """Delete files older than NO_OF_DAYS days"""

    print ("\n------------------------------")
    print ("Cleaning up old backups")
    # Always leave at lest the minimum number of backups
    filelist = os.listdir(backupdir)
    #Put them in order, newest First
    filelist.sort(reverse=True)
    # Only include files where the file name starts with FILE_TO_BACKUP name
    fileCount = len(filelist)
    for listElement in range(fileCount-1, -1,-1):
        if os.path.basename(filelist[listElement])[:len(os.path.basename(dbfile))] != os.path.basename(dbfile)[:len(os.path.basename(dbfile))]:
            print listElement
            del filelist[listElement]
    
    #the filelist should only contain backup files      
    fileCount = len(filelist)
    if fileCount > MINIMUM_BACKUPS:
        for listElement in range(MINIMUM_BACKUPS, fileCount):
            backup_file = os.path.join(backupdir, filelist[listElement])
            if os.path.isfile(backup_file):
                if os.stat(backup_file).st_ctime < (time.time() - NO_OF_DAYS * 86400):
                    os.remove(backup_file)
                    print ("Deleting {}...".format(backup_file))
    else:
        print('No Backup files to delete')
        

if __name__ == "__main__":
    fileName = FILE_TO_BACKUP
    dirName = BACKUP_DIRECTORY
    if len(sys.argv) > 1:
        if sys.argv[1]:
            fileName = sys.argv[1]
    if len(sys.argv) > 2:
        if sys.argv[2]:
            dirName = sys.argv[2]
    sqlite3_backup(fileName, dirName)
    clean_data(fileName, dirName)

    print ("\nBackup update has been successful.")