## Map view of trips
from flask import g, redirect, url_for, \
     render_template, flash, Blueprint
from bikeandwalk import db
from models import Trip, Location
from views.utils import printException
from collections import namedtuple


mod = Blueprint('map', __name__)

def setExits():
    g.title = 'Trips Map'

@mod.route('/map', methods=['POST', 'GET'])
@mod.route('/map/', methods=['POST', 'GET'])
def display():
    # Display the Trips map
    setExits()
    if db :
        
        # Jun 10, 2016 modified query to speed up map display
        # The order of the selected fields is critical to creating a proper namedtuple below
        sql = "select (select locationName from location where location.id = trip.location_ID)"
        sql += " ,trip.location_ID"
        sql += " ,(select latitude from location where location.id = trip.location_ID)"
        sql += " ,(select longitude from location where location.id = trip.location_ID)"
        sql += " ,sum(tripCount)"
        sql += " from Trip group by location_ID;"
        recs = db.engine.execute(sql).fetchall()
        
        markerData = {}
        queryData = {"orgs":[{"name":"Another Org","ID":2},{"name":"SABA","ID":1},]}
        
        if recs:
            markerData = {"markers":[]}
            for rec in recs:
                #db.engine.execute returns a list of sets without column names
                #namedtuple creates an object that makeBasicMarker can access with dot notation
                Fields = namedtuple('record', 'locationName ID latitude longitude tripCount')
                record = Fields(rec[0], rec[1], rec[2], rec[3], rec[4])
                
                marker = makeBasicMarker(record) # returns a dict or None
                if marker:
                    popup = render_template('map/tripCountMapPopup.html', rec=record)
                    popup = escapeTemplateForJson(popup)
                    marker['popup'] = popup
                    
                    markerData["markers"].append(marker)
                    
        markerData["cluster"] = True
        markerData["zoomToFit"] = True
        
        return render_template('map/JSONmap.html', markerData=markerData, queryData=queryData)

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
            
        markerData = {}
        queryData = {}
        
        if recs:
            markerData = {"markers":[]}

            for rec in recs:
                marker = makeBasicMarker(rec) # returns a dict or None
                
                if marker:
                    popup = render_template('map/locationListPopup.html', rec=rec)
                    popup = escapeTemplateForJson(popup)
                    marker['popup'] = popup
                    
                    markerData["markers"].append(marker)
                    
        markerData["cluster"] = True
        markerData["zoomToFit"] = True
            
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
    
    
def escapeTemplateForJson(popup):
    # json doesn't like some characters rendered from the template
    if type(popup) != str and type(popup) != unicode:
        popup = ''
    popup = popup.replace('"','\\"') # to escape double quotes in html
    popup = popup.replace('\r',' ') # replace any carriage returns with space
    popup = popup.replace('\n',' ') # replace any new lines with space
    
    return popup
    
def makeBasicMarker(rec):
    if rec and rec.latitude.strip() != '' and rec.longitude.strip() !='':
        marker = {"latitude": float(rec.latitude), "longitude": float(rec.longitude), \
           "locationID": rec.ID, "locationName": rec.locationName, "draggable": False, }
        return marker
    return None
    
    
    