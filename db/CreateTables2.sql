-- need to invoke PRAGMA foreign_keys=ON; to enable foreign key constraints

-- foreign key support must be OFF so we can drop the tables to init test data
PRAGMA foreign_keys=OFF;

DROP TABLE IF EXISTS organization;
CREATE TABLE IF NOT EXISTS organization (
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   name TEXT,
   email TEXT UNIQUE NOT NULL,
   defaultTimeZone TEXT DEFAULT 'PST'
);

DROP TABLE IF EXISTS user;
CREATE TABLE IF NOT EXISTS user (
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   name TEXT NOT NULL,
   email TEXT UNIQUE,
   userName TEXT UNIQUE,
   password TEXT,
   role TEXT NOT NULL DEFAULT 'counter',
   inactive INTEGER DEFAULT 0,
   organization_ID INTEGER REFERENCES organization(ID) ON DELETE CASCADE
);
DROP TABLE IF EXISTS location;
CREATE TABLE IF NOT EXISTS location (
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   locationName TEXT NOT NULL,
   NS_Street TEXT,
   EW_Street TEXT,
   locationType TEXT DEFAULT 'intersection', -- 'intersection' | 'mid block'
   city TEXT,
   state TEXT,
   latitude TEXT,
   longitude TEXT,
   -- can't delete the organization record that this location depends on
   organization_ID INTEGER REFERENCES organization(ID) ON DELETE RESTRICT
);
DROP TABLE IF EXISTS count_event;
CREATE TABLE IF NOT EXISTS count_event (
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   /* 
    Start Date and End Date are both to be in the form
    of DateTime. sqlite3 does not have a datetime type so Text is used.
    Dates will be stored as LOCAL time in the format YYYY-MM-DDTHH:MM:SS
         
   */
   startDate TEXT NOT NULL,
   endDate TEXT NOT NULL,
   timeZone TEXT DEFAULT 'PST', /* requires that all locations for this count be in the same time zone */
   isDST INTEGER DEFAULT 0, /* is the event during Daylight savings time */
   -- can't delete the organization record that this count_event depends on
   organization_ID INTEGER REFERENCES organization(ID) ON DELETE RESTRICT
);

DROP TABLE IF EXISTS assignment;
CREATE TABLE IF NOT EXISTS assignment (
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   assignmentUID TEXT UNIQUE, --System generated, hard to guess code
   weather TEXT, -- 1 = extreme, 2 = poor, 3 = acceptable
   countEvent_ID INTEGER REFERENCES count_event(ID) ON DELETE CASCADE,
   location_ID INTEGER REFERENCES location(ID) ON DELETE CASCADE,
   user_ID INTEGER REFERENCES user(ID) ON DELETE CASCADE
);

DROP TABLE IF EXISTS trip;
CREATE TABLE IF NOT EXISTS trip (
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   tripCount INTEGER,
   tripDate TEXT,
   turnDirection TEXT,
   seqNo TEXT,
   -- can't delete location or traveler records that this trip depends on
   location_ID INTEGER REFERENCES location(ID) ON DELETE RESTRICT,
   traveler_ID INTEGER REFERENCES traveler(ID) ON DELETE RESTRICT,
   countEvent_ID INTEGER REFERENCES count_event(ID) ON DELETE RESTRICT
);

DROP TABLE IF EXISTS provisional_trip;
CREATE TABLE IF NOT EXISTS provisional_trip (
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   tripCount INTEGER,
   tripDate TEXT,
   turnDirection TEXT,
   seqNo TEXT,
   location_ID INTEGER REFERENCES location(ID),
   traveler_ID INTEGER REFERENCES traveler(ID),
   countEvent_ID INTEGER REFERENCES count_event(ID),
   issue TEXT
);

DROP TABLE IF EXISTS eventTraveler;
CREATE TABLE IF NOT EXISTS eventTraveler (
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   sortOrder INTEGER,
   count_event_ID INTEGER REFERENCES count_event(ID) ON DELETE CASCADE,
   traveler_ID INTEGER REFERENCES traveler(ID) ON DELETE CASCADE
);
DROP TABLE IF EXISTS traveler;
CREATE TABLE IF NOT EXISTS traveler (
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   name TEXT NOT NULL,
   description TEXT,
   iconURL TEXT,
   travelerCode TEXT UNIQUE NOT NULL
);
DROP TABLE IF EXISTS travelerFeature;
CREATE TABLE IF NOT EXISTS travelerFeature (
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   traveler_ID INTEGER REFERENCES traveler(ID) ON DELETE CASCADE,
   feature_ID INTEGER REFERENCES feature(ID) ON DELETE CASCADE
);
DROP TABLE IF EXISTS feature;
CREATE TABLE IF NOT EXISTS feature (
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   featureClass TEXT,
   featureValue TEXT
);

-- Turn foreign key support on
pragma foreign_keys=ON;

