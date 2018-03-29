/*
    Create a new table user_organization to make a MtoM relation with orgs and users.
    Migrate the data from user.organization_ID to new table.
    Remove field user.organization_ID
*/

BEGIN;

CREATE TABLE user_organization 
    ( ID INTEGER PRIMARY KEY AUTOINCREMENT,
      user_ID INTEGER NOT NULL,
      organization_ID INTEGER NOT NULL,
      FOREIGN KEY("user_ID") REFERENCES user ("ID") ON DELETE CASCADE,
      FOREIGN KEY("organization_ID") REFERENCES organization ("ID") ON DELETE CASCADE
    );

COMMIT;

-- create user_organization data
BEGIN;

INSERT INTO user_organization (user_ID, organization_ID)
    SELECT ID, organization_ID 	FROM user;

COMMIT;

-- modify the user table to remove the organization_ID column

BEGIN;

CREATE TABLE user_temp (
        "ID" INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(80) UNIQUE NOT NULL,
        email VARCHAR(120) UNIQUE NOT NULL,
        "userName" VARCHAR(20) UNIQUE,
        password VARCHAR(20),
        role VARCHAR(20),
        inactive INTEGER
);

INSERT INTO user_temp (ID, name, email, username, password, role, inactive)
    SELECT ID, name, email, username, password, role, inactive FROM user;

DROP TABLE user;

ALTER TABLE user_temp RENAME TO user;

COMMIT;

