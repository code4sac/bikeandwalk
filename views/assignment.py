from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint, abort
from bikeandwalk import db, app
from models import Assignment, Location, User, CountEvent, Trip, Traveler
from views.utils import printException, getDatetimeFromString, nowString, getUserChoices, getCountEventChoices, \
    getLocationChoices, cleanRecordID
from forms import AssignmentForm, AssignmentEditFromListForm
import hmac
from datetime import datetime
from views.trip import getAssignmentTripTotal
from views.traveler import getTravelersForEvent
from datetime import timedelta

mod = Blueprint('assignment',__name__)

def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.delete')
    g.title = 'Assignment'
    
    
@mod.route("/super/assignment/", methods=['GET'])
@mod.route("/super/assignment", methods=['GET'])
def display():
    setExits()
    if db :
        recs = None
        cl = Assignment.query.filter(Assignment.organization_ID == g.orgID).order_by(Assignment.eventStartDate.desc())
        # collect additional data for each record
        if cl:
            recs = dict()
            for row in cl:
                base = str(row)
                recs[base] = dict()
                recs[base]["ID"] = row.ID
                recs[base]['UID'] = row.assignmentUID
                recs[base]['startDate'] = getDatetimeFromString(row.eventStartDate).strftime('%x @ %I:%M %p')
                recs[base]["location"] = row.locationName
                recs[base]["userName"] = row.userName
                    
        return render_template('assignment/assignment_list.html', recs=recs)
        
    else:
        flash(printException('Could not open Database',"info"))
        return redirect(url_for('home'))
        

@mod.route("/super/assignment/edit/", methods=['GET'])
@mod.route("/super/assignment/edit/<id>", methods=['GET','POST'])
@mod.route("/super/assignment/edit/<id>/", methods=['GET','POST'])
def edit(id="0"):
    setExits()
    id = cleanRecordID(id)
    if id < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
        
    rec = None
    if id > 0:
        rec = Assignment.query.get(id)
        if not rec:
            flash(printException("Could not edit that "+g.title + " record. ID="+str(id)+")",'error'))
            return redirect(g.listURL)
    
    form = AssignmentForm(request.form, rec)
        
    ## choices need to be assigned before rendering the form
    # AND before attempting to validate it
    form.user_ID.choices = getUserChoices()
    form.countEvent_ID.choices = getCountEventChoices()
    form.location_ID.choices = getLocationChoices()
    g.AssignedUserIDs = ()
    if rec: 
        g.AssignedUserIDs = getAssignedUsers(int(rec.countEvent_ID))

    if request.method == 'POST' and form.validate():
        if not rec:
            rec = createNewRecord(form.countEvent_ID.data)
            if not rec:
                return redirect(g.listURL)
                    
        form.populate_obj(rec)
        db.session.commit()
        return redirect(g.listURL)
        
    return render_template('genericEditForm.html', rec=rec, form=form)
    
    
@mod.route("/assignment/delete/", methods=['GET'])
@mod.route("/assignment/delete/<id>", methods=['GET','POST'])
@mod.route("/assignment/delete/<id>/", methods=['GET','POST'])
def delete(id="0"):
    setExits()
    id = cleanRecordID(id)
    
    if id < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
                        
    if deleteRecordID(id):
        pass
    else:
        flash(printException("Could not delete that "+g.title + " record ID="+str(id)+" could not be found.","error"))
        
    return redirect(g.listURL)
    
def getAssignedUsers(id=0):
    """ A list of the User IDs for those who are already
    assigned to a location for this event
    """
    a = [x.user_ID for x in Assignment.query.filter(Assignment.countEvent_ID == id) ]
    return a

## return an HTML code segment to include in the count_event edit form
@mod.route("/assignment/getAssignmentList", methods=['GET'])
@mod.route("/assignment/getAssignmentList/<countEventID>/", methods=['GET','POST'])
def getAssignmentList(countEventID=0):
    countEventID = cleanRecordID(countEventID)
    out = ""
    
    if countEventID > 0:
        recs = Assignment.query.filter(Assignment.countEvent_ID==countEventID).order_by(Assignment.locationName)
        if recs:
            out = ""
            for rec in recs:
                totalTrips = getAssignmentTripTotal(rec.countEvent_ID, rec.location_ID)
                out += render_template('assignment/listElement.html', rec=rec, totalTrips=totalTrips)
            
    return out
    
