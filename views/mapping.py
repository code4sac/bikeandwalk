## Map view of trips
from flask import g, redirect, url_for, \
     render_template, flash, Blueprint
from bikeandwalk import db
from models import Trip
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
