## Map view of trips
from flask import g, redirect, url_for, \
     render_template, flash, Blueprint, request
from bikeandwalk import db
from models import Trip, Location, Organization, CountEvent, Traveler, TravelerFeature, Feature
from views.utils import printException
from collections import namedtuple


mod = Blueprint('map', __name__)

def setExits():
    g.title = 'Trips Map'
    g.listURL = url_for('.display')
    
@mod.route('/map', methods=['POST', 'GET'])
@mod.route('/map/', methods=['POST', 'GET'])
def display():
    # Display the Trips map
    setExits()
    if db :
        mapOrgs = ['0']
        if request.form and 'mapOrgs' in request.form.keys():
            mapOrgs = request.form.getlist('mapOrgs')
            if '0' in mapOrgs:
                # if 'ALL' is selected just show all
                mapOrgs = ['0']
                
        mapEvents = ['0']
        if request.form and 'mapEvents' in request.form.keys():
            mapEvents = request.form.getlist('mapEvents')
            if '0' in mapEvents:
                # if 'ALL' is selected just show all
                mapEvents = ['0']
                
        #Get all orgs
        queryData = {"orgs":[]}
        sql = "select * from organization where 1=1 "
        sql += " order by 'name'"
            
        orgs = db.engine.execute(sql).fetchall()
        
        if orgs:
            for org in orgs:
                d = {'name':org.name, 'ID':str(org.ID)}
                queryData['orgs'].append(d)
                
        # get the events
        sql = "select * from count_event "
        haswhere = False
        if mapOrgs and len(mapOrgs) > 0 and '0' not in mapOrgs:
            for i in range(len(mapOrgs)):
                if i != '0' and mapOrgs[i].isdigit():
                    if not haswhere:
                        sql += " where count_event.organization_ID in ("
                        haswhere=True
                    sql += "%s" % (mapOrgs[i])
                    if i < len(mapOrgs) -1 and mapOrgs[i+1].isdigit():
                        sql +=","
            if haswhere:
                sql += ")"
                
        sql += " order by startDate desc"

        events = db.engine.execute(sql).fetchall()
        queryData['events'] = []
        if events:
            for event in events:
                d = {'name':event.title, 'ID':str(event.ID)}
                queryData['events'].append(d)
        
        # Jun 10, 2016 modified query to speed up map display
        # The order of the selected fields is critical to creating a proper namedtuple below
        sql = "select (select locationName from location where location.id = trip.location_ID)"
        sql += " ,trip.location_ID"
        sql += " ,(select latitude from location where location.id = trip.location_ID)"
        sql += " ,(select longitude from location where location.id = trip.location_ID)"
        sql += " ,sum(tripCount)"
        sql += " from Trip "
        haswhere = False
        if mapOrgs and '0' not in mapOrgs:
            for i in range(len(mapOrgs)):
                if mapOrgs[i].isdigit():
                    if not haswhere:
                        sql += " where ("
                        haswhere = True
                    sql += " trip.countEvent_ID in (select ID from count_event where organization_ID = %s) " % (mapOrgs[i])
                    if i < len(mapOrgs) - 1 and mapOrgs[i+1].isdigit():
                        sql += " or "
            if haswhere:
                sql += ") "
                
        if mapEvents and '0' not in mapEvents:
            for i in range(len(mapEvents)):
                if mapEvents[i].isdigit():
                    if not haswhere:
                        sql += " where ("
                        haswhere = True
                    else:
                        sql += " and ("
                    sql += " trip.countEvent_ID = %s " % (mapEvents[i])
                    if i < len(mapEvents) - 1  and mapEvents[i+1].isdigit():
                        sql += " or "
            if haswhere:
                sql += ") "
            
        sql += " group by location_ID "
        
        recs = db.engine.execute(sql).fetchall()
        
        markerData = None
        
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
        
        return render_template('map/JSONmap.html', markerData=markerData, queryData=queryData, mapOrgs=mapOrgs, mapEvents=mapEvents)

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
    
    
    