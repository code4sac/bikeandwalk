from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint, abort
from bikeandwalk import db, app
from models import CountingLocation, Location, User, CountEvent
from views.utils import printException, getDatetimeFromString, nowString, getUserChoices, getCountEventChoices, \
    getLocationChoices
from forms import CountingLocationForm
import hmac

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
                recs[base]["counter"] = row.counter
                    
        return render_template('countingLocation/countingLocation_list.html', recs=recs)
        
    else:
        flash(printException('Could not open Database',"info"))
        return redirect(url_for('home'))
        

@mod.route("/super/countingLocation/edit/", methods=['GET'])
@mod.route("/super/countingLocation/edit/<id>", methods=['GET','POST'])
@mod.route("/super/countingLocation/edit/<id>/", methods=['GET','POST'])
def edit(id=0):
    setExits()
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
            rec = CountingLocation(hmac.new(nowString(),app.config["SECRET_KEY"]).hexdigest())
            db.session.add(rec)
        form.populate_obj(rec)
        db.session.commit()
        return redirect(g.listURL)
        
    return render_template('genericEditForm.html', rec=rec, form=form)
    
    
@mod.route("/countingLocation/delete/", methods=['GET'])
@mod.route("/countingLocation/delete/<id>", methods=['GET','POST'])
@mod.route("/countingLocation/delete/<id>/", methods=['GET','POST'])
def delete(id=0):
    setExits()
    if db:
        if int(id) > 0:
            rec = CountingLocation.query.get(id)
            if rec:
                db.session.delete(rec)
                db.session.commit()
            else:
                flash(printException("Could not delete that "+g.title + " record ID="+str(id)+" could not be found.","error"))
    else:
        flash(printException("Could not open database","info"))
        
    return redirect(g.listURL)
    
def getAssignedUsers(id=0):
    """ A list of the User IDs for those who are already
    assigned to a location for this event
    """
    a = [x.user_ID for x in CountingLocation.query.filter(CountingLocation.countEvent_ID == id) ]
    return a

### Mover to utils    
##def getUserChoices():
##    a = [(0,u"Select a User")]
##    b = [(x.ID, x.name) for x in User.query.filter(User.organization_ID == g.orgID).order_by('name')]
##    return a + b
##    
##def getCountEventChoices():
##    a = [(0,u"Select a Count Event")]
##    b = [(x.ID, getDatetimeFromString(x.startDate).strftime('%x')) for x in CountEvent.query.filter(CountEvent.organization_ID == g.orgID).order_by(CountEvent.startDate.desc())]
##    return a + b
##    
##def getLocationChoices():
##    a = [(0,u"Select a Location")]
##    b = [(x.ID, x.locationName) for x in Location.query.filter(Location.organization_ID == g.orgID).order_by(Location.locationName)]
##    return a + b
    