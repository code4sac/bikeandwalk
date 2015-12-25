-- foreign key support must be OFF so we can drop the tables to init test data
PRAGMA foreign_keys=OFF;

BEGIN TRANSACTION;

/* Insert Test data into bikeandwalk data file */
delete from organization;
insert into organization (name,email) values ("Sacramento Area Bicycle Advocates","info@sacbike.org");
insert into organization (name,email) values ("Some Other Organization","bob@someothereorg.org");

create view saba_ID as select ID from organization where email="info@sacbike.org";

delete from user;
insert into user (name, email, organization_ID) values ('Bill Leddy', 'bill@williesworkshop.net', (select ID from saba_ID));
insert into user (name, email, organization_ID) values ('Jason Ody', 'jason@williesworkshop.net', (select ID from saba_ID));

delete from location;
insert into location (locationName,NS_Street,EW_Street,city,state,latitude,longitude,organization_ID) values 
    ("Vallejo & Freeport Blvd.","Freeport Blvd.","Vallejo Way","Sacramento","CA","38.551253","-121.488683",
    (select ID from saba_ID));
insert into location (locationName,NS_Street,EW_Street,city,state,latitude,longitude,organization_ID) values 
    ("West Capitol & Jefferson Blvd.","Jefferson Blvd.","W. Capitol Ave.","West Sacramento","CA","38.580614","-121.526599",
    (select ID from saba_ID));
insert into location (locationName,NS_Street,EW_Street,city,state,latitude,longitude,organization_ID) values 
    ("9th & L St.","9th Street","L Street","Sacramento","CA","38.578433","-121.495743",
    (select ID from saba_ID));

/*
-- Could use something like this to gin up the countEvent date
create view testEvent as 
    select DATETIME('now','+3 months');
-- then:
select * from testEvent; -- to return the date
*/
delete from count_event;
insert into count_event (startDate,endDate,organization_ID) values ("2015-11-15T16:00:00.000","2015-11-15T18:00:00.000",
    (select ID from saba_ID));
insert into count_event (startDate,endDate,organization_ID) values ("2016-03-10T16:00:00.000","2016-03-10T18:00:00.000",
    (select ID from saba_ID));

delete from counting_location;
insert into counting_location (countingLocationUID,countEvent_ID,location_ID,user_ID) values 
    ('alongnumber',
        (select ID from count_event where startDate="2015-11-15T16:00:00.000" and 
            organization_ID = (select ID from saba_ID)),
        (select ID from location where locationName = "Vallejo & Freeport Blvd." and 
            organization_ID = (select ID from saba_ID)),
        (select ID from user where email = 'bill@williesworkshop.net')
    );
insert into counting_location (countingLocationUID,countEvent_ID,location_ID,user_ID) values 
    ("anotherlongnumber",
        (select ID from count_event where startDate="2015-11-15T16:00:00.000" and 
            organization_ID = (select ID from saba_ID)),
        (select ID from location where locationName = "9th & L St." and 
            organization_ID = (select ID from saba_ID)),
        (select ID from user where email = 'jason@williesworkshop.net')
    );
    
delete from traveler;
insert into traveler (name,description,iconURL,travelerCode) values
    ("Male Bike Rider","A male on a bike riding in the street, not on the sidewalk","//bikeandwalk.org/images/travelers/BikeMale.png","BikeMale");
insert into traveler (name,description,iconURL,travelerCode) values
    ("Female Bike Rider","A female on a bike riding in the street, not on the sidewalk","//bikeandwalk.org/images/travelers/BikeFemale.png","BikeFemale");
insert into traveler (name,description,iconURL,travelerCode) values
    ("Male Bike Rider on Sidewalk","A male on a bike riding on the sidewalk, not in the street","//bikeandwalk.org/images/travelers/BikeMaleWalk.png","BikeMaleWalk");
insert into traveler (name,description,iconURL,travelerCode) values
    ("Female Bike Rider on Sidewalk","A female on a bike riding on the sidewalk, not in the street","//bikeandwalk.org/images/travelers/BikeFemaleWalk.png","BikeFemaleWalk");
insert into traveler (name,description,iconURL,travelerCode) values
    ("Male Pedestrian","Male Pedestrian","//bikeandwalk.org/images/travelers/MalePedestrian.png","PedestrianMale");
insert into traveler (name,description,iconURL,travelerCode) values
    ("Female Pedestrian","Female Pedestrian","//bikeandwalk.org/images/travelers/FemalePedestrian.png","PedestrianFemale");

delete from feature;
insert into feature (featureClass,featureValue) values
    ("Mode","Bicycle");
insert into feature (featureClass,featureValue) values
    ("Mode","Pedestrian");
insert into feature (featureClass,featureValue) values
    ("Gender","Male");
