## Map view of trips
from flask import g, redirect, url_for, \
     render_template, flash, Blueprint, request, make_response, abort
from bikeandwalk import db, app
from models import Trip, Location, Organization, CountEvent, Traveler, TravelerFeature, Feature
from views.utils import printException, getDatetimeFromString
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
                #namedtuple creates an object that getMarkerDict can access with dot notation
                Fields = namedtuple('record', 'locationName ID latitude longitude tripCount')
                record = Fields(rec[0], rec[1], rec[2], rec[3], rec[4])

                marker = getMarkerDict(record, searchEvents) # returns a dict or None
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
                #namedtuple creates an object that getMarkerDict can access with dot notation
                Fields = namedtuple('record', 'locationName ID latitude longitude')
                record = Fields(rec[0], rec[1], rec[2], rec[3])

                marker = getMarkerDict(record) # returns a dict or None
                
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
    data = None
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
        
        
    if exportStyle == 'nbpd':
        # this export is completely different...
        return NBPD_Export(data)
        
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
            headers = "%s is an unknown export style." % (exportStyle)
            row = ""
            if exportStyle == "map":
                headers = "Location Name,Latitude,Longitude,Trip Count\n"
                row = "\"%s\",\"%s\",\"%s\",%d\n" % (rec[0], rec[2], rec[3], rec[4])
            if exportStyle == "summary":
                headers = "Location Name,Latitude,Longitude,Trip Count,Organization Name,Event Title,Event Start,Event End\n"
                row = "\"%s\",\"%s\",\"%s\",%d,\"%s\",\"%s\",\"%s\",\"%s\"\n" % (rec[0], rec[2], rec[3], rec[4], rec[8], rec[9], rec[10], rec[11])
            if exportStyle == "detail":
                headers = "Location Name,Latitude,Longitude,Trip Count,Trip Date,Turn,Traveler,Organization Name,Event Title,Event Start,Event End\n"
                row = "\"%s\",\"%s\",\"%s\",%d,\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\"\n" % (rec[0], rec[2], rec[3], rec[4], rec[5], rec[6], rec[7], rec[8], rec[9], rec[10], rec[11])
                
            csv += row
            
        csv = headers + csv
   
    response = make_response(csv)
    now = datetime.now()
    now = now.strftime('%H%M%S')
    cd = "attachment; filename=BAW_%s_export_%s.csv" % (exportStyle, now)
    
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
    popup = popup.replace('\t',' ') # replace any tabs with space
    
    return popup
    
def getMarkerDict(rec, searchEvents=None):
    if rec and rec.latitude.strip() != '' and rec.longitude.strip() !='':
        marker = {"latitude": float(rec.latitude), "longitude": float(rec.longitude), 
           "locationID": rec.ID, "locationName": rec.locationName, "draggable": False, 
           }
           
        flowData = {}
        if searchEvents:
            '''
            # collect data for each direction of travel
                 "north":{"inbound":35,"outbound":66, "heading": 10},
                 "east":{"outbound":65,"inbound":54, "heading": 10}
                 "south":{"inbound":89, "outbound":80, "heading": 10},
                 "west":{"inbound":54,"outbound":25, "heading": 10},
            }
            '''
            flowRec = queryFlowData(rec.ID, searchEvents)
            if flowRec:
                rec = flowRec[0] # one row only
                # the compass headings
                headings = []
                headings.append(rec[8]) #North
                headings.append(rec[9]) #East
                headings.append(rec[8]+180) #South
                headings.append(rec[9]+180) #West
            
                compassPoint = ["north","east","south","west"]
                idx = 0
                heading = 0
                for direction in compassPoint:
                    if direction != "north":
                        idx += 2
                        heading += 1
                
                    dirData = {}
                    dirData["inbound"] = rec[idx]
                    dirData["outbound"] = rec[idx+1]
                    dirData["heading"] = headings[heading]
                
                    flowData[direction] = dirData
                
            marker["flowData"] = flowData
            
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
            
    divIcon = render_template("map/divIcon.html", markerName=markerName, markerCount=markerCount)
    
    return escapeTemplateForJson(divIcon)
    
