# -*- coding: utf-8 -*-
"""
    Bike and Walk app
    ~~~~~~

    A bike and pedestrian counting project using
    Flask and sqlite3.

    Started Nov. 18, 2015 - Bill Leddy
    
    :Flask copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, _app_ctx_stack, json
from datetime import datetime
import logging
import configuration
import requests

from setup import init_site_settings
init_site_settings() #this has to be done before creating app

# create our little application :)
app = Flask(__name__, instance_relative_config=True)
app.config.from_object(configuration.Config)
app.config.from_pyfile('settings.conf', silent=True)

# setup Flask-SQLAlchemy
from flask.ext.sqlalchemy import SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = app.config["DATABASE_URI"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


## views modules need db from above
#import models #### don't import models here, do it in views
import views.index
import views.user
import views.org
import views.feature
import views.count_event
import views.traveler
import views.count
import views.countingLocation
import views.db

## custom template filters
@app.template_filter()
def eventListFormat(value=datetime.now().isoformat(),format='%d-%m-%Y / %I:%M %p'):
#    return value.strftime(value,format)
     pass
     
### Generic Routes #########
 
@app.route('/')
def home():
    return views.index.home()
    
@app.route('/orgSwitch/<org>/', methods=['GET'])
def switchOrg(org):
    views.user.orgSwitch(org)
    return redirect(url_for('home'))

@app.route('/ping', methods=['GET'])
def ping():
    return "OK"
    
@app.route('/login', methods=['GET'])
def login():
    return views.index.login()
         
## User Routes ######
       
@app.route('/users/')
@app.route('/user/')
def user_list():
    return views.user.user_list()

@app.route('/user/edit', methods=['POST', 'GET'])
@app.route('/user/edit/', methods=['POST', 'GET'])
@app.route('/user/edit/<id>/', methods=['POST', 'GET'])
def user_edit(id=0):
    #checkLoggedin()
    return views.user.user_edit(id)
    
@app.route('/user/delete', methods=['GET'])
@app.route('/user/delete/', methods=['GET'])
@app.route('/user/delete/<id>/', methods=['GET'])
def user_delete(id=0):
    return views.user.user_delete(id)
    
## Org Routes ######
       
@app.route('/org')
def org_list():
    return views.org.org_list()

@app.route('/org/edit', methods=['POST', 'GET'])
@app.route('/org/edit/', methods=['POST', 'GET'])
@app.route('/org/edit/<id>/', methods=['POST', 'GET'])
def org_edit(id=0):
    #checkLoggedin()
    return views.org.org_edit(id)
    
@app.route('/org/delete', methods=['GET'])
@app.route('/org/delete/', methods=['GET'])
@app.route('/org/delete/<id>/', methods=['GET'])
def org_delete(id=0):
    return views.org.org_delete(id)
    
## Feature Routes ######
       
@app.route('/features')
@app.route('/feature')
def feature_list():
    return views.feature.feature_list()

@app.route('/feature/edit', methods=['POST', 'GET'])
@app.route('/feature/edit/', methods=['POST', 'GET'])
@app.route('/feature/edit/<id>/', methods=['POST', 'GET'])
def feature_edit(id=0):
    #checkLoggedin()
    return views.feature.feature_edit(id)
    
@app.route('/feature/delete', methods=['GET'])
@app.route('/feature/delete/', methods=['GET'])
@app.route('/feature/delete/<id>/', methods=['GET'])
def feature_delete(id=0):
    return views.feature.feature_delete(id)
    
## CountEvent Routes ######

@app.route('/event/')
def count_event_list():
    return views.count_event.count_event_list()

@app.route('/event/edit', methods=['POST', 'GET'])
@app.route('/event/edit/', methods=['POST', 'GET'])
@app.route('/event/edit/<id>/', methods=['POST', 'GET'])
def count_event_edit(id=0):
    #checkLoggedin()
    return views.count_event.count_event_edit(id)

@app.route('/event/delete', methods=['GET'])
@app.route('/event/delete/', methods=['GET'])
@app.route('/event/delete/<id>/', methods=['GET'])
def count_event_delete(id=0):
    return views.count_event.count_event_delete(id)
    
## Traveler Routes ######

@app.route('/traveler/')
def traveler_list():
    return views.traveler.traveler_list()

@app.route('/traveler/edit', methods=['POST', 'GET'])
@app.route('/traveler/edit/', methods=['POST', 'GET'])
@app.route('/traveler/edit/<id>/', methods=['POST', 'GET'])
def traveler_edit(id=0):
    return views.traveler.traveler_edit(id)

@app.route('/traveler/delete/', methods=['GET'])
@app.route('/traveler/delete/<id>/', methods=['GET'])
def traveler_delete(id=0):
    return views.traveler.traveler_delete(id)

@app.route('/traveler/select/', methods=['GET'])
@app.route('/traveler/select/<id>/', methods=['GET'])
def traveler_select(id=0):
    return "Traveler Select goes here!"
    
#### CountingLocation routes #####

@app.route('/countinglocation/')
def countingLocation_list():
    return views.countingLocation.countingLocation_list()

@app.route('/countinglocation/edit', methods=['POST', 'GET'])
@app.route('/countinglocation/edit/', methods=['POST', 'GET'])
@app.route('/countinglocation/edit/<id>/', methods=['POST', 'GET'])
def countingLocation_edit(id=0):
    return views.countingLocation.countingLocation_edit(id)

@app.route('/countinglocation/delete/', methods=['GET'])
@app.route('/countinglocation/delete/<id>/', methods=['GET'])
def countingLocation_delete(id=0):
    return views.countingLocation.countingLocation_delete(id)


#### The Count pages ###

@app.route('/count', methods=['POST', 'GET'])
@app.route('/count/', methods=['POST', 'GET'])
@app.route('/count/<UID>', methods=['POST', 'GET'])
@app.route('/count/<UID>/', methods=['POST', 'GET'])
def count_begin(UID=""):
    return views.count.count_begin(UID)
    
@app.route('/count/trip', methods=['POST', 'GET'])
@app.route('/count/trip/', methods=['POST', 'GET'])
def count_trip():
    return views.count.count_trip()
    
## database connection ##
def init_db():
    sample = None
    if app.debug:
        sample = ''
    
    views.db.db_init()
    
#    """Creates the database tables."""
#    with app.app_context():
#        db = get_db()
#        with app.open_resource('db/CreateTables2.sql', mode='r') as f:
#            db.cursor().executescript(f.read())
#        db.commit()
#        with app.open_resource('db/insertTestData2.sql', mode='r') as f:
#            db.cursor().executescript(f.read())
#        db.commit()
        
#def get_db():
#    """Opens a new database connection if there is none yet for the
#    current application context.
#    """
#    top = _app_ctx_stack.top
#    if not hasattr(top, 'sqlite_db'):
#        sqlite_db = sqlite3.connect(app.config['DATABASE'])
#        sqlite_db.row_factory = sqlite3.Row
#        top.sqlite_db = sqlite_db
#
#    return top.sqlite_db

