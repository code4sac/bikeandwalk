from flask import request, session, g, redirect, url_for, \
     render_template, flash
from bikeandwalk import db
from models import CountingLocation, Location, User
from views.db import printException, getDatetimeFromString

def setExits():
    g.listURL = url_for('countingLocation_list')
    g.editURL = url_for('countingLocation_edit')
    g.deleteURL = url_for('countingLocation_delete')
    g.title = 'Counting Location'

def countingLocation_list():
    setExits()
    if db :
        recs = None
        cl = CountingLocation.query.order_by(CountingLocation.eventStartDate.desc())
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
        
    
# Edit the Org
def countingLocation_edit(id=0):
    setExits()
    if db:
        if not request.form:
            """ if no form object, send the form page """
            # get the Org record if you can
            rec = None
            if int(id) > 0:
                rec = CountingLocation.query.get(id)
                
            return render_template('countingLocation/countingLocation_edit.html', rec=rec)

        #have the request form
        if validForm():
            try:
                if int(id) > 0:
                    rec = CountingLocation.query.get(id)
                else:
                    ## create a new record stub
                    rec = CountingLocation(request.form['featureClass'],request.form['featureValue'])
                    db.session.add(rec)
                #update the record
                rec.featureClass = request.form['featureClass']
                rec.featureValue = request.form['featureValue']
                db.session.commit()
                
                return redirect(url_for('countingLocation_list'))

            except Exception as e:
                flash(printException('Could not save record. Unknown Error',"error",e))

        # form not valid - redisplay
        return render_template('feature/countingLocation_edit.html', rec=request.form)

    else:
        flash(printException('Could not open database'),"info")

    return redirect(url_for('countingLocation_list'))

def countingLocation_delete(id=0):
    setExits()
    if db:
        if int(id) > 0:
            rec = CountingLocation.query.get(id)
            if rec:
                db.session.delete(rec)
                db.session.commit()
            else:
                flash(printException(g.title + " Record ID "+str(id)+" could not be found.","info"))
    else:
        flash(printException("Could not open database","info"))
        
    return redirect(url_for('countingLocation_list'))
    
def validForm():
    # Validate the form
    goodForm = True

    if request.form['featureClass'] == '':
        goodForm = False
        flash('Feature Class may not be blank')
    
    if request.form['featureValue'] == '':
        goodForm = False
        flash('Feature Value may not be blank')

    return goodForm
