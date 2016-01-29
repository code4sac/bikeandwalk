from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint
from datetime import datetime, timedelta
from bikeandwalk import db,app
from views.utils import nowString, printException, getTimeZones, cleanRecordID
from views.assignment import getAssignmentList
from views.traveler import getTravelerList
from models import CountEvent, Organization, Assignment, EventTraveler, User

mod = Blueprint('count_event',__name__)

def setExits():
   g.listURL = url_for('.display')
   g.editURL = url_for('.edit')
   g.deleteURL = url_for('.delete')
   g.title = 'Count Event' ## Always singular


@mod.route('/event/')
def display():
    setExits()
    theTime = getTimeDictionary()
    cur = CountEvent.query.filter(CountEvent.organization_ID == int(g.orgID)).order_by(CountEvent.startDate.desc())
    if cur:
        ### need to loop through each record retireve an call getTimeDictionary
        ## then need to create a second level of the time dict : theTime[n][elementName]
        for row in cur:
            theTime[row.ID] = getTimeDictionary(row.startDate,row.endDate)
    
    return render_template('count_event/count_event_list.html', recs=cur, theTime=theTime)


@mod.route('/event/edit', methods=['POST', 'GET'])
@mod.route('/event/edit/', methods=['POST', 'GET'])
@mod.route('/event/edit/<id>/', methods=['POST', 'GET'])
def edit(id=0):
    setExits()
    id = cleanRecordID(id)
    if id < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
        
    assignmentList = getAssignmentList(id) #fully rendered HTML
    travelerList = getTravelerList(id)
    timeZones = getTimeZones()
    if not request.form:
        """ if no form object, send the form page """
        #Set up a default time for the event
        # Today with time set to something reasonable
        start = datetime.now().replace(hour=16, minute=0, second=0)
        end = start + timedelta(hours=2)
        
        theTime = getTimeDictionary(start.isoformat(),end.isoformat())
        cur = None
        #Get the default timeZone for this Organization
        g.timeZone = "PST"
        org = Organization.query.get(g.orgID)
        if org:
            g.timeZone = org.defaultTimeZone
            
        if id > 0:
            cur = CountEvent.query.filter_by(ID=id).first()
            if not cur:
                mes = g.title +" Record could not be found." + " ID:" + str(id)
                flash(printException(mes,"error"))
                return redirect(g.listURL)
            
            theTime = getTimeDictionary(cur.startDate,cur.endDate)
            g.timeZone = None
            
        
        return render_template('count_event/count_event_edit.html', 
            rec=cur ,theTime=theTime, 
            timeZones=timeZones, 
            assignmentList=assignmentList, 
            travelerList=travelerList,
            )

    #have the request form
    # handle the checkbox for Daylite savings time
    isDST = 0
    if request.form["isDST"]:
        isDST = request.form["isDST"]
        
    if validForm():
        startingDate = startDateFromForm()
        endingDate = endDateFromForm()
        try:
            if id > 0:
                cur = CountEvent.query.get(id)
                #update the record
                cur.title = request.form["title"]
                cur.startDate = startingDate.isoformat()[:19]
                cur.endDate = endingDate.isoformat()[:19]
                cur.isDST = isDST
                cur.timeZone = request.form["timeZone"]
                cur.organization_ID = request.form['organization_ID']
            else:
                ## create a new record
                cur = CountEvent(request.form["title"],startingDate.isoformat()[:19],endingDate.isoformat()[:19],request.form["timeZone"],isDST,request.form['organization_ID'])
                db.session.add(cur)
            db.session.commit()
            
            return redirect(g.listURL)

        except Exception as e:
            flash(printException('Error attempting to save '+g.title+' record.',"error",e))
            db.session.rollback()

    # form not valid - redisplay
    #restore theTime to the values as entered
    theTime = dict()
    theTime["hour"] = int(request.form["hour"])
    theTime["minute"] = int(request.form["minute"])
    theTime["duration"] = int(request.form["duration"])
    theTime["AMPM"] = request.form["AMPM"]
    theTime["eventDate"] = request.form["eventDate"]
    
    return render_template('count_event/count_event_edit.html', rec=request.form, theTime=theTime, timeZones=timeZones, assignmentList=assignmentList)


@mod.route('/event/delete', methods=['GET'])
@mod.route('/event/delete/', methods=['GET'])
@mod.route('/event/delete/<id>/', methods=['GET'])
def delete(id=0):
    setExits()
    id = cleanRecordID(id)
    if id < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)

    if id > 0:
        rec = CountEvent.query.filter(CountEvent.ID == id, CountEvent.organization_ID == g.orgID)
        if rec:
            try:
                #delete related records
                assigned = Assignment.query.filter(Assignment.countEvent_ID == id).delete()
                trav = EventTraveler.query.filter(EventTraveler.countEvent_ID == id).delete()
                rec.delete()
                db.session.commit()
                app.logger.info(g.title+' record (id='+str(id)+') Deleted by: ' + g.user + " on "+ datetime.now().isoformat())
            except Exception as e:
                flash(printException('Error attempting to delete '+g.title+' record.',"error",e))
                db.session.rollback()
        else:
            flash("Record could not be found.")
            
    return redirect(g.listURL)

