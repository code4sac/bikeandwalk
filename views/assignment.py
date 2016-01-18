from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint, abort
from bikeandwalk import db, app
from models import Assignment, Location, User, CountEvent
from views.utils import printException, getDatetimeFromString, nowString, getUserChoices, getCountEventChoices, \
    getLocationChoices, cleanRecordID
from forms import AssignmentForm, AssignmentEditFromListForm
import hmac
from datetime import datetime
from views.trip import getAssignmentTripTotal

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
    if not id.isdigit() or int(id) < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
            
    id = int(id)
    
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
            out = "<table>"
            for rec in recs:
                totalTrips = getAssignmentTripTotal(rec.countEvent_ID, rec.location_ID)
                out += render_template('assignment/listElement.html', rec=rec, totalTrips=totalTrips)
            out +=  "</table>"
            
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
    formTemplate = 'assignment/popupEditForm.html'
    successTemplate = 'assignment/listElement.html'
    
    data = None
    if request.method.upper() == "post":
        # receive a json object containing the trips and other data
        data = request.get_json(force=True)
        print "Data: " + data
        
    if not data:
        data = request.form
        
    if "ID" in data:
        id = data["ID"]
    
    id = cleanRecordID(id)
    print "Assignment ID=" + str(id)
    if id < 0:
        flash("Invalid Record ID")
        return redirect(g.listURL)
        
    locations = None
    if id == 0:
        if "countEvent_ID" in data:
            g.countEventID = data["countEvent_ID"]
            
        ceID = cleanRecordID(g.countEventID)
        g.orgID = cleanRecordID(g.orgID)
        print "got to here..."
        
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
        print "Valid"
        if not rec:
            rec = createNewRecord(form.countEvent_ID.data)
            if  not rec:
                return "failure: Unable to create a new Assignment record"
                
        rec.location_ID = form.location_ID.data
        rec.countEvent_ID = form.countEvent_ID.data
        rec.user_ID = form.user_ID.data
        rec.weather = form.weather.data
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
    print "Ready to render..."
    return render_template(formTemplate, 
        form=form, locations=locations, 
        assigned=assignedUserIDs, 
        )
    
    

@mod.route('/assignment/sendInvite', methods=["GET","POST"])
@mod.route('/assignment/sendInvite/<id>/', methods=["GET","POST"])
def sendInvitationEmail(id):
    id=cleanRecordID(id)
    if id > 0:
        rec = Assignment.query.get(id)
        if rec and rec.user_ID > 0:
            ## send an email to the user
            pass

            return True
    #else
    printException("Unable to send email for ID ="+str(id),"error")
    return False
    
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
        cur = Assignment.query.filter(Assignment.assignmentUID == uid)
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
