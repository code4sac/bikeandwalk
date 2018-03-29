from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint
from time import time
import re
from bikeandwalk import db,app
from models import User, Organization, UserOrganization
from views.utils import printException, cleanRecordID, getOrgUsers, getUserOrgs
import hmac
import hashlib
import random
from sqlalchemy import func
#from views.login import setUserSession #user imported in login
import views.login

mod = Blueprint('user',__name__)

def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.delete')
    g.title = 'User'

@mod.route('/user/')
def display():
    setExits()
    if db :
        recs = getOrgUsers(g.orgID)
        return render_template('user/user_list.html', recs=recs)

    flash('Could not open Database')
    return redirect(url_for('index'))
    
# Edit the user
@mod.route('/user/edit', methods=['POST', 'GET'])
@mod.route('/user/edit/', methods=['POST', 'GET'])
@mod.route('/user/edit/<id>/', methods=['POST', 'GET'])
def edit(id=0):
    #printException(str(request.form)) 
    
    setExits()
    id = cleanRecordID(id)
    orgs = Organization.query.order_by(Organization.name)
    u = getUserOrgs(id)
    selectedOrgs = []
    for s in u:
        selectedOrgs.append(s.ID)
    
    if id < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
            
    rec = None
    
    if not request.form:
        """ if no form object, send the form page """
        # get the user record if you can
        currentPassword = ""
        if id > 0:
            rec = User.query.get(id)
            currentPassword = rec.password
                
        
    else:
        #have the request form
        #ensure a value for the check box
        inactive = request.form.get('inactive')
        if not inactive: 
            inactive = "0"
        

        if validForm():
            if id > 0:
                rec = User.query.get(id)
            else:
                ## create a new record stub
                rec = User(request.form['name'],request.form['email'])
                db.session.add(rec)
                #db.session.commit() # this loads the new ID into rec
                
                rec.userName = db.null()
                rec.password = db.null()
        
            #Are we editing the current user's record?
            editingCurrentUser = ''
            if(g.user == rec.userName):
                editingCurrentUser = request.form['userName'].strip()
            else: 
                if(g.user == rec.email):
                    editingCurrentUser = request.form['email'].strip()
            
            #update the record
            rec.name = request.form['name'].strip()
            rec.email = request.form['email'].strip()
            rec.role = request.form['role'].strip()
            rec.inactive = str(inactive)
            
            user_name = ''
            if request.form['userName']:
                user_name = request.form['userName'].strip()
            
            if user_name != '':
                rec.userName = user_name
            else:
                rec.userName = db.null()
        
            # Null values in db are returned as None
            if str(rec.password) != 'NULL' and request.form['password'].strip() == '':
                # Don't change the password
                pass
            else:
                user_password = ''
                if request.form['password'].strip() != '':
                    user_password = getPasswordHash(request.form['password'].strip())

                if user_password != '':
                    rec.password = user_password
                else:
                    rec.password = db.null()
    
            try:
                db.session.commit()
                # create user_organization records
                # in the case of a new user, rec.ID is now available
                orgIDs = request.form.getlist("orgs")
                if not orgIDs:
                    orgIDs = [request.form.get('org')]
                makeUserOrgRecords(rec.ID,orgIDs)
                db.session.commit()
                
                # if the username or email address are the same as g.user
                # update g.user if it changes
                if(editingCurrentUser != ''):
                    setUserStatus(editingCurrentUser)
                    views.login.setUserSession(editingCurrentUser)
                
            
           
                
            except Exception as e:
                db.session.rollback()
                flash(printException('Error attempting to save '+g.title+' record.',"error",e))
            
            return redirect(g.listURL)
        
        else:
            # form did not validate, giv user the option to keep their old password if there was one
            currentPassword = ""
            if request.form["password"] != "" and id > 0:
                rec = User.query.get(id)
                currentPassword = rec.password
            rec=request.form

    # so the checkbox will be set on new record form
    if len(selectedOrgs) == 0:
        selectedOrgs.append(g.orgID)
            
    # display form
    return render_template('user/user_edit.html', rec=rec, currentPassword=currentPassword, orgs=orgs, selectedOrgs=selectedOrgs)
    

@mod.route('/user/delete', methods=['GET'])
@mod.route('/user/delete/', methods=['GET'])
@mod.route('/user/delete/<id>/', methods=['GET'])
def delete(id=0):
    setExits()
    id = cleanRecordID(id)
    if id < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
    
    if id > 0:
        rec = User.query.get(id)
        if rec:
            try:
                db.session.delete(rec)
                db.session.commit()
            except Exception as e:
                flash(printException('Error attempting to delete '+g.title+' record.',"error",e))
        else:
            flash("Record could not be deleted.")
            
    return redirect(g.listURL)
    

@mod.route('/orgSwitch/<newOrg>/', methods=['GET'])
def orgSwitch(newOrg=None):
    # switch to another organization
    if g.role == 'super' and newOrg :
        session['superOrgID'] = newOrg

    return redirect(url_for('home'))        

        
