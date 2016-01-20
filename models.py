from bikeandwalk import db
from sqlalchemy import *
from sqlalchemy.orm import *

"""
    So, it seems that SQLAlchemy can't figure out the table relationships if I try
    to suppress the underscore it wants to put into camelCase table names.
    I just have to accept it for now that 'countEvent' is created as 'count_event' in the 
    database.
"""
class Organization(db.Model):
    ID = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    defaultTimeZone = db.Column(db.String(3), default='PST')

    def __init__(self, name, email,defaultTimeZone='PST'):
        self.name = name
        self.email = email
        self.defaultTimeZone = defaultTimeZone

    def __repr__(self):
        return '<Org: %r>' % self.name
        

class User(db.Model):
    ID = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True, )
    userName = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(20))
    role = db.Column(db.String(20), default='counter')
    inactive = db.Column(db.Integer, default=0)
    organization_ID = db.Column(db.Integer, db.ForeignKey('organization.ID'), nullable=False)
    
    def __init__(self, name, email, organization_ID):
        self.name = name
        self.email = email
        self.organization_ID = organization_ID

    def __repr__(self):
        return '<User %r>' % self.name
        
class Location(db.Model):
    ID = db.Column(db.Integer, primary_key=True)
    locationName = db.Column(db.Text, nullable=False)
    NS_Street = db.Column(db.Text)
    EW_Street = db.Column(db.Text)
    locationType = db.Column(db.Text)
    city = db.Column(db.Text)
    state = db.Column(db.Text)
    latitude = db.Column(db.Text)
    longitude = db.Column(db.Text)
    organization_ID = db.Column(db.Integer, db.ForeignKey('organization.ID'), nullable=False)
    
    def __init__(self, name, org):
        self.locationName = name
        self.organization_ID = org

    def __repr__(self):
        return self.locationName
    

class CountEvent(db.Model):
    #__tablename__ = 'countEvent'
    ID = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    startDate = db.Column(db.Text, nullable=False)
    endDate = db.Column(db.Text, nullable=False)
    timeZone = db.Column(db.Text)
    isDST = db.Column(db.Integer, default=0)
    organization_ID = db.Column(db.Integer, db.ForeignKey('organization.ID'), nullable=False)

    def __init__(self, title, start, end, timeZone, isDST, org):
        self.title = title
        self.startDate = start
        self.endDate = end
        self.timeZone = timeZone
        self.isDST = isDST
        self.organization_ID = org

    def __repr__(self):
        return '<Start: %r, End: %r>' % (self.startDate, self.endDate)
    

class Assignment(db.Model):
    __tablename__ = 'assignment'
    ID = db.Column(db.Integer, primary_key=True)
    assignmentUID = db.Column(db.Text, unique=True)
    weather = db.Column(db.Text)
    countEvent_ID = db.Column(db.Integer, db.ForeignKey('count_event.ID'))
    location_ID = db.Column(db.Integer, db.ForeignKey('location.ID'))
    user_ID = db.Column(db.Integer, db.ForeignKey('user.ID'))

    #countevent = relationship(CountEvent)
    #locations = relationship(Location)
    #user = relationship(User)
    
    # Get the Starting date of the related event
    eventStartDate = deferred(select([CountEvent.startDate]).where(CountEvent.ID == countEvent_ID))
    organization_ID = deferred(select([CountEvent.organization_ID]).where(CountEvent.ID == countEvent_ID))
    locationName = deferred(select([Location.locationName]).where(Location.ID == location_ID))
    userName = deferred(select([User.name]).where(User.ID == user_ID))

    def __init__(self, eventID, UID):
        self.countEvent_ID = eventID
        self.assignmentUID = UID

    def __repr__(self):
        return '<UID: %r>' % self.assignmentUID
    
class Traveler(db.Model):
    ID = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    iconURL = db.Column(db.Text)
    travelerCode = db.Column(db.Text, nullable=False, unique=True)

    def __init__(self, name, code):
        self.name = name
        self.travelerCode = code

    def __repr__(self):
        return '<Trav: %r>' % self.name


