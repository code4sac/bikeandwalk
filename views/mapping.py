## Map view of trips
from flask import g, redirect, url_for, \
     render_template, flash, Blueprint
from bikeandwalk import db
from models import Trip, Location
from views.utils import printException


mod = Blueprint('map', __name__)

def setExits():
    g.title = 'Trips Map'

@mod.route('/map', methods=['POST', 'GET'])
@mod.route('/map/', methods=['POST', 'GET'])
def display():
    setExits()
    if db :
        recs = Trip.query.order_by(Trip.tripDate)

        return render_template('map/map.html', recs=recs)

    else:
        flash(printException('Could not open Database',"info"))
        return redirect(url_for('home'))
        
@mod.route('/report/locationMap', methods=['POST', 'GET'])
@mod.route('/report/locationMap/', methods=['POST', 'GET'])
def location():
    setExits()
    g.title = 'All Locations'
    if db :
        if g.orgID:
            recs = Location.query.filter(Location.organization_ID == g.orgID)
        else:
            recs = Location.query.all()
        # would like to set cluster to false but makes map view not dragable for some reason
        # This seems to be a Safari(6.1.1) issue. Not tested on newer
        return render_template('map/map.html', recs=recs, cluster = 'true')

    else:
        flash(printException('Could not open Database',"info"))
        return redirect(url_for('home'))
