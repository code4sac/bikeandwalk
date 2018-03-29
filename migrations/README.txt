# Database Migration Files

This is a simple approach to tracking and applying changes to the database structure and data. There is nothing managed or automatic about how this works. All migrations need to be applied manually. Likewise, the migration file naming described below is not enforced in any way.

## Migration File Names

The files should be named as: <### the sequence num>_<YYYYMMDD the date>_<some meaningful name> where the sequence number is a number to indicate the sequence in which files are to be applied. The date string documents when the migration was created.

So a file name might look something like: 003_20180329_UpdateLocationKeys.sql

## File Contents

The contents of the files are assumed to be pure SQL in the dialect of the target database. 

To apply the migrations either execute the file directly into the database or use a cut and paste approach from the terminal.