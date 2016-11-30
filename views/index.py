from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash
from bikeandwalk import db
from models import Organization


def home():
    orgs = None
    if g.role == 'super':
        orgs = Organization.query.order_by(Organization.name)
    
    return render_template('index.html', orgs=orgs)

