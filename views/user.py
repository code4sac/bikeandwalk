from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash
from time import time
import re
from bikeandwalk import db,app
from models import User

def setExits():
    g.listURL = url_for('user_list')
    g.editURL = url_for('user_edit')
    g.deleteURL = url_for('user_delete')
    g.title = 'User'

def user_list():
    if db :
        setExits()
        recs = User.query.filter(User.organization_ID == int(g.orgID)).order_by(User.name)
        return render_template('user/user_list.html', recs=recs)

    flash('Could not open Database')
    return redirect(url_for('index'))
    
# Edit the user
def user_edit(id=0):
    if db:
        rec = None
        setExits()
        
        if not request.form:
            """ if no form object, send the form page """
            # get the user record if you can
            if int(id) > 0:
                rec = User.query.filter_by(ID=id).first_or_404()
                
            return render_template('user/user_edit.html', rec=rec)

        #have the request form
        #ensure a value for the check box
        inactive = request.form.get('inactive')
        if not inactive: 
            inactive = "0"

        if validForm():
            try:
                if int(id) > 0:
                    rec = User.query.get(id)
                else:
                    ## create a new record stub
                    rec = User(request.form['name'],request.form['email'],request.form['organization_ID'])
                    db.session.add(rec)
                #update the record
                rec.name = request.form['name']
                rec.email = request.form['email']
                rec.role = request.form['role']
                rec.inactive = str(inactive)
                rec.organization_ID = request.form['organization_ID']
                
                ### for now the username and password are not used
                rec.userName = db.null()
                rec.password = db.null()
                #if str(uName) !='':
                #    rec.userName = str(uName)
                #    rec.password = request.form['password']
                #else:
                #    rec.userName = db.null()
                #    rec.password = db.null()
                
                
                db.session.commit()
                
                return redirect(url_for('user_list'))
            except:
                flash(printException('Error attempting to save '+g.title+' record.',"error",e))

        # form not valid - redisplay
        return render_template('user/user_edit.html', rec=request.form)

    else:
        flash('Could not open database')

    return redirect(url_for('user_list'))

def user_delete(id=0):
    setExits()
    if int(id) > 0:
        rec = User.query.get(id)
        if rec:
            try:
                db.session.delete(rec)
                db.session.commit()
            except Exception as e:
                flash(printException('Error attempting to delete '+g.title+' record.',"error",e))
        else:
            flash("Record could not be deleted.")
            
    return redirect(url_for('user_list'))
    
def validForm():
    # Validate the form
    global uName, inactive
    goodForm = True
    
    if request.form['name'] == '':
        goodForm = False
        flash('Name may not be blank')

    if request.form['email'] == '':
        goodForm = False
        flash('Email may not be blank')

    if request.form['email'] != '':
        cur = User.query.filter(User.email == request.form['email'], User.ID != request.form['ID']).count()
        if cur > 0 :
            goodForm = False
            flash('That email address is already in use')
        #test the format of the email address (has @ and . after @)
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", request.form['email']):
            goodForm = False
            flash('That doesn\'t look like a valid email address')
            
    if request.form['organization_ID'] <= "0":
        goodForm = False
        flash('You must select an Organization')

## Username and password not used for now        
#    # user name must be unique
#    uName = request.form['userName']
#    if uName == "None":
#        uName = ""
#    else :
#        cur = User.query.filter(str(User.userName).upper() == request.form['userName'].upper(), User.ID != request.form['ID']).count()
#        if cur > 0 :
#            goodForm = False
#            flash('That User Name is already in use')
#        
#    if request.form['password'] == '' and uName != '':
#        goodForm = False
#        flash('Password may not be blank if User Name is present')
    
    return goodForm
    
def setUserStatus(email):
    ## locate the user with this email and set some globals
    sessionTimeout = 1200 #20 minutes
    if session.get('timeout') and session.get('timeout') < time():
        ## log the user out
        session.clear()
        flash("Your session has timed out. Please sign in again.")
        return False
        
    rec = User.query.filter(User.email == email).first()
    if rec:
        g.user = rec.email
        g.role = rec.role
        g.orgID = rec.organization_ID
        if g.role == "super" and ('superOrgID' in session) :
            g.orgID = int(session.get('superOrgID'))
        
        session['timeout'] = time() + sessionTimeout
        return True
    else:
        session.clear()
        flash("That email address is not on file")
        return False
         
def orgSwitch(newOrg=None):
    # switch to another organization
    if g.role == 'super' and newOrg :
        session['superOrgID'] = newOrg
                     