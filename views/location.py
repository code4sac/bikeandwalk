from flask import request, g, redirect, url_for, \
     render_template, flash, Blueprint, abort
from bikeandwalk import db, app
from models import Location
from views.trip import getLocationTripTotal
from views.utils import printException, getDatetimeFromString, nowString, cleanRecordID
from forms import LocationForm

mod = Blueprint('location',__name__)

def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.delete')
    g.title = 'Location'
    
@mod.route("/location/", methods=['GET'])
@mod.route("/location", methods=['GET'])
def display():
    setExits()
    recs = Location.query.filter(Location.organization_ID == g.orgID).order_by(Location.state,Location.city,Location.locationName)
    
    return render_template('location/location_list.html', recs=recs)



@mod.route("/location/edit/", methods=['GET'])
@mod.route("/location/edit/<id>", methods=['GET','POST'])
@mod.route("/location/edit/<id>/", methods=['GET','POST'])
def edit(id=0):
    setExits()
    defaultLoc = {'lat': app.config['LOCATION_DEFAULT_LAT'], 'lng': app.config['LOCATION_DEFAULT_LNG']}
    #LOCATION_DEFAULT_LNG
    #LOCATION_DEFAULT_LAT
    
    id = cleanRecordID(id)
    if id < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
            
    g.tripTotalCount = getLocationTripTotal(id)
    rec = None
    if id > 0:
        rec = Location.query.get(id)
        if not rec:
            flash(printException("Could not edit that "+g.title + " record. ID="+str(id)+")",'error'))
            return redirect(g.listURL)
    
    form = LocationForm(request.form, rec)

    if request.method == 'POST' and form.validate():
        if not rec:
            rec = Location(form.locationName.data,g.orgID)
            db.session.add(rec)
        form.populate_obj(rec)
        db.session.commit()
        return redirect(g.listURL)
        
    return render_template('location/location_edit.html', rec=rec, form=form, defaultLoc=defaultLoc)
    
    
@mod.route("/location/delete/", methods=['GET'])
@mod.route("/location/delete/<id>", methods=['GET','POST'])
@mod.route("/location/delete/<id>/", methods=['GET','POST'])
def delete(id=0):
    setExits()
    id = cleanRecordID(id)
    if id < 0:
        flash("That is not a valid record ID")
        return redirect(g.listURL)

    if id > 0:
        rec = Location.query.filter(Location.ID == id, Location.organization_ID == g.orgID).first()
        if rec:
            db.session.delete(rec)
            db.session.commit()
        else:
            flash(printException("Could not delete that "+g.title + " record ID="+str(id)+" could not be found or was wrong org.","error"))

    return redirect(g.listURL)
