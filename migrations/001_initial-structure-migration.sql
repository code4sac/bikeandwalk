/* 
     the structure for the bikeandwalk database on 3/17/2018
*/

BEGIN;

CREATE TABLE feature (
	"ID" INTEGER NOT NULL AUTOINCREMENT, 
	"featureClass" TEXT, 
	"featureValue" TEXT, 
	PRIMARY KEY ("ID")
);
CREATE TABLE traveler (
	"ID" INTEGER NOT NULL AUTOINCREMENT, 
	name TEXT NOT NULL, 
	description TEXT, 
	"iconURL" TEXT, 
	"travelerCode" TEXT NOT NULL, 
	PRIMARY KEY ("ID"), 
	UNIQUE ("travelerCode")
);
CREATE TABLE user (
	"ID" INTEGER NOT NULL AUTOINCREMENT, 
	name VARCHAR(80) NOT NULL, 
	email VARCHAR(120) NOT NULL, 
	"userName" VARCHAR(20), 
	password VARCHAR(20), 
	role VARCHAR(20), 
	inactive INTEGER, 
	"organization_ID" INTEGER NOT NULL, 
	PRIMARY KEY ("ID"), 
	UNIQUE (email), 
	UNIQUE ("userName"), 
	FOREIGN KEY("organization_ID") REFERENCES organization ("ID")
);
CREATE TABLE traveler_feature (
	"ID" INTEGER NOT NULL AUTOINCREMENT, 
	"traveler_ID" INTEGER, 
	"feature_ID" INTEGER, 
	PRIMARY KEY ("ID"), 
	FOREIGN KEY("traveler_ID") REFERENCES traveler ("ID"), 
	FOREIGN KEY("feature_ID") REFERENCES feature ("ID")
);
CREATE TABLE location (
	"ID" INTEGER NOT NULL AUTOINCREMENT, 
	"locationName" TEXT NOT NULL, 
	"NS_Street" TEXT, 
	"EW_Street" TEXT, 
	city TEXT, 
	state TEXT, 
	latitude TEXT, 
	longitude TEXT, 
	"organization_ID" INTEGER NOT NULL, locationType TEXT default 'intersection', NS_Heading REAL DEFAULT 0, EW_Heading REAL DEFAULT 90, 
	PRIMARY KEY ("ID"), 
	FOREIGN KEY("organization_ID") REFERENCES organization ("ID")
);
CREATE TABLE event_traveler (
	"ID" INTEGER NOT NULL AUTOINCREMENT, 
	"sortOrder" INTEGER, 
	"countEvent_ID" INTEGER, 
	"traveler_ID" INTEGER, 
	PRIMARY KEY ("ID"), 
	FOREIGN KEY("countEvent_ID") REFERENCES count_event ("ID"), 
	FOREIGN KEY("traveler_ID") REFERENCES traveler ("ID")
);

CREATE TABLE organization (
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   name TEXT,
   email TEXT UNIQUE NOT NULL,
   defaultTimeZone TEXT DEFAULT 'PST'
);
CREATE TABLE count_event (
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   /* 
    Start Date and End Date are both to be in the form
    of DateTime. sqlite3 does not have a datetime type so Text is used.
    Dates will be stored as LOCAL time in the format YYYY-MM-DDTHH:MM:SS XXX
         where 'XXX' is a three letter time zone identifier
   */
   startDate TEXT NOT NULL,
   endDate TEXT NOT NULL,
   timeZone TEXT DEFAULT 'PST', /* requires that all locations for this count be in the same time zone */
   isDST INTEGER DEFAULT 0, /* is the event during Daylight savings time */
   -- can't delete the organization record that this count_event depends on
   organization_ID INTEGER REFERENCES organization(ID) ON DELETE RESTRICT
, title text, weather text);

CREATE TABLE trip (
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
CREATE TABLE provisional_trip (
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
CREATE TABLE assignment (
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   assignmentUID TEXT UNIQUE, --System generated, hard to guess code
   countEvent_ID INTEGER REFERENCES count_event(ID) ON DELETE CASCADE,
   location_ID INTEGER REFERENCES location(ID) ON DELETE CASCADE,
   user_ID INTEGER REFERENCES user(ID) ON DELETE CASCADE
, invitationSent TEXT);

COMMIT;