@app.before_request
def before_request():
    freeDirectories = ("login","count","static","ping","_auth",) #first directory of request URL
    rootURL = request.path.split("/")
    rootURL = rootURL[1]
    g.role = None
    g.orgID = None
    g.user = session.get('email')
    
    if rootURL == "login" and g.user != None:
        # usually this is the refresh after the persona validation
        return redirect(url_for('home'))
    elif rootURL in freeDirectories:
        #No login required
        pass
    else:
        # login required
        if g.user is not None:
            ## email must be linked to a user
            if views.user.setUserStatus(g.user):
                # Session timeout is set in app.config["PERMANENT_SESSION_LIFETIME"]
                # g.email, g.role, & g.orgID will be set
                g.organizationName = views.org.getName(g.orgID)
            else:
                # Not a valid email or session timed out, go to login page...
                return redirect(url_for('login'))
        else:
            # no email in session
            flash("You must log in to use this site")
            return redirect(url_for('login'))
                
    ## otherwise, serve the requested page...
    
@app.teardown_request
def teardown_request(exception):
#    db = getattr(g, 'db', None)
#    if db is not None:
#        db.close()
    pass


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

        
## persona authentication ##
@app.route('/_auth/login', methods=['GET', 'POST'])
def login_handler():
    """This is used by the persona.js file to kick off the
    verification securely from the server side.  If all is okay
    the email address is remembered on the server.
    """
    resp = requests.post(app.config['PERSONA_VERIFIER'], data={
        'assertion': request.form['assertion'],
        'audience': request.host_url,
    }, verify=True)
    if resp.ok:
        verification_data = json.loads(resp.content)
        if verification_data['status'] == 'okay':
            session['email'] = verification_data['email']
            logging.info(verification_data['email'])
            return 'OK'

    abort(400)

@app.route('/_auth/logout', methods=['POST'])
def logout_handler():
    """This is what persona.js will call to sign the user
    out again.
    """
    session.clear()
    return 'OK'

def checkLoggedin():
    """ bail if the user is not logged in """
    if not g.user:
        abort(401)
    else:
        return

def startLogging():
        logging.basicConfig(filename='bikeandwalk.log', level=logging.DEBUG)
        logging.info('Logging Started : ' + datetime.now().isoformat())
        
   
if __name__ == '__main__':
    """ Test to see if database file exists.
        if not, create it with init_db()
    """
    ## Turn on logging:
    startLogging()
    try:
        f=open(app.config["DATABASE"],'r')
        f.close()
    except IOError as e:
        try:
            init_db()
        except Exception as e:
            print "Not able to create database file."
            print "Error: " + str(e)
            import sys
            sys.exit(0)

    print "Web Server Running"
    app.run()
    ##app.run('10.0.1.9',5000)
