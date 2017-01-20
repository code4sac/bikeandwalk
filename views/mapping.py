## Map view of trips
from flask import g, redirect, url_for, \
     render_template, flash, Blueprint, request, make_response, abort
from bikeandwalk import db, app
from models import Trip, Location, Organization, CountEvent, Traveler, TravelerFeature, Feature
from views.utils import printException
from views import searchForm
from collections import namedtuple
import json
from datetime import datetime
from views.trip import getAssignmentTripTotal, queryTripData

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
        searchOrgs = []
        searchEvents = []
        searchForm.getSelectValues(request.form,searchOrgs,searchEvents) 
        
        queryData = {}
        queryData["searchOrgs"] = searchOrgs
        queryData["searchEvents"] = searchEvents
        queryData['searchType'] = 'map'
        queryData['selectType'] = 'multiple'
        queryData['includeAllOption'] = True
        
        #Get all orgs
        searchForm.orgsToDict(queryData)

        #get the Events
        searchForm.eventsToDict(queryData)
        
        # Jun 10, 2016 modified query to speed up map display
        # The order of the selected fields is critical to creating a proper namedtuple below
        
        recs = queryTripData(searchOrgs, searchEvents, queryData['searchType'])
        
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
                    
                    marker["divIcon"] = getDivIcon(record.tripCount)
                    
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
        queryData['searchType'] = 'locations'
        queryData['selectType'] = 'multiple'
        queryData['includeAllOption'] = True
        
        #Get all orgs
        searchForm.orgsToDict(queryData)
        
        searchOrgs = []
        searchEvents = []
        if not request.form and g.orgID:
            queryData['searchOrgs'] = [str(g.orgID)]
        else:
            searchForm.getSelectValues(request.form, searchOrgs,searchEvents) # all parameters must be empty lists
            queryData['searchOrgs'] = searchOrgs #We don't need searchEvents for this map

        sql = "select locationName, ID, latitude, longitude from location "
        if '0' not in searchOrgs:
            orgIDs = ""
            for i in searchOrgs:
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
    if 'searchOrgs' in data.keys() and 'searchEvents' in data.keys():
        recs = queryTripData(data['searchOrgs'], data['searchEvents'], exportStyle)
        
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
            header = ''
            if exportStyle == "map":
                headers = "Location Name,Latitude,Longitude,Trip Count\n"
                row = "\"%s\",\"%s\",\"%s\",%d\n" % (rec[0], rec[2], rec[3], rec[4])
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
        
@mod.route('/report/map/liveCount/', methods=['post', 'get'])
def liveCount():
    """A simple page to show the counts for a specific count event.
    The idea is that each refresh will update the location count displays
    """
    
    g.title = "Live Count"
    
    #get the form data
    searchOrgs = []
    searchEvents = []
    searchForm.getSelectValues(request.form, searchOrgs,searchEvents) # all parameters must be empty lists
    
    queryData = {}
    queryData["searchOrgs"] = searchOrgs
    queryData["searchEvents"] = searchEvents
    queryData['searhType'] = 'liveCount'
    queryData['selectType'] = 'single'
    queryData['includeAllOption'] = False
    
    #Get all orgs
    searchForm.orgsToDict(queryData)

    #get the Events
    searchForm.eventsToDict(queryData)
    
    #Select assignment records
    eventIDs = ""
    for i in searchEvents:
        if i.isdigit():
            eventIDs += i + ","
    
    recs = None

    sql = "select assignment.ID, assignment.countEvent_ID, assignment.location_ID, \
            count_event.title, location.locationName, \
            (select sum(trip.tripCount) from trip where trip.countEvent_ID = count_event.ID and trip.location_ID = location.ID) as tripTotal \
            from assignment join location, count_event "
                
    if eventIDs != "":
        sql += " where assignment.countEvent_ID in (%s) " % (eventIDs[0:-1])
                
    sql += " and location.ID = assignment.location_ID \
            and count_event.ID = assignment.countEvent_ID "
    theOrg = "0"
    if queryData['searchOrgs'] and len(queryData['searchOrgs']) > 0:
        theOrg = queryData['searchOrgs'][0]
        
    sql += " and count_event.organization_ID = %s " % theOrg
    sql += " order by tripTotal desc"

    recs = db.engine.execute(sql).fetchall()
    
    #Display the page
    return render_template('map/liveCount.html', queryData=queryData, assignments=recs)
    
    
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

def getDivIcon(markerCount):
    """
    return an HTML block to be used as the DivIcon for a marker
    """
    if not markerCount:
        markerCount = "n/a"
    markerName = "BikeMarker_Blue.png"

    if type(markerCount) is int:
        if markerCount > 19:
            markerName = "BikeMarker_Green.png"
        if markerCount > 99:
            markerName = "BikeMarker_Gold.png"
        if markerCount > 199:
            markerName = "BikeMarker_Red.png"
            
    divIcon = render_template("map/divicon.html", markerName=markerName, markerCount=markerCount)
    
    return escapeTemplateForJson(divIcon)
    