from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint
from bikeandwalk import db
from models import Organization
from views.utils import getTimeZones, printException, cleanRecordID

mod = Blueprint('org',__name__)

def setExits():
    g.listURL = url_for('.org_list')
    g.editURL = url_for('.org_edit')
    g.deleteURL = url_for('.org_delete')
    g.title = 'Orgnaization' ## Always singular

@mod.route('/org')
def org_list():
    if db :
        rec = Organization.query.all()
        setExits()
        return render_template('org/org_list.html', recs=rec)

    flash('Could not open Database')
    return redirect(url_for('home'))
    
# Edit the Org
@mod.route('/org/edit', methods=['POST', 'GET'])
@mod.route('/org/edit/', methods=['POST', 'GET'])
@mod.route('/org/edit/<id>/', methods=['POST', 'GET'])
def org_edit(id=0):
    setExits()
    id = cleanRecordID(id)
    if id < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
     
    timeZones = getTimeZones()
    if not request.form:
        """ if no form object, send the form page """
        # get the Org record if you can
        rec = None
        if int(id) > 0:
            rec = Organization.query.get(id)
            
        return render_template('org/org_edit.html', rec=rec, timeZones=timeZones)
            
            
    #have the request form
    if validForm():
        if id > 0:
            rec = Organization.query.get(id)
        else:
            ## create a new record stub
            rec = Organization(request.form['name'],request.form['email'],request.form["defaultTimeZone"])
            db.session.add(rec)
        #update the record
        rec.name = request.form['name']
        rec.email = request.form['email']
        rec.defaultTimeZone = request.form["defaultTimeZone"]
        try:
            db.session.commit()
        except Exception as e:
            flash(printException('Error attempting to create '+g.title+' record.',"error",e))
            db.session.rollback()
            
        return redirect(url_for('.org_list'))
        
    # form not valid - redisplay
    return render_template('org/org_edit.html', rec=request.form, timeZones=timeZones)


@mod.route('/org/delete', methods=['GET'])
@mod.route('/org/delete/', methods=['GET'])
@mod.route('/org/delete/<id>/', methods=['GET'])
def org_delete(id=0):
    setExits()
    id = cleanRecordID(id)
    if id < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
    
    if id > 0:
        rec = Organization.query.get(id)
        if rec:
            db.session.delete(rec)
            db.session.commit()
        else:
            flash("Record could not be deleted.")
            
    return redirect(url_for('.org_list'))
    
def validForm():
    # Validate the form
    goodForm = True
    
    if request.form['name'] == '':
        goodForm = False
        flash('Name may not be blank')
    if request.form['name'] != '':
        rec = Organization.query.filter(Organization.name == request.form['name'], Organization.ID != request.form['ID']).count()
        if rec > 0 :
            goodForm = False
            flash('That name is already in use')

    if request.form['email'] == '':
        goodForm = False
        flash('Email may not be blank')
    if request.form['email'] != '':
        rec = Organization.query.filter(Organization.email == request.form['email'], Organization.ID != request.form['ID']).count()
        if rec > 0 :
            goodForm = False
            flash('That email address is already in use for another Organization')


    return goodForm

def getName(orgID):
    orgID = cleanRecordID(orgID)
    if orgID > 0:
        org = Organization.query.get(orgID)
        if org:
            return org.name
        
    return ''
    
def getOrgDefaultTimeZone(orgID):
    orgID = cleanRecordID(orgID)
    if orgID > 0:
        org = Organization.query.get(orgID)
        if org:
            return org.defaultTimeZone

    return ""