@mod.route("/assignment/createFromList", methods=['GET',"POST"])
@mod.route("/assignment/createFromList/<countEventID>/", methods=['GET',"POST"])
def createFromList(countEventID="0"):
    """
    Create a new Assignment record from the CountEvent edit form
    """
    #the template popupEditForm will substitue this for the missing countEvent_ID
    g.countEventID = cleanRecordID(countEventID)
    return editFromList(0)
    
    
## editing list called from within countEvent form
@mod.route("/assignment/editFromList", methods=['GET',"POST"])
@mod.route("/assignment/editFromList/<id>/", methods=['GET',"POST"])
def editFromList(id="0"):
    """
        handle the editing from the count event form.
        Intended for use with AJAX request
        There should always be POST data
    """
    ## when creating a new record, g.countEventID will contain the ID of the countEvent record
    setExits()
    
    data = None
    if not data:
        data = request.form
        
    if "ID" in data:
        id = data["ID"]
    
    id = cleanRecordID(id)
    if id < 0:
        flash("Invalid Record ID")
        return redirect(g.listURL)
        
    locations = None
    if id == 0:
        if "countEvent_ID" in data:
            g.countEventID = data["countEvent_ID"]
            
        ceID = cleanRecordID(g.countEventID)
        g.orgID = cleanRecordID(g.orgID)
        
        ## It's important to call fetchAll() or fetchOne() after executing sql this way or the
        ##  database will be left in a locked state.
        
        sql = 'select ID,locationName from location where organization_ID = %d \
               and ID not in \
               (select location_ID from assignment where countEvent_ID  = %d);' \
            % (g.orgID, ceID)
        
        locations = db.engine.execute(sql).fetchall()
        if len(locations) == 0:
            return "failure: There are no more Locations to use."
        
        
    rec = None
    if id > 0:
        rec = Assignment.query.get(id)
        if not rec:
            flash(printException("Could not edit that "+g.title + " record. (ID="+str(id)+")",'error'))
            return redirect(g.listURL)
    
    form = AssignmentEditFromListForm(data, rec)
        
    ## choices need to be assigned before rendering the form
    # AND before attempting to validate it
    form.user_ID.choices = getUserChoices()        

    if request.method == "POST" and form.validate():
        if not rec:
            rec = createNewRecord(form.countEvent_ID.data)
            if  not rec:
                return "failure: Unable to create a new Assignment record"
                
        rec.location_ID = form.location_ID.data
        rec.countEvent_ID = form.countEvent_ID.data
        rec.user_ID = form.user_ID.data
        try:
            db.session.commit()
        except Exception as e:
            printException("Unable to save Assignment from list", "error", e)
            return "failure: Sorry. Unable to save your changes."
            
        return "success" # the success function looks for this...
        
            
    assignedUserIDs = ()
    if rec: 
        g.countEventID = int(rec.countEvent_ID)
        
    assignedUserIDs = getAssignedUsers(g.countEventID)
    return render_template('assignment/popupEditForm.html', 
        form=form, 
        locations=locations, 
        assigned=assignedUserIDs, 
        )
    
