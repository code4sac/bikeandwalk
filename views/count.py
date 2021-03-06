## this is where the count data is received and stored
from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint
from datetime import datetime, timedelta
from bikeandwalk import db,app
from models import CountEvent, Trip, Location, Assignment,\
    Traveler, EventTraveler, User, ProvisionalTrip
import json
from views.utils import getTurnDirectionList, printException, getDatetimeFromString, \
    getLocalTimeAtEvent, cleanRecordID
    
from views.trip import getAssignmentTripTotal
from views.traveler import getEventTravelers

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
        g.title = 'No Assignment ID'
        return render_template("count/no-uid.html")
    # lookup the UID
    cntLoc = Assignment.query.filter_by(assignmentUID= UID).first()
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
    print localTime
    print endDate
    print (endDate + timedelta(days=1))
    
    if localTime >= endDate + timedelta(days=1):
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
        return redirect(url_for(".count_begin")+UID+"/")
        
    ## Valid UID
    #Get the travelers
    et = getEventTravelers(cntLoc.countEvent_ID)
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
    
    gridType="intersection"
    if location.locationType[0:10].upper() == "SCREENLINE":
        gridType = "screenline"
        
    #Ok, send the count page
    return render_template("count/count.html", cntLoc=cntLoc, event=event, location=location, travelers=travelers, user=user, gridType=gridType)
    
def isValidUID(UID=""):
    return Assignment.query.filter_by(assignmentUID= UID).exists()
    

@mod.route('/count/trip', methods=['POST', 'GET'])
@mod.route('/count/trip/', methods=['POST', 'GET'])
def count_trip():
    #theResult = "Unknown"
    try:
        # receive a json object containing the trips and other data
        data = request.get_json(force=True)
        
    except Exception as e:
        printException('Bad JSON data in post',"error",e)
        printException("json = " + request.data,"info")
        return '{"result":"success"}'
        
    # get the countEvent record because we need the timezone offset
    rec = CountEvent.query.get(int(data['countEvent']))
    try:
        if rec:
            startDate = getDatetimeFromString(rec.startDate)
            endDate = getDatetimeFromString(rec.endDate)
            localTime = getLocalTimeAtEvent(rec.timeZone,rec.isDST) # Get the current local time at the event location
        else:
            raise ValueError("CountEvent Record No Found")
            
    except Exception as e:
        printException("CountEvent Record No Found","error")
        #theResult = "CountEventError"
        return '{"result":"success"}'
        
    trip = dict()
    trip['action'] = data.get('action')
    trip['location_ID'] = cleanRecordID(data.get('location'))
    trip['countEvent_ID'] = cleanRecordID(data.get('countEvent'))
    
    ## There is an 'action' called as 'total' with no trips data.
    ##  This loop will not execute and only the current total will be returned
    
    for i in range(len(data['trips'])):
        #d = datetime.utcnow() + timedelta(hours=-7)
        temp = data['trips'][i] # get the dict for the trip
        trip['seqNo'] = cleanRecordID(temp.get('seqNo'))
        trip['tripCount'] = cleanRecordID(temp.get("count"))
        trip['tripDate'] = temp.get('tripDate', "").strip()
        trip['turnDirection'] = temp.get('direction', "").strip()
        trip['traveler_ID'] = cleanRecordID(temp.get('traveler'))
        
        tripDate = getDatetimeFromString(trip['tripDate'])
        if not tripDate:
            # bad date string, log it and go to the next record
            printException("Bad trip date: " + temp, "error")
            continue # do next loop
           
        if trip['action'] == "undo":
            ## don't allow old trips to be undone
            ### If the trip is more than 1 minute in the past, it can't be deleted
            if tripDate + timedelta(minutes= 1) > localTime:
                
                try:
                    rec = Trip.query.filter(Trip.location_ID == trip['location_ID'], \
                        Trip.countEvent_ID == trip['countEvent_ID'], \
                        Trip.seqNo == trip['seqNo'], \
                        Trip.tripDate == trip["tripDate"]).first()
                    
                    if rec:
                        db.session.delete(rec)
                        db.session.commit()
                
                except Exception as e:
                    printException('Could not undo Trip '+str(i),"error",e)
            

        if trip["action"] == "add":
            
            validTrip, errorMess = isValidTrip(trip,startDate,endDate,localTime)
            
            if validTrip or True: #### Always Valid for Now #####
                try:
                    cur = Trip(trip['tripCount'],trip['tripDate'],trip['turnDirection'],trip['seqNo'],trip['location_ID'],trip['traveler_ID'],trip['countEvent_ID'])
                    db.session.add(cur)
                    db.session.commit()            
                except Exception as e:
                    printException('Could not record Trip '+str(i),"error",e)
                    printException("trip data: " + str(data), "info" )
                    
            else:
                #not a valid trip, so save in provisionalTrip table
                try:
                    cur = ProvisionalTrip(trip['tripCount'],trip['tripDate'],trip['turnDirection'],trip['seqNo'],trip['location_ID'],trip['traveler_ID'],trip['countEvent_ID'])
                    db.session.add(cur)
                    cur.issue = errorMess
                    
                    # inform the responsible parties
                    #sendProvisionalTripEmail() #Sends an email no more than once a day
                    
                except Exception as e:
                    printException('Could not record provisional Trip',"error",e)
                    printException("trip data: " + str(data), "info" )
                    
        else:
            #Bad action request
            pass
            
    try:
        db.session.commit()
    except Exception as e:
        printException("Unable to commit to trip or provisionalTrip", "error", e)
        printException("trip data: " + str(data), "info" )
        
    #Get the total so far:
    totalCnt = getAssignmentTripTotal(trip["countEvent_ID"], trip["location_ID"])
    
    return '{"result":"success", "total": %d}' % (totalCnt)

