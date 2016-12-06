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
        #recs = Trip.query.order_by(Trip.tripDate)
        
        # Jun 10, 2016 modified query to speed up map display
        # The order of the columns selected is critical to the html template
        sql = "select (select locationName from location where location.id = trip.location_ID)"
        sql += " ,(select latitude from location where location.id = trip.location_ID)"
        sql += " ,(select longitude from location where location.id = trip.location_ID)"
        sql += " ,sum(tripCount)"
        sql += " from Trip group by location_ID;"
        recs = db.engine.execute(sql).fetchall()
        
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
            
        markerData = ""
        queryData = ""
        
        if recs:
            markerData = {"markers":[]}
            for rec in recs:
                popup = render_template('map/locationListPopup.html', locationName=rec.locationName)
                popup = popup.replace('"','\\"') # to escape double quotes in html
                
                if rec.latitude.strip() != '' and rec.longitude.strip() !='':
                    marker = {"latitude": float(rec.latitude), "longitude": float(rec.longitude), \
                      "locationID": rec.ID, "locationName": rec.locationName, "popup": popup, "draggable": True, }
                    markerData["markers"].append(marker)
                else:
                    pass
                    
            markerData["cluster"] = True
         # would like to set cluster to false but makes map view not dragable for some reason
        # This seems to be a Safari(6.1.1) issue. Not tested on newer
        return render_template('map/JSONmap.html', markerData=markerData, queryData=queryData)
        
        

    else:
        flash(printException('Could not open Database',"info"))
        return redirect(url_for('home'))

@mod.route('/report/mapError', methods=['GET'])
@mod.route('/report/mapError/', methods=['GET'])
@mod.route('/report/mapError/<errorMessage>/', methods=['GET'])
def mapError(errorMessage=""):
    setExits()
    return render_template('map/mapError.html', errorMessage=errorMessage)
    