def NBPD_Export(data):
    """Export data formatted in CSV text suitable to paste into the 
       National Bike & Ped Documentation project spreadsheet.
       The 'data' dict element searchEvents contains the count_event IDs to report on.
    """
    
    if data == None or 'searchEvents' not in data.keys() \
       or len(data['searchEvents']) != 1 or '0' in data['searchEvents']:
        flash("You must select only one Event and you may not select 'All' for this export")
        return redirect("/map/")

    # Step 1, get all the locations for this event that have counts
    sql = "select distinct location_ID from trip where countEvent_ID = %s order by location_ID" % (data['searchEvents'][0])
    recs = db.engine.execute(sql).fetchall()
    if recs == None:
        flash("There are no trips to report for that Count Event")
        return redirect("/map/")
        
    #put ids in a list
    locs = []
    for rec in recs: 
        locs.append(str(rec.location_ID))
    
    # Step 2, get all the results
    sql = """select count_event.title, count_event.weather, count_event.startDate, count_event.endDate, 
             location_ID, sum(tripCount) as tripTotal, lower(feature.featureClass) as featureClass, lower(feature.featureValue) as featureValue
             from trip JOIN location, count_event, traveler, traveler_feature, feature
          """
    sql += "where trip.countEvent_ID = %s and" % (data['searchEvents'][0])
    sql += """(
                (lower(featureClass) = "mode" and lower(featureValue) = "bicycle") or
                (lower(featureClass) = "mode" and lower(featureValue) = "pedestrian") 
                ) and 
                trip.countEvent_ID = count_event.ID and 
                trip.location_ID = location.ID and 
                trip.traveler_ID = traveler.ID and 
                traveler_feature.traveler_ID = trip.traveler_ID and 
                traveler_feature.feature_ID = feature.ID  

                Group by count_event.startDate, feature.featureValue, location.ID 
                Order by count_event.startDate, feature.featureValue, location.ID
            """
    
    recs = db.engine.execute(sql).fetchall()
    if recs == None:
        flash("No Trip Records Found for that event")
        return redirect("/map/")
        
    # Step 3 for each locaion output location header rows
    csv = ""
    #location ID
    for loc in locs:
        csv += "Loc. #%s," % (loc) 
    csv = csv[0:-1] + "\n" #replace last comma with return
    
    # Event Date
    sD = getDatetimeFromString(recs[0]["startDate"]).strftime('%m/%m/%y')
    for loc in locs:
        csv += "%s," % (sD)
    csv = csv[0:-1] + "\n" 
    
    # Time period
    sT = getDatetimeFromString(recs[0]["startDate"]).strftime('%H:%M')
    eT = getDatetimeFromString(recs[0]["endDate"]).strftime('%H:%M')
    for loc in locs:
        csv += "%s - %s," % (sT,eT)
    csv = csv[0:-1] + "\n" 
    
    #weather
    for loc in locs:
        csv += recs[0]["weather"] + ","
    csv = csv[0:-1] + "\n" 
    
    # Step 4, for each of 'bicycle', 'pedestrian' and 'other'
    for mode in ["bicycle", "pedestrian", "other"]:
        for loc in locs:
            foundVal = "0"
            for rec in recs:
                if rec["location_ID"] == int(loc) and rec["featureValue"] == mode:
                    foundVal = rec["tripTotal"]
                    break

            csv += "%s," %(foundVal)
            
        csv = csv[0:-1] + "\n" 
        
    
    response = make_response(csv)
    now = datetime.now()
    now = now.strftime('%H%M%S')
    cd = "attachment; filename=BAW_NBPD_export_%s.csv" % (now)

    response.headers['Content-Disposition'] = cd 
    response.mimetype='text/csv'

    return response
    
def queryFlowData(locID, searchEvents):
    """Retrun a single row from db of counts by direction or None"""
    
    sql = """select 
    (select ifnull(sum(tripCount),0) from trip where turnDirection LIKE "C%" and replaceMe ) as northBoundIn,
    (select ifnull(sum(tripCount),0) from trip where (turnDirection = "C2" or turnDirection = "B3" or turnDirection = "D1")  and replaceMe ) as northBoundOut,

    (select ifnull(sum(tripCount),0) from trip where turnDirection LIKE "D%" and replaceMe ) as eastBoundIn,
    (select ifnull(sum(tripCount),0) from trip where (turnDirection = "D2" or turnDirection = "C3" or turnDirection = "A1")  and replaceMe ) as eastBoundOut,

    (select ifnull(sum(tripCount),0) from trip where turnDirection LIKE "A%" and replaceMe ) as southBoundIn,
    (select ifnull(sum(tripCount),0) from trip where (turnDirection = "A2" or turnDirection = "D3" or turnDirection = "B1")  and replaceMe ) as southBoundOut,

    (select ifnull(sum(tripCount),0) from trip where turnDirection LIKE "B%" and replaceMe ) as westBoundIn,
    (select ifnull(sum(tripCount),0) from trip where (turnDirection = "B2" or turnDirection = "A3" or turnDirection = "C1") and replaceMe ) as westBoundOut,
    
    location.NS_Heading,location.EW_Heading
    from trip join location
    where location.ID = location_ID
    and replaceMe limit 1
    """
    
    crit = " location_ID = %d " % (locID )
    if not "0" in searchEvents and len(searchEvents) > 0:
        eventIDs = ""
        for i in searchEvents:
            eventIDs += "%s," % i
            
        crit += " and countEvent_ID in (%s) " % (eventIDs[0:-1])
        
    sql = sql.replace("replaceMe", crit)
    
    flowRow = db.engine.execute(sql).fetchall()
    
    return flowRow
    
    