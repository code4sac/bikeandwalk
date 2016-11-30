from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint
from time import time
import re
from bikeandwalk import db,app
from models import User
from views.utils import printException, cleanRecordID
import hmac
import hashlib
import random
from sqlalchemy import func

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
        recs = User.query.filter(User.organization_ID == int(g.orgID)).order_by(User.name)
        return render_template('user/user_list.html', recs=recs)

    flash('Could not open Database')
    return redirect(url_for('index'))
    
# Edit the user
@mod.route('/user/edit', methods=['POST', 'GET'])
@mod.route('/user/edit/', methods=['POST', 'GET'])
@mod.route('/user/edit/<id>/', methods=['POST', 'GET'])
def edit(id=0):
    setExits()
    id = cleanRecordID(id)
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
            
        return render_template('user/user_edit.html', rec=rec, currentPassword=currentPassword)
            
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
            rec = User(request.form['name'],request.form['email'],request.form['organization_ID'])
            db.session.add(rec)
            rec.userName = db.null()
            
        #update the record
        rec.name = request.form['name'].strip()
        rec.email = request.form['email'].strip()
        rec.role = request.form['role'].strip()
        rec.inactive = str(inactive)
        rec.organization_ID = request.form['organization_ID']
                
        ### for now the username and password are not used
        user_name = ''
        if request.form['userName']:
            user_name = (request.form['userName']).strip()
            
        if user_name != '':
            rec.userName = user_name
        else:
            rec.userName = db.null()

        user_password = ''
        if request.form['password']:
            user_password = getPasswordHash(request.form['password'].strip())

        if user_password != '':
            rec.password = user_password
            
        try:
            db.session.commit()
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
        

    # form not valid - redisplay
    return render_template('user/user_edit.html', rec=request.form, currentPassword=currentPassword)


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
    
        
def validForm():
    # Validate the form
    global uName, inactive
    goodForm = True
    
    if request.form['name'].strip() == '':
        goodForm = False
        flash('Name may not be blank')

    if request.form['email'].strip() == '':
        goodForm = False
        flash('Email may not be blank')

    if request.form['email'] != '':
        cur = User.query.filter(func.lower(User.email) == request.form['email'].strip().lower(), User.ID != request.form['ID']).count()
        if cur > 0 :
            goodForm = False
            flash('That email address is already in use')
        #test the format of the email address (has @ and . after @)
        elif not looksLikeEmailAddress(request.form['email']):
            goodForm = False
            flash('That doesn\'t look like a valid email address')
            
    if request.form['organization_ID'] <= "0":
        goodForm = False
        flash('You must select an Organization')

    # user name must be unique
    uName = request.form['userName'].strip()
    if uName == "None":
        uName = ""
    else :
        cur = User.query.filter(func.lower(User.userName) == request.form['userName'].strip().lower(), User.ID != request.form['ID']).count()
        if cur > 0 :
            goodForm = False
            flash('That User Name is already in use')
        
    #passwords must match if present
    if request.form['password'].strip() != '' and request.form['confirmPassword'].strip() != request.form['password'].strip():
        goodForm = False
        flash('Passwords don\'t match.')
        
    return goodForm
    
def findUser(emailOrUserName=None,includeInactive=False):
    if emailOrUserName == None:
        return None
        
    emailOrUserName = emailOrUserName.strip()
    sql = "SELECT * FROM User where "
    ## locate the user with this email and set some globals        
    if looksLikeEmailAddress(emailOrUserName):
        sql = sql + "lower(User.email) = '" + emailOrUserName.lower() + "' "
    else:
        sql = sql + "lower(User.userName) = '" + emailOrUserName.lower() + "' "

        #Filter inactive if needed
    if includeInactive:
        pass
    else:
        #Active user only
        sql = sql + " and User.inactive = '0'"
    
    sql = sql + " ;"

    rec = db.engine.execute(sql).fetchone()
    if rec:
        return rec
        
    return None
    
def setUserStatus(emailOrUserName):
    if emailOrUserName == None:
        return False
    emailOrUserName = emailOrUserName.strip()
    rec = findUser(emailOrUserName.strip())
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
        #session.clear()
        flash("User is not on file")
        return False
            

@mod.route('/orgSwitch/<newOrg>/', methods=['GET'])
def orgSwitch(newOrg=None):
    # switch to another organization
    if g.role == 'super' and newOrg :
        session['superOrgID'] = newOrg
        
    return redirect(url_for('home'))        
    
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
    