insert into feature (featureClass,featureValue) values
    ("Gender","Female");
insert into feature (featureClass,featureValue) values
    ("Behaviour","Sidewalk Riding");
insert into feature (featureClass,featureValue) values
    ("Behaviour","Helmet");
insert into feature (featureClass,featureValue) values
    ("Behaviour","No Helmet");

delete from traveler_feature;
insert into traveler_feature (traveler_ID,feature_ID) values
    ((select ID from traveler where travelerCode = "BikeMale"),(select ID from feature where featureClass = "Mode" and featureValue = "Bicycle"));
insert into traveler_feature (traveler_ID,feature_ID) values
    ((select ID from traveler where travelerCode = "BikeMale"),(select ID from feature where featureClass = "Gender" and featureValue = "Male"));
insert into traveler_feature (traveler_ID,feature_ID) values
    ((select ID from traveler where travelerCode = "BikeFemale"),(select ID from feature where featureClass = "Mode" and featureValue = "Bicycle"));
insert into traveler_feature (traveler_ID,feature_ID) values
    ((select ID from traveler where travelerCode = "BikeFemale"),(select ID from feature where featureClass = "Gender" and featureValue = "Female"));
insert into traveler_feature (traveler_ID,feature_ID) values
    ((select ID from traveler where travelerCode = "BikeMaleWalk"),(select ID from feature where featureClass = "Mode" and featureValue = "Bicycle"));
insert into traveler_feature (traveler_ID,feature_ID) values
    ((select ID from traveler where travelerCode = "BikeMaleWalk"),(select ID from feature where featureClass = "Gender" and featureValue = "Male"));
insert into traveler_feature (traveler_ID,feature_ID) values
    ((select ID from traveler where travelerCode = "BikeMaleWalk"),(select ID from feature where featureClass = "Behaviour" and featureValue = "Sidewalk Riding"));
insert into traveler_feature (traveler_ID,feature_ID) values
    ((select ID from traveler where travelerCode = "BikeFemaleWalk"),(select ID from feature where featureClass = "Mode" and featureValue = "Bicycle"));
insert into traveler_feature (traveler_ID,feature_ID) values
    ((select ID from traveler where travelerCode = "BikeFemaleWalk"),(select ID from feature where featureClass = "Gender" and featureValue = "Female"));
insert into traveler_feature (traveler_ID,feature_ID) values
    ((select ID from traveler where travelerCode = "BikeFemaleWalk"),(select ID from feature where featureClass = "Behaviour" and featureValue = "Sidewalk Riding"));
insert into traveler_feature (traveler_ID,feature_ID) values
    ((select ID from traveler where travelerCode = "PedestrianMale"),(select ID from feature where featureClass = "Mode" and featureValue = "Pedestrian"));
insert into traveler_feature (traveler_ID,feature_ID) values
    ((select ID from traveler where travelerCode = "PedestrianMale"),(select ID from feature where featureClass = "Gender" and featureValue = "Male"));
insert into traveler_feature (traveler_ID,feature_ID) values
    ((select ID from traveler where travelerCode = "PedestrianFemale"),(select ID from feature where featureClass = "Mode" and featureValue = "Pedestrian"));
insert into traveler_feature (traveler_ID,feature_ID) values
    ((select ID from traveler where travelerCode = "PedestrianFemale"),(select ID from feature where featureClass = "Gender" and featureValue = "Female"));

delete from event_traveler;
drop view if exists eventDate;
create view eventDate as select "2015-11-15";
insert into event_traveler (sortOrder,countEvent_ID,traveler_ID) values 
    (100,
    (select ID from count_event where date(startDate)=(select * from eventDate) and 
        organization_ID = (select ID from saba_ID)),
    (select ID from traveler where travelerCode = "BikeMale")
    );
insert into event_traveler (sortOrder,countEvent_ID,traveler_ID) values 
    (200,
    (select ID from count_event where date(startDate)=(select * from eventDate) and 
        organization_ID = (select ID from saba_ID)),
    (select ID from traveler where travelerCode = "BikeFemale")
    );
insert into event_traveler (sortOrder,countEvent_ID,traveler_ID) values 
    (300,
    (select ID from count_event where date(startDate)=(select * from eventDate) and 
        organization_ID = (select ID from saba_ID)),
    (select ID from traveler where travelerCode = "BikeMaleWalk")
    );
insert into event_traveler (sortOrder,countEvent_ID,traveler_ID) values 
    (400,
    (select ID from count_event where date(startDate)=(select * from eventDate) and 
        organization_ID = (select ID from saba_ID)),
    (select ID from traveler where travelerCode = "BikeFemaleWalk")
    );

drop view saba_ID;
drop view eventDate;

COMMIT TRANSACTION;

-- turn foreign key support on
PRAGMA foreign_keys=ON;
