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
import sys

# create our little application :)
app = Flask(__name__, instance_relative_config=True)
app.config.from_object(configuration.Config)
app.config.from_pyfile('settings.conf', silent=True)

app.debug = app.config["DEBUG"]

# setup Flask-SQLAlchemy
from flask.ext.sqlalchemy import SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = app.config["DATABASE_URI"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Create a mailer obj
from flask_mail import Mail
mail = Mail(app)

## views modules need db from above
#import models #### don't import models here, do it in views
import views.index
from views.utils import db_init, printException
     
### Base Routes #########
 
@app.route('/')
def home():
    return views.index.home()
    
@app.route('/ping', methods=['GET'])
def ping():
    return "OK"
    

@app.before_request
def before_request():
    # layout.html looks for g.user so declare it early
    g.user = session.get('user')
    g.orgID = None
    g.role = None
    
    if not db:
        # really can't do anything with out a database, so just bail
        printException("Database not Available", "error")
        return render_template('errors/500.html'), 500
        
    freeDirectories = ("login","logout","count","static","ping","_auth","map",
            "report",) #first directory of request URL
    superUserDirectories = ("org","feature","trip","traveler","super",) #first directory of request URL
    rootURL = request.path.split("/")
    rootURL = rootURL[1]

    superRequired = rootURL in superUserDirectories
    noLoginRequired = rootURL in freeDirectories
    ### Otherwise, user must be an Org. admin
    
    if noLoginRequired:
        #No login required
        pass
    else:
        # login required
        if g.user is None and rootURL !="":
            # no email in session, can only see the home page
            return redirect(url_for('login.login'))
        
        ## email must be linked to a user
        if views.user.setUserStatus(g.user):
            # Session timeout is set in app.config["PERMANENT_SESSION_LIFETIME"]
            # g.email, g.role, & g.orgID will be set
            if g.role == "counter":
                ## Nothing for these users here...
                session.clear()
                g.user = None
                flash("You don't have access to the Administration web site.")
                return redirect(url_for("login.login"))
                
            g.organizationName = views.org.getName(g.orgID)
            if superRequired and g.role != "super":
                flash("Sorry, you don't have access for that feature.")
                return redirect(url_for("home"))
        else:
            # Not a valid email or session timed out, go to Home page...
            return views.index.home()
                
    ## otherwise, serve the requested page...
    
@app.teardown_request
def teardown_request(exception):
    if db:
        db.session.close()


@app.errorhandler(404)
def page_not_found(e):
    if not hasattr(g, 'user'):
        g.user = None # layout .html looks for g.user
        
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def db_error():
    if not hasattr(g, 'user'):
        g.user = None # layout .html looks for g.user
        
    return render_template('errors/500.html'), 404
    
### Blueprinted views ####
from views import login
app.register_blueprint(login.mod)
from views import user
app.register_blueprint(user.mod)
from views import org
app.register_blueprint(org.mod)
from views import feature
app.register_blueprint(feature.mod)
from views import count_event
app.register_blueprint(count_event.mod)
from views import traveler
app.register_blueprint(traveler.mod)
from views import assignment
app.register_blueprint(assignment.mod)
from views import count
app.register_blueprint(count.mod)
from views import persona
app.register_blueprint(persona.mod)
from views import location
app.register_blueprint(location.mod)
from views import trip
app.register_blueprint(trip.mod)
from views import mapping
app.register_blueprint(mapping.mod)
from views import report
app.register_blueprint(report.mod)


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
            printException("Not able to create database file.","error",e)
            sys.exit(0)
            
    if not db:
        printException("Database did not startup","error")
        sys.exit(0)
        
    print "Web Server Running"
    app.run()
    ##app.run('10.0.1.9',5000)