def validForm():
    # Validate the form
    goodForm = True
    
    #must have at least one organization selected
    if not request.form.getlist('orgs') and not request.form['org']:
        goodForm = False
        flash("You must select at least one organization")
    
    if request.form['name'].strip() == '':
        goodForm = False
        flash('Name may not be blank')

    if request.form['email'].strip() == '':
        goodForm = False
        flash('Email may not be blank')

    if request.form['email'] != '':
        cur = User.query.filter(func.lower(User.email) == request.form['email'].strip().lower(), User.ID != request.form['ID']).count()
        if cur == 0:
            # be sure that no other user has this email as their userName. Very unlikely...
            cur = User.query.filter(func.lower(User.userName) == request.form['email'].strip().lower(), User.ID != request.form['ID']).count()

        if cur > 0 :
            goodForm = False
            flash('That email address is already in use')
        #test the format of the email address (has @ and . after @)
        elif not looksLikeEmailAddress(request.form['email']):
            goodForm = False
            flash('That doesn\'t look like a valid email address')
            
    # user name must be unique
    uName = request.form['userName'].strip()
    if uName == "None":
        uName = ""
    else :
        cur = User.query.filter(func.lower(User.userName) == request.form['userName'].strip().lower(), User.ID != request.form['ID']).count()
        if cur == 0:
            # be sure no one else has this email address as their userName... Unlikely, I know.
            cur = User.query.filter(func.lower(User.email) == request.form['userName'].strip().lower(), User.ID != request.form['ID']).count()
            
        if cur > 0 :
            goodForm = False
            flash('That User Name is already in use')
        
    passwordIsSet = ((User.query.filter(User.password != db.null(), User.ID == request.form['ID']).count()) > 0)
    
    if request.form["userName"].strip() != '' and request.form["password"].strip() == '' and not passwordIsSet:
        goodForm = False
        flash('There must be a password if there is a User Name')
        
    if len(request.form["password"].strip()) == 0 and len(request.form["password"]) != 0 and passwordIsSet:
        goodForm = False
        flash('You can\'t enter a blank password.')
    
    #passwords must match if present
    if request.form['password'].strip() != '' and request.form['confirmPassword'].strip() != request.form['password'].strip():
        goodForm = False
        flash('Passwords don\'t match.')
        
    return goodForm
    
def findUser(emailOrUserName=None,includeInactive=False):
    if emailOrUserName == None:
        return None
        
    emailOrUserName = emailOrUserName.strip().lower()
    ## locate the user with this as their email or userName
    sql = "SELECT user.*, user_organization.organization_ID FROM user join user_organization WHERE lower(user.email) = '%s' OR lower(user.userName) = '%s'"
    #sql = "SELECT * FROM user WHERE  lower(user.email) = '%s' OR lower(user.userName) = '%s'"
    sql = sql % (emailOrUserName, emailOrUserName)
    
    #Filter inactive if needed
    if not includeInactive:
        #Active user only
        sql = sql + " AND user.inactive = '0'"
    
    sql = sql + " LIMIT 1 ;"
    
    rec = db.engine.execute(sql).fetchone()
    if rec:
        return rec
        
    return None
    
def setUserStatus(emailOrUserName):
    if emailOrUserName == None:
        return False
    emailOrUserName = emailOrUserName.strip()
    rec = findUser(emailOrUserName)
    if rec:
        g.user = emailOrUserName
        g.role = rec.role
        g.orgID = rec.organization_ID
        
        if g.role == "super" and ('superOrgID' in session) :
            ## super user is managing another organization's data
            if 'superOrgID' in session:
                g.orgID = int(session.get('superOrgID'))
        
        return True
    else:
        flash("User is not on file")
        return False
            
def getPasswordHash(pw, theSalt=None, timesAround='05'):
    if type(pw) is str or type(pw) is unicode:
        pw = pw.strip()
        if not theSalt:
            theSalt = getPasswordSalt()
        codeWord = str(pw) + theSalt
        
        for i in range(int(timesAround) * 1000):
            codeWord = hmac.new(app.config["SECRET_KEY"], str(codeWord), hashlib.sha256).hexdigest() 
        return theSalt +'.'+timesAround+'.'+codeWord
    return "" #test this for error
    
def getPasswordSalt():
    theChars = '0123456789abcdef'
    s = random.sample(theChars,16)
    salt = ''
    for i in range(len(s)):
        salt = salt + s[i]
        
    return salt
    
def matchPasswordToHash(pw,passHash):
    if pw and passHash:
        s = passHash.split('.')
        if len(s) != 3:
            return False
        salt = s[0]
        timesAround = s[1]
        hashToTest = getPasswordHash(pw,salt,timesAround)
        if hashToTest == passHash:
            return True
        
    return False
    
def getUserPasswordHash(emailOrUserName=''):
    includeInactive = True
    rec = findUser(emailOrUserName.strip(),includeInactive)
    if rec:
        return rec.password
        
    return ""
    
def looksLikeEmailAddress(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email.strip())
    
def makeUserOrgRecords(userID,orgIDs):
    """ create user_organization records for a user """
    # orgIDs is a list, usually strings
    
    #first delete any current records
    sql = "delete from user_organization where user_ID = '%s';" % (str(userID))
    db.engine.execute(sql)
    
    #db.session.commit()
    
    recs=getUserOrgs(id)
    for orgID in orgIDs:
        rec = UserOrganization(cleanRecordID(userID),cleanRecordID(orgID))
        db.session.add(rec)
        
    
    