@mod.route('/assignment/editTripsFromList', methods=["GET","POST"])
@mod.route('/assignment/editTripsFromList/<id>/', methods=["GET","POST"])
def editTripsFromList(id):
    setExits()
    tripData = {} #empty dictionary
    id=cleanRecordID(id)
    if id > 0:
        rec = Assignment.query.get(id)
        if not rec:
            return "failure: Assignment record not found"
            
        tripCount = getAssignmentTripTotal(id)
        if tripCount > 0:
            return "failure: There are already trips recorded."
        
        # Get travelers
        travelers = getTravelersForEvent(rec.countEvent_ID)        
        
        #populate tripData with info on manually enterd counts
        tripData = getTurnData(rec)
        countEvent = CountEvent.query.get(rec.countEvent_ID)
        
        timeFrames = getTripTimeFrames(getDatetimeFromString(countEvent.startDate),getDatetimeFromString(countEvent.endDate))
        
        if request.method == "POST":
            # Validate form?
            result = True
            # record trips
            for countInputName in tripData.keys():
                if not request.form[countInputName]:
                    tripCount = 0
                else:
                    tripCount = request.form[countInputName]

                turnLeg = tripData[countInputName][1]
                travelerID = tripData[countInputName][2]
                try:
                    tripCount = int(tripCount) #this may throw a ValueError
                    if tripCount < 0:
                        result = False
                        raise ValueError("Negative values are not allowed.")
                        
                    if tripCount != tripData[countInputName][0]:
                         #delete the previous manual trips, if any
                         # gin up the possible start and end times
                         startTime, endTime = getTimeStampFromTimeFrame(tripData[countInputName][3].split("-")[0],countEvent.startDate)
                        
                         try:
                             trips = Trip.query.filter(Trip.countEvent_ID == rec.countEvent_ID, 
                                                       Trip.location_ID == rec.location_ID, 
                                                       Trip.traveler_ID == travelerID, 
                                                       Trip.tripDate >= startTime,
                                                       Trip.tripDate <= endTime,
                                                       Trip.turnDirection == turnLeg, 
                                                       Trip.seqNo == "000"
                                                       ).delete()
                         except:
                             pass #the trip records may not exist
                             
                             
                         if tripCount > 0:
                             # genterate the trip time stamp
                             startTime, endTime = getTimeStampFromTimeFrame(tripData[countInputName][3].split("-")[0],countEvent.startDate)
                             try:
                                 cur = Trip(tripCount,endTime,turnLeg,"000",rec.location_ID,travelerID,rec.countEvent_ID)
                                 db.session.add(cur)
                             except Exception as e:
                                 result = False
                                 flash(printException('Could not record Trip for ' + turnLeg,"error",e))
                                
                except ValueError as e:
                    result = False
                    #remove the 'standard' errpr message
                    mes = "%s" % (e)
                    if mes[0:7] == 'invalid':
                        mes = ''
                        
                    trav = Traveler.query.get(travelerID)
                    errTrav = "a traveler"
                    if trav:
                        errTrav = trav.name

                    flash("The value '%s' in turn %s of %s is invalid. %s" % (tripCount,turnLeg,errTrav,mes))
                            
            if result:
                db.session.commit()
                return "success" # this is an ajax request
            else:
                db.session.rollback()
                tripData = getTurnData(rec,request.form)
                flash("No changes were saved.")
                
        # render form
        return render_template('assignment/editTrips.html',
            rec=rec, 
            travelers=travelers,
            tripData=tripData,
            timeFrames=timeFrames
            )
        
    return "failure: Unable to edit trips for Assignment"
    
    
@mod.route('/assignment/deletefromList', methods=["GET","POST"])
@mod.route('/assignment/deletefromList/<id>/', methods=["GET","POST"])
def deleteFromList(id):
    id=cleanRecordID(id)
    if deleteRecordID(id):
        return "success"
    else:
        return "failure: Unable to Delete that record."

def getUID():
    i = 0
    while i < 1000:
        uid = hmac.new(datetime.now().isoformat(), app.config["SECRET_KEY"]).hexdigest()
        cur = Assignment.query.filter(Assignment.assignmentUID == uid).count()
        if cur:
            i += 1
        else:
            break
            
    return uid
    
def createNewRecord(eventID=None):
    """ return a reference to a newly created record or elss None"""
    eventID=cleanRecordID(eventID)
    rec = None
    if eventID > 0:
        #test that countEvent record exits
        cnt = CountEvent.query.filter(CountEvent.ID == eventID).count()
        if cnt > 0:
            rec = Assignment(eventID,getUID())
            db.session.add(rec)
        else:
            flash(printException("Invalid countEvent ID during Count Event creation.","error"))
            
    return rec
    
