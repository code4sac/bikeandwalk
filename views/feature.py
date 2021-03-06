from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint
from bikeandwalk import db
from models import Feature
from views.utils import printException, cleanRecordID

mod = Blueprint('feature',__name__)

def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.delete')
    g.title = 'Feature'

@mod.route('/features')
@mod.route('/feature')
def display():
    if db :
        recs = Feature.query.all()
        setExits()
        return render_template('feature/feature_list.html', recs=recs)

    flash(printException('Could not open Database',"info"))
    return redirect(url_for('home'))
    
    
@mod.route('/feature/edit', methods=['POST', 'GET'])
@mod.route('/feature/edit/', methods=['POST', 'GET'])
@mod.route('/feature/edit/<id>/', methods=['POST', 'GET'])
def edit(id=0):
    setExits()
    id = cleanRecordID(id)
    if id < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
        
    if db:
        if not request.form:
            """ if no form object, send the form page """
            # get the Org record if you can
            rec = None
            if id > 0:
                rec = Feature.query.filter_by(ID=id).first_or_404()
                
            return render_template('feature/feature_edit.html', rec=rec)

        #have the request form
        if validForm():
            try:
                if int(id) > 0:
                    rec = Feature.query.get(id)
                else:
                    ## create a new record stub
                    rec = Feature(request.form['featureClass'],request.form['featureValue'])
                    db.session.add(rec)
                #update the record
                rec.featureClass = request.form['featureClass']
                rec.featureValue = request.form['featureValue']
                db.session.commit()
                
                return redirect(url_for('.display'))

            except Exception as e:
                flash(printException('Could not save record. Unknown Error',"error",e))

        # form not valid - redisplay
        return render_template('feature/feature_edit.html', rec=request.form)

    else:
        flash(printException('Could not open database'),"info")

    return redirect(url_for('.display'))

@mod.route('/feature/delete', methods=['POST'])
@mod.route('/feature/delete/<id>/', methods=['GET'])
def delete(id=0):
    setExits()
    id = cleanRecordID(id)
    if id < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
            
    if db:
        if id > 0:
            rec = Feature.query.get(id)
            if rec:
                db.session.delete(rec)
                db.session.commit()
            else:
                flash(printException(g.title + " Record ID "+str(id)+" could not be found.","info"))
    else:
        flash(printException("Could not open database","info"))
        
    return redirect(url_for('.display'))
    
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
