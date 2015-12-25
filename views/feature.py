from flask import request, session, g, redirect, url_for, \
     render_template, flash
from bikeandwalk import db
from models import Feature
from views.db import printException

def setExits():
    g.listURL = url_for('feature_list')
    g.editURL = url_for('feature_edit')
    g.deleteURL = url_for('feature_delete')
    g.title = 'Feature'

def feature_list():
    if db :
        recs = Feature.query.all()
        setExits()
        return render_template('feature/feature_list.html', recs=recs)

    flash(printException('Could not open Database',"info"))
    return redirect(url_for('home'))
    
# Edit the Org
def feature_edit(id=0):
    if db:
        setExits()
        if not request.form:
            """ if no form object, send the form page """
            # get the Org record if you can
            rec = None
            if int(id) > 0:
                cur = Feature.query.filter_by(ID=id).first_or_404()
                
            return render_template('feature/feature_edit.html', rec=cur)

        #have the request form
        if validForm():
            try:
                if int(id) > 0:
                    cur = Feature.query.get(id)
                else:
                    ## create a new record stub
                    cur = Feature(request.form['featureClass'],request.form['featureValue'])
                    db.session.add(cur)
                #update the record
                cur.featureClass = request.form['featureClass']
                cur.featureValue = request.form['featureValue']
                db.session.commit()
                
                return redirect(url_for('feature_list'))

            except Exception as e:
                flash(printException('Could not save record. Unknown Error',"error",e))

        # form not valid - redisplay
        return render_template('feature/feature_edit.html', rec=request.form)

    else:
        flash(printException('Could not open database'),"info")

    return redirect(url_for('feature_list'))

def feature_delete(id=0):
    setExits()
    if db:
        if int(id) > 0:
            rec = Feature.query.get(id)
            if rec:
                db.session.delete(rec)
                db.session.commit()
            else:
                flash(printException(g.title + " Record ID "+str(id)+" could not be found.","info"))
    else:
        flash(printException("Could not open database","info"))
        
    return redirect(url_for('feature_list'))
    
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