def isValidTrip(trip,startDate,endDate,localTime):
    #trip is a dictionary of trip data
        #trip['tripCount']
        #trip['tripDate'] 
        #trip['turnDirection']
        #trip['location_ID']
        #trip['traveler_ID']
        #trip['countEvent_ID']
    
    isValid = True
    errorMess = ""
    
    #test that the tripTime is in the time frame of the countEvent
    if getDatetimeFromString(trip['tripDate']) < localTime:
        isValid = False
        errorMess += "That trip date is before the count event. "

    if getDatetimeFromString(trip['tripDate']) > localTime:
        isValid = False
        errorMess += "That trip date is after the count event. "
        
    #test that all the trip data elements are present and valid
    if trip['turnDirection'] == "" or \
       trip['turnDirection'] not in getTurnDirectionList() :
        isValid = False
        errorMess += trip['turnDirection'] + " is not a valid Turn Direction. "
    
    #test that location and count_event ID is valid
    tempTest = False
    try:
        cur = Assignment.query.filter(Assignment.location_ID == cleanRecordID(trip["location_ID"]), Assignment.countEvent_ID == cleanRecordID(trip["countEvent_ID"]))
        if cur:
            tempTest = True
    except:
        pass
    
    if not tempTest:
        isValid = False
        errorMess += str(trip["location_ID"]) + " is not a valid location ID. "
        
     #test that traveler ID is valid
    tempTest = False
    try:
        cur = EventTraveler.query.filter(EventTraveler.countEvent_ID == cleanRecordID(trip["countEvent_ID"]), EventTraveler.traveler_ID == cleanRecordID(trip["traveler_ID"]))
        if cur:
            tempTest = True
    except:
        pass
    
    if not tempTest:
        isValid = False
        errorMess += str(trip["traveler_ID"]) + " is not a valid Traveler ID. "
       
    
    # An error or testing
    #isValid = False
    #errorMess += "This should not have happened!"
    
    return isValid, errorMess
    