def deleteRecordID(id):
    id = cleanRecordID(id)
    g.orgID = cleanRecordID(g.orgID)
    # Can't delete an assignment with trips
    rec = Assignment.query.get(id)
    if rec:
        if getAssignmentTripTotal(rec.countEvent_ID, rec.location_ID) > 0:
            return False
            
    if id > 0:
        #rec = Assignment.query.get(id)
        sql = 'DELETE FROM assignment  \
        WHERE assignment."ID" = %d AND (SELECT count_event."organization_ID" \
        FROM count_event \
        WHERE count_event."organization_ID" = %d);' % (id,g.orgID)
        try:
            rec = db.engine.execute(sql)
        except:
            return False
        return True
       
    return False

def getTurnData(assignmentRec, inputForm=None):
    ''' 
    return a dictionary of lists with data that will be used to populate the input form
    when editing the trip data from the assignment record. 
    
    Dictionary layout: 
    ---- Key --- : [TripCount, turnDirection, travelerID]
    
    if inputForm (the request.form obj.) is provided, use the values there instead of querying db
    
    '''
    
    tripData = {}
    
    # Get travelers
    travelers = getTravelersForEvent(assignmentRec.countEvent_ID)        
    ce = CountEvent.query.get(assignmentRec.countEvent_ID)
    timeFrames = getTripTimeFrames(getDatetimeFromString(ce.startDate),getDatetimeFromString(ce.endDate))
    
    
    for traveler in travelers:
        for leg in ("A", "B", "C", "D"):
            for turn in range(3):
                turnLeg = leg + str(turn+1)
                for timeFrame in timeFrames:
                    countInputName = "%d-%s-%s" % (traveler.ID,turnLeg,timeFrame)
                    tripData[countInputName] = [0,turnLeg,traveler.ID,timeFrame]
                    if inputForm and countInputName in inputForm:
                        # load the matching value from the input form object
                        tripData[countInputName][0] = inputForm[countInputName]
                    else:
                        # get the current manual count if any from the database
                        # Calculate the start and end time for the current time frame
                        startTime, endTime = getTimeStampFromTimeFrame(timeFrame,ce.startDate)
                        tripData[countInputName][0] = getAssignmentTripTotal(assignmentRec.countEvent_ID, assignmentRec.location_ID, traveler.ID, startTime, endTime, turnLeg, "000")
                        
    return tripData


def getTripTimeFrames(startDateTime,endDateTime):
    # return a list of start and end times for 15 minute count segments. Used to render and record 
    #    manually entered trip counts.
    #e.g.: ["0:00~0:15","0:16~0:30","0:31~0:45","0:46~1:00","1:01~1:15","1:16~1:30","1:31~1:45","1:46~2:00"]
    
    e = b = datetime.now().replace(hour=0,minute=0)
    duration = endDateTime.hour - startDateTime.hour
    timeFrames = []
    for h in range(duration):
       for m in range(4):
           e = e + timedelta(minutes=15)
           timeFrames.append("%d:%02d~%d:%02d" % (b.hour,b.minute,e.hour,e.minute))
           b = e + timedelta(minutes=1)

    return timeFrames
    
    
def getTimeStampFromTimeFrame(timeFrame,baseTimeString):
    # Returns two datetime strings for the start time and end time of the timeFrame string
    # The timeFrame is in the format: h:mm~h:mm
    #baseTimeString is the string representation of the start of the count event
    
    t = timeFrame.split("~") # = "1:15~1:30" for example
    
    # get the minute offset from the timeFrame to add to the start time
    m = int(t[0].split(":")[0])*60 + int(t[0].split(":")[1])
    tripTime = getDatetimeFromString(baseTimeString) #Start timestamp text to time
    tripTime = tripTime + timedelta(minutes=m)
    startTime = tripTime.isoformat()[:19]
    
    m = int(t[1].split(":")[0])*60 + int(t[1].split(":")[1])
    tripTime = getDatetimeFromString(baseTimeString) #Start timestamp text to time
    tripTime = tripTime + timedelta(minutes=m)
    endTime = tripTime.isoformat()[:19]
    
    return startTime, endTime
    