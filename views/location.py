from flask import request, g, redirect, url_for, \
     render_template, flash, Blueprint, abort
from bikeandwalk import db
from models import Location
from views.utils import printException, getDatetimeFromString, nowString
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
    if db :
        recs = None
        recs = Location.query.filter(Location.organization_ID == g.orgID).order_by(Location.locationName)
        
        return render_template('location/location_List.html', recs=recs)
        
    else:
        flash(printException('Could not open Database',"info"))
        return redirect(url_for('home'))
        

@mod.route("/location/edit/", methods=['GET'])
@mod.route("/location/edit/<id>", methods=['GET','POST'])
@mod.route("/location/edit/<id>/", methods=['GET','POST'])
def edit(id=0):
    setExits()
    if not id.isdigit() or int(id) < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
            
    id = int(id)
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
        
    return render_template('location/location_edit.html', rec=rec, form=form)
    
    
@mod.route("/location/delete/", methods=['GET'])
@mod.route("/location/delete/<id>", methods=['GET','POST'])
@mod.route("/location/delete/<id>/", methods=['GET','POST'])
def delete(id=0):
    setExits()
    if db:
        if int(id) > 0:
            rec = Location.query.get(id)
            if rec:
                db.session.delete(rec)
                db.session.commit()
            else:
                flash(printException("Could not delete that "+g.title + " record ID="+str(id)+" could not be found.","error"))
    else:
        flash(printException("Could not open database","info"))
        
    return redirect(g.listURL)
    