-- Get the list of traveler data for a count event
create view event as 
    select ID 
    from countEvent 
    where date(startDate) = "2015-11-15" 
        and organization_ID = (select ID from organization where email = "info@sacbike.org");
/*
    eventTraveler.sortOrder, traveler.id, traveler.iconURL,
*/
SELECT 
    et.sortOrder, 
    t.ID as travelerID, 
    t.iconURL 
from 
    eventTraveler as et, 
    traveler as t 
where 
    et.countEvent_ID=(select ID from event) 
    and 
    et.traveler_ID = t.ID 
order by 
    et.sortOrder;

drop view event;

-- Get the location data for a countingLocation
/*
    countingLocation.id, countingLocation.countingLocationUID, countingLocation.countType,
    countEvent.startDate, countEvent.endDate,
    location.ID, location.locationName, location.NS_Street, location.EW_Street
*/
select 
    cl.ID as countlocationID, 
    cl.countingLocationUID, 
    cl.countType, 
    DATE(ce.startDate) as eventDate, 
    TIME(ce.startDate) as startTime, 
    TIME(ce.endDate) as endTime, 
    l.ID as locationID,
    l.locationName, 
    l.NS_Street, 
    l.EW_Street
from
    countingLocation as cl, 
    countEvent as ce, 
    location as l
where
    cl.countingLocationUID = 'anotherlongnumber'
    and
    l.ID = cl.location_ID
    and
    ce.ID =cl.countEvent_ID
;

