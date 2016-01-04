## this is where the count data is received and stored
from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint
from datetime import datetime, timedelta
from bikeandwalk import db,app
from models import CountEvent, Trip, Location, CountingLocation,\
    Traveler, EventTraveler, User
from db import printException, getDatetimeFromString, getLocalTimeAtEvent
import json
from views.utils import getTurnDirectionList

mod = Blueprint('count',__name__)


def setExits():
    g.countBeginURL = url_for('.count_begin')
    #g.editURL = url_for('feature_edit')
    #g.deleteURL = url_for('feature_delete')
    g.title = 'Count'

@mod.route('/count', methods=['POST', 'GET'])
@mod.route('/count/', methods=['POST', 'GET'])
@mod.route('/count/<UID>', methods=['POST', 'GET'])
@mod.route('/count/<UID>/', methods=['POST', 'GET'])
def count_begin(UID=""):
    UID = UID.strip()
    # remember if the initial request did not include a UID
    noInitialUID = UID == "" 
    
    if request.form and request.form['UID']:
        UID = request.form['UID']
        
    setExits()
    g.UID = UID
    g.UIDStatus = "noUID"
    
    ## UID not supplied
    if UID == "":
        g.title = 'No Counting Location ID'
        return render_template("count/no-uid.html")
    # lookup the UID
    cntLoc = CountingLocation.query.filter_by(countingLocationUID= UID).first()
    ## UID not valid
    if not cntLoc:
        g.title = "Count ID Not Found"
        g.UIDStatus = "notFound"
        return render_template("count/no-uid.html")
    #get the data related to this count location
    event = CountEvent.query.filter_by(ID=cntLoc.countEvent_ID).first()
    if not event:
        g.title = "No Event Found"
        g.UIDStatus ="noEvent"
        return render_template("count/no-uid.html")
        # get the event date
        
    localTime = getLocalTimeAtEvent(event.timeZone,event.isDST) # Get the current local time at the event location
    endDate = getDatetimeFromString(event.endDate)
    
    if endDate <= (localTime + timedelta(days=1)):
        # The count date has passed
        g.title="Count Event is over"
        g.UIDStatus = "countOver"
        g.endDate = endDate.isoformat()
        g.now = (datetime.now() + timedelta(days=1)).isoformat()[:19]
        return render_template("count/no-uid.html")
    
    ## test the Location
    location = Location.query.filter_by(ID=cntLoc.location_ID).first()
    if not location:
        g.title="Location not Found"
        g.UIDStatus = "noLocation"
        return render_template("count/no-uid.html")
        
    if noInitialUID:
        #Redirect to here but with UID
        return redirect(url_for("count_begin")+UID+"/")
        
    ## Valid UID
    #Get the travelers
    et = EventTraveler.query.filter_by(countEvent_ID=cntLoc.countEvent_ID).order_by(EventTraveler.sortOrder).all()
    g.travelerCnt = EventTraveler.query.filter_by(countEvent_ID=cntLoc.countEvent_ID).count()
    if not et:
        g.UIDStatus = "noTravelers"
        g.title = "No Travlers Found"
        return render_template("count/no-uid.html")
        
    travelers = dict()
    for elem in range(g.travelerCnt):
        trav = Traveler.query.filter_by(ID=et[elem].traveler_ID).first()
        if trav:
            traveler = dict()
            traveler['row'] = elem
            traveler['travelerCode'] = trav.travelerCode
            traveler['iconURL'] = trav.iconURL
            traveler['name'] = trav.name
            traveler['ID'] = trav.ID
            travelers[elem]=traveler
            
    user = User.query.filter_by(ID=cntLoc.user_ID).first()
    #Ok, send the count page
    return render_template("count/count.html", cntLoc=cntLoc, event=event, location=location, travelers=travelers, user=user)
    
def isValidUID(UID=""):
    return CountingLocation.query.filter_by(countingLocationUID= UID).exists()
    

@mod.route('/count/trip', methods=['POST', 'GET'])
@mod.route('/count/trip/', methods=['POST', 'GET'])
def count_trip():
    theResult = "Unknown"
    try:
        # receive a json object containing the trips and other data
        data = request.get_json(force=True)
       
        # get the countEvent record because we need the timezone offset
        rec = CountEvent.query.get(int(data['countEvent']))
        try:
            if rec:
                startDate = getDatetimeFromString(rec.startDate)
                endDate = getDatetimeFromString(rec.endDate)
                localTime = getLocalTimeAtEvent(rec.timeZone,rec.isDST) # Get the current local time at the event location
            else:
                raise ValueError("CountEvent Record No Found")
                
        except ValueError as e:
            printException("CountEvent Record No Found","error")
            theResult = "CountEventError"
            return '{"result":"'+theResult+'"}'
            
        #determine the start and end times of the event
        
        for i in range(len(data['trips'])):
            d = datetime.utcnow() + timedelta(hours=-7)
            trip = dict()
            trip['action'] = data['action']
            trip['seqNo'] = data['trips'][i]['seqNo']
            trip['location_ID'] = data['location']
            trip['countEvent_ID'] = data['countEvent']
            
            if trip['action'] == "undo":
                try:
                    rec = Trip.query.filter(Trip.location_ID == trip['location_ID'], \
                        Trip.countEvent_ID == trip['countEvent_ID'], \
                        Trip.seqNo == trip['seqNo']).first()
                        
                    if rec:
                        db.session.delete(rec)
                        db.session.commit()
                    
                except Exception as e:
                    printException('Could not undo Trip '+str(i),"error",e)

            else: #Add
                trip['tripCount'] = data['trips'][i]['count']
                trip['tripDate'] = data['trips'][i]['tripDate'].strip()
                trip['turnDirection'] = data['trips'][i]['direction'].strip()
                trip['traveler_ID'] = data['trips'][i]['traveler']
                
                if isValidTrip(trip,startDate,endDate,localTime) or True: #### Always Valid for Now #####
                    try:
                        cur = Trip(trip['tripCount'],trip['tripDate'],trip['turnDirection'],trip['seqNo'],trip['location_ID'],trip['traveler_ID'],trip['countEvent_ID'])
                        db.session.add(cur)
                        #mark this trip as saved
                        #db.session.commit()            
                    except Exception as e:
                        printException('Could not record Trip '+str(i),"error",e)
                        # log the data collected?
                        # mark this trip as failed?
            
        db.session.commit()
        theResult = "Success"

    except Exception as e:
        printException('Bad JSON data in post',"error",e)
        theResult = request.data
        printException("json = " + theResult,"info")
        
    return '{"result":"'+theResult+'"}'

def isValidTrip(trip,startDate,endDate,localTime):
    #trip is a dictionary of trip data
        #trip['tripCount']
        #trip['tripDate'] 
        #trip['turnDirection']
        #trip['location_ID']
        #trip['traveler_ID']
        #trip['countEvent_ID']
        
    isValid = True
    
    #test that the tripTime is in the time frame of the countEvent
    if getDatetimeFromString(trip['tripDate']) < localTime:
        isValid = False
        #flash("That trip date is before the count event")

    if getDatetimeFromString(trip['tripDate']) > localTime:
        isValid = False
        #flash("That trip date is after the count event")
        
    #test that all the trip data elements are present and valid
    if trip['turnDirection'] == "" or \
       trip['turnDirection'] not in getTurnDirectionList() :
        isValid = False
        #flash(trip['turnDirection'] + " is not a valid Turn Direction")
    
    #test that location ID is valid
    
    #test that traveler ID is valid
    
    #test that the countEvent ID is valid
    
    if not isValid:
        #record the errors to a log...
        pass
        
    return isValid
    
