## Map view of trips
from flask import g, redirect, url_for, \
     render_template, flash, Blueprint, request, make_response, abort
from bikeandwalk import db, app
from models import Trip, Location, Organization, CountEvent, Traveler, TravelerFeature, Feature
from views.utils import printException
from collections import namedtuple
import json
from datetime import datetime

mod = Blueprint('map', __name__)

def setExits():
    g.title = 'Trips Map'
    g.listURL = url_for('.display')
    g.exportURL = url_for('.export')
    
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
                
        ### TODO - remove any ID's from mapEvents that don't belong to a selected org in mapOrgs
        ###    if none of the events belong to a selected org, set the mapEvents to ['0']
        
        queryData = {}
        queryData["mapOrgs"] = mapOrgs
        queryData["mapEvents"] = mapEvents
        
        #Get all orgs
        queryData["orgs"] = []
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
        
        recs = queryTripData(mapOrgs, mapEvents, 'summary')
        
        markerData = {"markers":[]}
        markerData["cluster"] = True
        markerData["zoomToFit"] = False # can/t zoom if there are no markers.
        if recs:
            markerData["zoomToFit"] = True
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
    
@mod.route('/report/map/export/', methods=['post'])
def export():
    """ Export some data"""
    K = []
    F = {}
    if request.form:
        F = request.form
        K = F.keys()
        
    # convert queryData from json
    if 'queryData' in K:
        data = request.form['queryData']
        try:
            data = json.loads(request.form['queryData'])
        except Exception as e:
            printException('Bad JSON data in post',"error",e)
            printException("json = " + request.data,"info")
            abort(500)
            
    exportStyle = 'summary'
    if 'exportStyle' in K:
        exportStyle = F['exportStyle']
        
    # perform query
    recs = None
    if 'mapOrgs' in data.keys() and 'mapEvents' in data.keys():
        recs = queryTripData(data['mapOrgs'], data['mapEvents'], exportStyle)
        
    #print recs
    csv = "Error occured while creating Export\n"
    if app.debug:
        if 'queryData' in K:
            csv += "queryData: %s" % F['queryData']
        else:
            csv += "No queryData in form"
    
    if recs:
    # the columns output are:
    #   Location Name, Location ID, Latitude, Longitude, sum(tripCount), tripCount, 
    #      tripDate, Event Start, Event End, Turn direction, Traveler name
        csv = ""
        for rec in recs:
            row = ""
            if exportStyle == "summary":
                headers = "Location Name,Latitude,Longitude,Trip Count,Event Start,Event End\n"
                row = "\"%s\",\"%s\",\"%s\",%d,\"%s\",\"%s\"\n" % (rec[0], rec[2], rec[3], rec[4], rec[7], rec[8] )
            if exportStyle == "detail":
                headers = "Location Name,Latitude,Longitude,Trip Count,Trip Date,Event Start,Event End,Turn,Traveler\n"
                row = "\"%s\",\"%s\",\"%s\",%d,\"%s\",\"%s\",\"%s\",\"%s\",\"%s\"\n" % (rec[0], rec[2], rec[3], rec[5], rec[6], rec[7], rec[8], rec[9], rec[10])
            if exportStyle == "nbpd":
                headers = "NBPD Report not available yet"
                row = ""
                
            csv += row
            
        csv = headers + csv
   
    response = make_response(csv)
    now = datetime.now()
    cd = "attachment; filename=BAW_%s_export_%d%d%d.csv" % (exportStyle, now.hour, now.minute, now.second)
    
    response.headers['Content-Disposition'] = cd 
    response.mimetype='text/csv'
    
    return response
        

    
def queryTripData(mapOrgs, mapEvents, exportStyle='summary'):
    
    # Jun 10, 2016 modified query to speed up map display
    # The order of the selected fields is critical to creating a proper namedtuple below
    
    # the columns output are:
    #   Location Name, Location ID, Latitude, Longitude, sum(tripCount), tripCount, 
    #      tripDate, Event Start, Event End, Turn direction, Traveler name
    
    sql = "Select "
    sql += "location.locationName as 'Location', "
    sql += "location.ID as 'Location ID', "
    sql += "location.latitude as 'lat', "
    sql += "location.longitude as 'lng', "
    sql += "sum(tripCount), "
    ## fields above are used for map display
    sql += "tripCount, "
    sql += "tripDate, "
    sql += "strftime('%Y-%m-%d %H:%M', count_event.startDate) as 'Count Start', "
    sql += "strftime('%Y-%m-%d %H:%M', count_event.endDate) as 'Count End', "
    sql += "trip.turnDirection as 'Turn', "
    sql += "traveler.name as 'Traveler' "
    
    sql += "from trip JOIN location, organization, count_event, traveler "
    
    sql += "Where "

    orgIDs = ""
    if mapOrgs and '0' not in mapOrgs:
        for i in mapOrgs:
            if i.isdigit():
                orgIDs += i + ","
                
        if len(orgIDs) > 0:
            orgIDs = orgIDs[0:-1] # remove trailing comma
            sql += "(organization.ID in ( %s)) " % (orgIDs)
            
    eventIDs = ""
    if mapEvents and '0' not in mapEvents:
        for i in mapEvents:
            if i.isdigit():
                eventIDs += i + ","
                
        if len(eventIDs) > 0:
            eventIDs = eventIDs[0:-1] # remove trailing comma
            if len(orgIDs) >0:
                sql += " and "
            sql += "(count_event.ID in (%s)) " % (eventIDs)
            
    if len(orgIDs+eventIDs) > 0:
        sql += " and "
        
        
    sql += "trip.countEvent_ID = count_event.ID and "
    sql += "trip.location_ID = location.ID and "
    sql += "trip.traveler_ID = traveler.ID and "
    sql += "count_event.organization_ID = organization.ID "
    if exportStyle == "summary":
        sql += "Group by location.ID "
        sql += "Order by location.locationName"
        
    else:
        #Detail
        sql += "Group by trip.turnDirection, traveler.ID, location.locationName "
        sql += "Order by organization.name, count_event.startDate, location.locationName, trip.turnDirection, traveler.name"
        
    #print sql
    
    return db.engine.execute(sql).fetchall()
    
    
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
    
    