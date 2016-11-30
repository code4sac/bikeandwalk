from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint
from bikeandwalk import db,app
from models import User
from views.utils import printException, cleanRecordID
from views.user import matchPasswordToHash, looksLikeEmailAddress, setUserStatus, getUserPasswordHash
from time import sleep


mod = Blueprint('login',__name__)

def setExits():
    g.title = 'Login'

@mod.route('/login', methods=['GET', 'POST'])
@mod.route('/login/', methods=['GET', 'POST'])
def login():
    setExits()
    if g.user and g.user != None:
        flash("Already Logged in...")
        return redirect(url_for("home"))
       
    if request.form:
            
        if validateUser(request.form["password"],request.form["userNameOrEmail"]):
            session["user"] = request.form["userNameOrEmail"].strip()
            return redirect(url_for("home"))
        else:
            flash("Invalid User Name or Password")
        
    #remember howmany times the user has tried to log in
    if 'loginTries' not in session:
        session['loginTries'] = 0
    session['loginTries'] = session['loginTries'] + 1
    #slow down login attempts
    if session['loginTries'] > 5:
        sleep(session['loginTries']/.8)
        
    return render_template('login/user_login.html', form=request.form)
       
def validateUser(password,userNameOrEmail):
    if password and userNameOrEmail: 
        password = password.strip()
        userNameOrEmail = userNameOrEmail.strip()
        #Check for a password match
        passHash = getUserPasswordHash(userNameOrEmail)
        if passHash != '':
            if matchPasswordToHash(password,passHash):
                return setUserStatus(userNameOrEmail)
            
            
    return False
    
    
@mod.route('/logout', methods=['GET'])
@mod.route('/logout/', methods=['GET'])
def logout():
    session.clear()
    g.user = None
    flash("Successfully Logged Out")
    return redirect(url_for("home"))
    