@mod.route('/event/sendAssignment', methods=['GET'])
@mod.route('/event/sendAssignment/<assignmentID>/', methods=['GET'])
def sendAssignmentEmail(assignmentID):
    import mailer
    setExits()
    resultString = ""
    
    assignment = Assignment.query.get(cleanRecordID(assignmentID))
    if not assignment:
        resultString = "Invitaton Could not be sent. The Assignment Record could not be found"
        return resultString

    user = User.query.get(assignment.user_ID)
    if not user:
        resultString = "Invitaton Could not be sent. The User Record could not be found"
        return resultString

    countEvent = CountEvent.query.get(assignment.countEvent_ID)
    if not countEvent:
        resultString = "Invitaton Could not be sent. The Count Event record could not be found"
        return resultString

    countEventDict = getTimeDictionary(countEvent.startDate,countEvent.endDate)

    sendResult, resultString = mailer.sendInvite(assignment,user,countEventDict)

    return resultString


def validForm():
    # Validate the form
    goodForm = True
    
#    if not request.form['year'].isdigit() or len(request.form['year']) != 4:
#        goodForm = False
#        flash('The Year must be 4 digits')        
#    if not request.form['month'].isdigit() or int(request.form['month']) < 1 or int(request.form['month']) > 12:
#        goodForm = False
#        flash('The Month must be between 1 and 12')        
#    if not request.form['day'].isdigit() or int(request.form['day']) < 1 or int(request.form['day']) > 31:
#        goodForm = False
#        flash('The Day number must be between 1 and 31')        
       
    try:
        startingDate = startDateFromForm()
        print startingDate
    except:
        goodForm = False
        flash('There is a problem with your Starting Date')
    
    if request.form['organization_ID'] <= "0":
        goodForm = False
        flash('You must select an Organization')

    return goodForm

def startDateFromForm():
    ## 12 hour does not match the select item
    hour = ('00' + request.form['hour'])[-2:]
    minute = ('00' + request.form['minute'])[-2:]
    if request.form['AMPM'] == 'PM' and (int(hour) < 12):
        hour = str(int(hour) + 12)
    if request.form['AMPM'] == 'AM' and (int(hour) == 12):
        hour = "00"
    dateString = request.form["eventDate"] + "T" + hour + ":" + minute +":00"
    d = datetime.strptime(dateString,'%Y-%m-%dT%H:%M:%S')

    return d ## returns a datetime


def endDateFromForm():
    d = startDateFromForm()
    d = d + timedelta(hours=int(request.form['duration']))
    return d ## returns a datetime

def getTimeDictionary(start=datetime.now().isoformat(),end=(datetime.now() + timedelta(hours=2)).isoformat()):
    """
        start and end are iso formated date strings
    """
    #remove the milliseconds from the time string if present
    start = start[:19]
    end = end[:19]
    
    theTime = dict()
    if len(start)==19 and len(end) == 19:        
        #time stamp text could have a space or "T" time delimiter
        timeDelimiter = " "
        if "T" in start:
            timeDelimiter = "T"

        formatString = '%Y-%m-%d'+timeDelimiter+'%H:%M:%S'
        st = datetime.strptime(start, formatString) ## convert string to datetime
        
        timeDelimiter = " "
        if "T" in end:
            timeDelimiter = "T"

        formatString = '%Y-%m-%d'+timeDelimiter+'%H:%M:%S'
        et = datetime.strptime(end, formatString) ## convert string to datetime
        
        theTime["eventDate"] = datetime.strftime(st, '%Y-%m-%d')
        theTime["longStartDate"] = datetime.strftime(st, '%A, %B %d, %Y')
        theTime["startTime"] = datetime.strftime(st, '%I:%M %p')
        theTime["longEndDate"] = datetime.strftime(et, '%A, %B %d, %Y')
        theTime["endTime"] = datetime.strftime(et, '%I:%M %p')

        AMPM = "PM"
        theHour = st.hour
        if st.hour < 12:
            AMPM = "AM"
            if st.hour == 0:
                theHour = 12
        if st.hour > 12:
            theHour -= 12
        theTime['AMPM'] = AMPM
        theTime['hour'] = theHour
        theTime['strHour'] = ("00" + str(theHour))[-2:]
        theTime['minute'] = st.minute
        theTime['strMinute'] = ("00" + str(st.minute))[-2:]
        
        ## end time
        theTime['duration'] = et.hour - st.hour
        AMPM = "AM"
        theHour = et.hour
        if et.hour > 11:
            AMPM = "PM"
            theHour = theHour - 12
        theTime['AMPMEnd'] = AMPM
        theTime['hourEnd'] = theHour
        theTime['strHourEnd'] = ("00" + str(theHour))[-2:]
        theTime['minuteEnd'] = et.minute
        theTime['strMinuteEnd'] = ("00" + str(et.minute))[-2:]
        
        ## for testing
        theTime['startTimeStamp'] = start
        theTime['endTimeStamp'] = end
    return theTime

