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
        mapOrgs = []
        mapEvents = []
        getSearchFormSelectValues(mapOrgs,mapEvents) # all parameters must be empty lists
        
        queryData = {}
        queryData["mapOrgs"] = mapOrgs
        queryData["mapEvents"] = mapEvents
        queryData['mapType'] = 'trips'
        
        #Get all orgs
        getOrgs(queryData)

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
    g.title = 'Count Locations'
    
    if db :
        queryData = {}
        queryData['mapType'] = 'locations'

        #Get all orgs
        getOrgs(queryData)
        
        mapOrgs = []
        mapEvents = []
        if not request.form and g.orgID:
            queryData['mapOrgs'] = [str(g.orgID)]
        else:
            getSearchFormSelectValues(mapOrgs,mapEvents) # all parameters must be empty lists
            queryData['mapOrgs'] = mapOrgs #We don't need mapEvents for this map

        sql = "select locationName, ID, latitude, longitude from location "
        if '0' not in mapOrgs:
            orgIDs = ""
            for i in mapOrgs:
                orgIDs += i + ","
            sql += " where organization_ID in (%s) " % (orgIDs[0:-1])
        
        recs = db.engine.execute(sql).fetchall()
        
        markerData = {}
        markerData["cluster"] = True
        markerData["zoomToFit"] = False # can't zoom if there are no markers
        if recs:
            markerData["markers"] = []

            for rec in recs:
                #db.engine.execute returns a list of sets without column names
                #namedtuple creates an object that makeBasicMarker can access with dot notation
                Fields = namedtuple('record', 'locationName ID latitude longitude')
                record = Fields(rec[0], rec[1], rec[2], rec[3])

                marker = makeBasicMarker(record) # returns a dict or None
                
                if marker:
                    popup = render_template('map/locationListPopup.html', rec=record)
                    popup = escapeTemplateForJson(popup)
                    marker['popup'] = popup
                    
                    markerData["markers"].append(marker)
                    
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
    #   Location, Location ID, Latitude, Longitude, Trip Count, 
    #       Trip Date, Turn direction, Traveler name, Organization Name, Event Title, Event Start, Event End
        csv = ""
        for rec in recs:
            row = ""
            if exportStyle == "summary":
                headers = "Location Name,Latitude,Longitude,Trip Count,Organization Name,Event Title,Event Start,Event End\n"
                row = "\"%s\",\"%s\",\"%s\",%d,\"%s\",\"%s\",\"%s\",\"%s\"\n" % (rec[0], rec[2], rec[3], rec[4], rec[8], rec[9], rec[10], rec[11])
            if exportStyle == "detail":
                headers = "Location Name,Latitude,Longitude,Trip Count,Trip Date,Turn,Traveler,Organization Name,Event Title,Event Start,Event End\n"
                row = "\"%s\",\"%s\",\"%s\",%d,\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\"\n" % (rec[0], rec[2], rec[3], rec[4], rec[5], rec[6], rec[7], rec[8], rec[9], rec[10], rec[11])
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
    
    # the first 5 fields are used for map display
    sql = "Select "
    sql += "location.locationName, "
    sql += "location.ID, "
    sql += "location.latitude, "
    sql += "location.longitude, "
    
    if exportStyle == "summary" :
        sql += "sum(tripCount), " #using a summary function will compress detail
    else:
        sql += "tripCount, "
        
    sql += "strftime('%Y-%m-%d %H:%M:%S', tripDate), "
    sql += "trip.turnDirection, "
    sql += "traveler.name, "
    sql += "organization.name, "
    sql += "count_event.title, "
    sql += "strftime('%Y-%m-%d %H:%M', count_event.startDate), "
    sql += "strftime('%Y-%m-%d %H:%M', count_event.endDate) "
    
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
        sql += "Group by organization.name, count_event.ID, location.Locationname "
        sql += "Order by organization.name, count_event.ID, location.locationName"
        
    else:
        #Detail
        sql += "Order by organization.name, count_event.ID, location.locationName, trip.tripDate, trip.turnDirection, traveler.name"
        
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
    
def getSearchFormSelectValues(mapOrgs,mapEvents):
    # all parameters must be empty lists
    # lists will be manipulated directly. 
    # DON'T ASSIGN VALUES TO LISTS - USE .append()
    
    if request.form and 'mapOrgs' in request.form.keys():
        tempList = request.form.getlist('mapOrgs')
        if '0' in tempList:
            # if 'ALL' is selected just show all
            mapOrgs.append('0')
        else:
            for i in tempList:
                mapOrgs.append(i)
    else:
        mapOrgs.append('0')
        
    if request.form and 'mapEvents' in request.form.keys():
        tempList = request.form.getlist('mapEvents')
        if '0' in tempList:
            # if 'ALL' is selected just show all
            mapEvents.append('0')
        else:
            for i in tempList:
                mapEvents.append(i)
    else:
        mapEvents.append('0')
    
    
def getOrgs(queryData):
    # queryData is a dictionary
    queryData["orgs"] = []
    sql = "select * from organization where 1=1 "
    sql += " order by 'name'"
        
    orgs = db.engine.execute(sql).fetchall()
    
    if orgs:
        for org in orgs:
            d = {'name':org.name, 'ID':str(org.ID)}
            queryData['orgs'].append(d)