from flask import request, session, g, redirect, url_for, \
     render_template, flash
from bikeandwalk import db
from models import Organization
from views.db import getTimeZones, printException

def setExits():
    g.listURL = url_for('org_list')
    g.editURL = url_for('org_edit')
    g.deleteURL = url_for('org_delete')
    g.title = 'Orgnaization' ## Always singular

def org_list():
    if db :
        cur = Organization.query.all()
        setExits()
        return render_template('org/org_list.html', recs=cur)

    flash('Could not open Database')
    return redirect(url_for('home'))
    
# Edit the Org
def org_edit(id=0):
    if db:
        setExits()
        timeZones = getTimeZones()
        if not request.form:
            """ if no form object, send the form page """
            # get the Org record if you can
            cur = None
            if int(id) > 0:
                cur = Organization.query.filter_by(ID=id).first_or_404()
                
            return render_template('org/org_edit.html', rec=cur, timeZones=timeZones)

        #have the request form
        if validForm():
            try:
                if int(id) > 0:
                    cur = Organization.query.get(id)
                else:
                    ## create a new record stub
                    cur = Organization(request.form['name'],request.form['email'],request.form["defaultTimeZone"])
                    db.session.add(cur)
                #update the record
                cur.name = request.form['name']
                cur.email = request.form['email']
                cur.defaultTimeZone = request.form["defaultTimeZone"]
                db.session.commit()
                
                return redirect(url_for('org_list'))
#                    except sqlite3.OperationalError:
#                        flash('sqlite3 Operational error')
#                    except sqlite3.IntegrityError:
#                        flash('sqlite3 Integrity Error')
            except Exception as e:
                flash(printException('Error attempting to create '+g.title+' record.',"error",e))
                db.session.rollback()
            

        # form not valid - redisplay
        return render_template('org/org_edit.html', rec=request.form, timeZones=timeZones)

    else:
        flash('Could not open database')

    return redirect(url_for('org_list'))

def org_delete(id=0):
    setExits()
    if int(id) > 0:
        rec = Organization.query.get(id)
        if rec:
            db.session.delete(rec)
            db.session.commit()
        else:
            flash("Record could not be deleted.")
            
    return redirect(url_for('org_list'))
    
def validForm():
    # Validate the form
    goodForm = True
    
    if request.form['name'] == '':
        goodForm = False
        flash('Name may not be blank')
    if request.form['name'] != '':
        cur = Organization.query.filter(Organization.name == request.form['name'], Organization.ID != request.form['ID']).count()
        if cur > 0 :
            goodForm = False
            flash('That name is already in use')

    if request.form['email'] == '':
        goodForm = False
        flash('Email may not be blank')
    if request.form['email'] != '':
        cur = Organization.query.filter(Organization.email == request.form['email'], Organization.ID != request.form['ID']).count()
        if cur > 0 :
            goodForm = False
            flash('That email address is already in use for another Organization')


    return goodForm

def getName(orgID):
    if orgID > 0:
        org = Organization.query.get(orgID)
        if org:
            return org.name
        
    return ''
    
    