class Trip(db.Model):
    ID = db.Column(db.Integer, primary_key=True)
    tripCount = db.Column(db.Integer)
    tripDate = db.Column(db.Text)
    turnDirection = db.Column(db.Text)
    seqNo = db.Column(db.Text)
    location_ID = db.Column(db.Integer, db.ForeignKey('location.ID'))
    traveler_ID = db.Column(db.Integer, db.ForeignKey('traveler.ID'))
    countEvent_ID = db.Column(db.Integer, db.ForeignKey('count_event.ID'))

    countevent = relationship(CountEvent)
    location = relationship(Location)
    traveler = relationship(Traveler)
    
    #from views.utils import getDatetimeFromString
    
    # Get the Starting date of the related event
    eventStartDate = deferred(select([CountEvent.startDate]).where(CountEvent.ID == countEvent_ID))
    travelerName = deferred(select([Traveler.name]).where(Traveler.ID == traveler_ID))
    locationName = deferred(select([Location.locationName]).where(Location.ID == location_ID))

    def __init__(self, tripCnt,tripDate,turnDirection,seqNo,location_ID,traveler_ID,countEvent_ID):
        self.tripCount = tripCnt
        self.tripDate = tripDate
        self.turnDirection = turnDirection
        self.seqNo = seqNo
        self.location_ID = location_ID
        self.traveler_ID = traveler_ID
        self.countEvent_ID = countEvent_ID

    def __repr__(self):
        return '<Date: %r>' % self.tripDate
        
## a place to stash trips that don't validate for some reason
### SQLAlchemy is supposed to support inheritance so we wouldn't need
###    to restate all this, but it looks hard. 8-(
class ProvisionalTrip(db.Model):
    ID = db.Column(db.Integer, primary_key=True)
    tripCount = db.Column(db.Integer)
    tripDate = db.Column(db.Text)
    turnDirection = db.Column(db.Text)
    seqNo = db.Column(db.Text)
    location_ID = db.Column(db.Integer, db.ForeignKey('location.ID'))
    traveler_ID = db.Column(db.Integer, db.ForeignKey('traveler.ID'))
    countEvent_ID = db.Column(db.Integer, db.ForeignKey('count_event.ID'))
    issue = db.Column(db.Text) #The reason trip was suspect

    countevent = relationship(CountEvent)
    location = relationship(Location)
    traveler = relationship(Traveler)

    #from views.utils import getDatetimeFromString

    # Get the Starting date of the related event
    eventStartDate = deferred(select([CountEvent.startDate]).where(CountEvent.ID == countEvent_ID))
    travelerName = deferred(select([Traveler.name]).where(Traveler.ID == traveler_ID))
    locationName = deferred(select([Location.locationName]).where(Location.ID == location_ID))

    def __init__(self, tripCnt,tripDate,turnDirection,seqNo,location_ID,traveler_ID,countEvent_ID):
        self.tripCount = tripCnt
        self.tripDate = tripDate
        self.turnDirection = turnDirection
        self.seqNo = seqNo
        self.location_ID = location_ID
        self.traveler_ID = traveler_ID
        self.countEvent_ID = countEvent_ID

    def __repr__(self):
        return '<Date: %r>' % self.tripDate


class EventTraveler(db.Model):
    ID = db.Column(db.Integer, primary_key=True)
    sortOrder = db.Column(db.Integer, default=0)
    countEvent_ID = db.Column(db.Integer, db.ForeignKey('count_event.ID'))
    traveler_ID = db.Column(db.Integer, db.ForeignKey('traveler.ID'))
    
    travelerName = deferred(select([Traveler.name]).where(Traveler.ID == traveler_ID))
    
    def __init__(self, event, traveler):
        self.countEvent_ID = event
        self.traveler_ID = traveler

    def __repr__(self):
        return '<EventTrav: %r : %r>' % (self.countEvent_ID, self.traveler_ID)


"""
CREATE TABLE IF NOT EXISTS travelerFeature (
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   traveler_ID INTEGER REFERENCES traveler(ID) ON DELETE CASCADE,
   feature_ID INTEGER REFERENCES feature(ID) ON DELETE CASCADE
);
"""
class TravelerFeature(db.Model):
    ID = db.Column(db.Integer, primary_key=True)
    traveler_ID = db.Column(db.Integer, db.ForeignKey('traveler.ID'))
    feature_ID = db.Column(db.Integer, db.ForeignKey('feature.ID'))

    def __init__(self, traveler, feature):
        self.traveler_ID = traveler
        self.feature_ID = feature

    def __repr__(self):
        return '<TravFeat: %r / %r>' % (self.traveler_ID, self.feature_ID)

"""
CREATE TABLE IF NOT EXISTS feature (
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   featureClass TEXT,
   featureValue TEXT
);
"""
class Feature(db.Model):
    ID = db.Column(db.Integer, primary_key=True)
    featureClass = db.Column(db.Text)
    featureValue = db.Column(db.Text)

    def __init__(self, theClass, theValue):
        self.featureClass = theClass
        self.featureValue = theValue

    def __repr__(self):
        return '<Feat: %r : %r>' % (self.featureClass, self.featureValue)
    
