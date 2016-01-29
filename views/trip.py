from flask import request, g, redirect, url_for, \
     render_template, flash, Blueprint, abort
from bikeandwalk import db
from models import Trip
from views.utils import printException, getCountEventChoices, \
    getLocationChoices, getTravelerChoices, getTurnDirectionChoices, cleanRecordID
from forms import TripForm

mod = Blueprint('trip',__name__)

def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.delete')
    g.title = 'Trip'
    
@mod.route("/trip/", methods=['GET'])
@mod.route("/trip", methods=['GET'])
def display():
    setExits()
    if db :
        recs = None
        recs = Trip.query.order_by(Trip.tripDate)

        return render_template('trip/trip_list.html', recs=recs)
        
    else:
        flash(printException('Could not open Database',"info"))
        return redirect(url_for('home'))
        

@mod.route("/trip/edit/", methods=['GET'])
@mod.route("/trip/edit/<id>", methods=['GET','POST'])
@mod.route("/trip/edit/<id>/", methods=['GET','POST'])
def edit(id=0):
    setExits()
    id = cleanRecordID(id)
    if id < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
            
    rec = None
    if id > 0:
        rec = Trip.query.get(id)
        if not rec:
            flash(printException("Could not edit that "+g.title + " record. ID="+str(id)+")",'error'))
            return redirect(g.listURL)
    
    form = TripForm(request.form, rec)
    ## choices need to be assigned before rendering the form
    # AND before attempting to validate it
    form.countEvent_ID.choices = getCountEventChoices()
    form.location_ID.choices = getLocationChoices()
    form.traveler_ID.choices = getTravelerChoices()
    form.turnDirection.choices = getTurnDirectionChoices()
    
    if request.method == 'POST' and form.validate():
        if not rec:
            rec = Trip(form.tripCount.data,form.tripDate.data,form.turnDirection.data,form.seqNo.data,form.location_ID.data,form.traveler_ID.data,form.countEvent_ID.data)
            db.session.add(rec)
        form.populate_obj(rec)
        db.session.commit()
        return redirect(g.listURL)
        
    return render_template('genericEditForm.html', rec=rec, form=form)
    
    
@mod.route("/trip/delete/", methods=['GET'])
@mod.route("/trip/delete/<id>", methods=['GET','POST'])
@mod.route("/trip/delete/<id>/", methods=['GET','POST'])
def delete(id=0):
    setExits()
    id = cleanRecordID(id)
    if id < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
        
    if id > 0:
        rec = Trip.query.get(id)
        if rec:
            db.session.delete(rec)
            db.session.commit()
        else:
            flash(printException("Could not delete that "+g.title + " record ID="+str(id)+" could not be found.","error"))
        
    return redirect(g.listURL)
    
def getAssignmentTripTotal(countEventID=0, locationID=0):
    result = 0
    countEventID = cleanRecordID(countEventID)
    locationID = cleanRecordID(locationID)
    sql =  "select sum(tripCount) as tripTotal from trip where countEvent_ID = %d and location_ID = %d;" % (int(countEventID), int(locationID))
    cur = db.engine.execute(sql).fetchone()
    if cur:
        result = cur[0]
        if result == None:
            result = 0
            
    return result
    
def getEventTravelerTripTotal(countEventID = 0, travelerID =0):
    result = 0
    countEventID = cleanRecordID(countEventID)
    travelerID = cleanRecordID(travelerID)
    sql =  "select sum(tripCount) as tripTotal from trip where countEvent_ID = %d and traveler_ID = %d;" % (countEventID, travelerID)
    cur = db.engine.execute(sql).fetchone()
    if cur:
        result = cur[0]
        if result == None:
            result = 0
            
    return result
    
