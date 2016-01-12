from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint, abort
from bikeandwalk import db, app
from models import CountingLocation, Location, User, CountEvent
from views.utils import printException, getDatetimeFromString, nowString, getUserChoices, getCountEventChoices, \
    getLocationChoices, cleanRecordID
from forms import CountingLocationForm, CountingLocationEditFromListForm
import hmac
from datetime import datetime

mod = Blueprint('countingLocation',__name__)

def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.delete')
    g.title = 'Counting Location'
    
    
@mod.route("/super/countingLocation/", methods=['GET'])
@mod.route("/super/countingLocation", methods=['GET'])
def display():
    setExits()
    if db :
        recs = None
        cl = CountingLocation.query.filter(CountingLocation.organization_ID == g.orgID).order_by(CountingLocation.eventStartDate.desc())
        # collect additional data for each record
        if cl:
            recs = dict()
            for row in cl:
                base = str(row)
                recs[base] = dict()
                recs[base]["ID"] = row.ID
                recs[base]['UID'] = row.countingLocationUID
                recs[base]['startDate'] = getDatetimeFromString(row.eventStartDate).strftime('%x @ %I:%M %p')
                recs[base]["location"] = row.locationName
                recs[base]["userName"] = row.userName
                    
        return render_template('countingLocation/countingLocation_list.html', recs=recs)
        
    else:
        flash(printException('Could not open Database',"info"))
        return redirect(url_for('home'))
        

@mod.route("/super/countingLocation/edit/", methods=['GET'])
@mod.route("/super/countingLocation/edit/<id>", methods=['GET','POST'])
@mod.route("/super/countingLocation/edit/<id>/", methods=['GET','POST'])
def edit(id="0"):
    setExits()
    if not id.isdigit() or int(id) < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
            
    id = int(id)
    
    rec = None
    if id > 0:
        rec = CountingLocation.query.get(id)
        if not rec:
            flash(printException("Could not edit that "+g.title + " record. ID="+str(id)+")",'error'))
            return redirect(g.listURL)
    
    form = CountingLocationForm(request.form, rec)
        
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
    
    
@mod.route("/countingLocation/delete/", methods=['GET'])
@mod.route("/countingLocation/delete/<id>", methods=['GET','POST'])
@mod.route("/countingLocation/delete/<id>/", methods=['GET','POST'])
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
    a = [x.user_ID for x in CountingLocation.query.filter(CountingLocation.countEvent_ID == id) ]
    return a

## return an HTML code segment to include in the count_event edit form
@mod.route("/countingLocation/getAssignmentList", methods=['GET'])
@mod.route("/countingLocation/getAssignmentList/<countEventID>/", methods=['GET','POST'])
def getAssignmentList(countEventID=0):
    countEventID = cleanRecordID(countEventID)
    out = ""
    
    if countEventID > 0:
        recs = CountingLocation.query.filter(CountingLocation.countEvent_ID==countEventID).order_by(CountingLocation.locationName)
        if recs:
            out = "<table>"
            for rec in recs:
                out += render_template('countingLocation/listElement.html', rec=rec)
            out +=  "</table>"
            
    return out
    
## editing list called from within countEvent form
@mod.route("/countingLocation/editFromList", methods=['GET',"POST"])
@mod.route("/countingLocation/editFromList/<id>/", methods=['GET',"POST"])
def editFromList(id="0"):
    """
        handle the editing from the count event form.
        Intended for use with AJAX request
        There should always be POST data
    """
    setExits()
    formTemplate = 'countingLocation/popupEditForm.html'
    successTemplate = 'countingLocation/listElement.html'
    
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
        sql = 'select ID,locationName from location where organization_ID = %d \
               and ID not in \
               (select location_ID from counting_location where countEvent_ID  = %d);' \
            % (g.orgID, int(data["countEvent_ID"]))

        locations = db.engine.execute(sql)
        if locations == None:
            flash("There are no more Locations to use.")
            ## Just refresh the count Event form?
        
    rec = None
    if id > 0:
        rec = CountingLocation.query.get(id)
        if not rec:
            flash(printException("Could not edit that "+g.title + " record. (ID="+str(id)+")",'error'))
            return redirect(g.listURL)
    
    form = CountingLocationEditFromListForm(data, rec)
        
    ## choices need to be assigned before rendering the form
    # AND before attempting to validate it
    form.user_ID.choices = getUserChoices()        
    
    if request.method == "POST" and form.validate():
        print "Valid"
        if not rec:
            rec = createNewRecord(form.countEvent_ID.data)
            if not rec:
                flash("Unable to create a new Assignment record")
                return redirect(g.listURL)
        
        rec.location_ID = form.location_ID.data
        rec.countEvent_ID = form.countEvent_ID.data
        rec.user_ID = form.user_ID.data
        rec.weather = form.weather.data
        rec.countType = form.countType.data
    
        db.session.commit()
        return "success" # the success function looks for this...
        
            
    assignedUserIDs = ()
    if rec: 
        assignedUserIDs = getAssignedUsers(int(rec.countEvent_ID))
    
    return render_template(formTemplate, 
        form=form, locations=locations, 
        assigned=assignedUserIDs, 
        )
    
    

@mod.route('/countingLocation/sendInvite', methods=["GET","POST"])
@mod.route('/countingLocation/sendInvite/<id>/', methods=["GET","POST"])
def sendInvitationEmail(id):
    id=cleanRecordID(id)
    if id > 0:
        rec = CountingLocation.query.get(id)
        if rec and rec.user_ID > 0:
            ## send an email to the user
            pass

            return True
    #else
    printException("Unable to send email for ID ="+str(id),"error")
    return False
    
@mod.route('/countingLocation/deletefromList', methods=["GET","POST"])
@mod.route('/countingLocation/deletefromList/<id>/', methods=["GET","POST"])
def deleteFromList(id):
    id=cleanRecordID(id)
    if deleteRecordID(id):
        return "success"
    else:
        return "failure"

def getUID():
    uid = hmac.new(datetime.now().isoformat(), app.config["SECRET_KEY"]).hexdigest()
    return uid
    
def createNewRecord(eventID=None):
    """ return a reference to a newly created record or elss None"""
    eventID=cleanRecordID(eventID)
    rec = None
    if eventID > 0:
        #test that countEvent record exits
        cnt = CountEvent.query.filter(CountEvent.ID == eventID).count()
        if cnt > 0:
            rec = CountingLocation(eventID,getUID())
            db.session.add(rec)
        else:
            flash(printException("Invalid countEvent ID during countingEvent creation.","error"))
            
    return rec
    
def deleteRecordID(id):
    if id > 0:
        rec = CountingLocation.query.get(id)
        if rec:
            db.session.delete(rec)
            db.session.commit()
            
            return True
       
    return False
