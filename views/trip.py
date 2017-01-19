from flask import request, g, redirect, url_for, \
     render_template, flash, Blueprint, abort
from bikeandwalk import db
from models import Trip
from views.utils import printException, getCountEventChoices, \
    getLocationChoices, getTravelerChoices, getTurnDirectionChoices, cleanRecordID
from forms import TripForm
from datetime import datetime
from views import searchForm

mod = Blueprint('trip',__name__)

def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.delete')
    g.title = 'Trip'
    
@mod.route("/trip/", methods=['GET', 'POST'])
@mod.route("/trip", methods=['GET', 'POST'])
def display():
    setExits()
    if db :
        recs = None
        queryData = {}
        queryData['searchType'] = 'tripList'
        queryData['selectType'] = 'single'
        queryData['includeAllOption'] = False
        
        searchOrgs = []
        searchEvents = []
        searchForm.getSelectValues(request.form,searchOrgs,searchEvents)
        queryData['searchOrgs'] = searchOrgs
        queryData['searchEvents'] = searchEvents
        
        #Get all orgs
        searchForm.orgsToDict(queryData)

        #get the Events
        searchForm.eventsToDict(queryData)
        
        recs = queryTripData(searchOrgs, searchEvents, searchType='listing')
        
        return render_template('trip/trip_list.html', recs=recs, queryData=queryData )
        
    else:
        flash(printException('Could not open Database',"info"))
        return redirect(url_for('home'))
        

@mod.route("/trip/edit/", methods=['GET'])
@mod.route("/trip/edit/<id>", methods=['GET','POST'])
@mod.route("/trip/edit/<id>/", methods=['GET','POST'])
def edit(id=0):
    setExits()
    id = cleanRecordID(id)
    if id < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
            
    rec = None
    if id > 0:
        rec = Trip.query.get(id)
        if not rec:
            flash(printException("Could not edit that "+g.title + " record. ID="+str(id)+")",'error'))
            return redirect(g.listURL)
    
    form = TripForm(request.form, rec)
    ## choices need to be assigned before rendering the form
    # AND before attempting to validate it
    form.countEvent_ID.choices = getCountEventChoices()
    form.location_ID.choices = getLocationChoices()
    form.traveler_ID.choices = getTravelerChoices()
    form.turnDirection.choices = getTurnDirectionChoices()
    
    if request.method == 'POST' and form.validate():
        if not rec:
            rec = Trip(form.tripCount.data,form.tripDate.data,form.turnDirection.data,form.seqNo.data,form.location_ID.data,form.traveler_ID.data,form.countEvent_ID.data)
            db.session.add(rec)
        form.populate_obj(rec)
        db.session.commit()
        return redirect(g.listURL)
        
    return render_template('genericEditForm.html', rec=rec, form=form)
    
    
@mod.route("/trip/delete/", methods=['GET'])
@mod.route("/trip/delete/<id>", methods=['GET','POST'])
@mod.route("/trip/delete/<id>/", methods=['GET','POST'])
def delete(id=0):
    setExits()
    id = cleanRecordID(id)
    if id < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
        
    if id > 0:
        rec = Trip.query.get(id)
        if rec:
            db.session.delete(rec)
            db.session.commit()
        else:
            flash(printException("Could not delete that "+g.title + " record ID="+str(id)+" could not be found.","error"))
        
    return redirect(g.listURL)
    
def getAssignmentTripTotal(countEventID=0, locationID=0, travelerID=0, startTime=None, endTime=None, turnDir=None, seqNo = None):
    # Jun 3, 2016 - Modified to allow for selection of total count for a single turn Direction and or seqNo
    
    result = 0
    countEventID = cleanRecordID(countEventID)
    locationID = cleanRecordID(locationID)
    travelerID = cleanRecordID(travelerID)
    sql =  "select sum(tripCount) as tripTotal from trip where countEvent_ID = %d and location_ID = %d" % (int(countEventID), int(locationID))
    if travelerID > 0:
        sql += " and traveler_ID = %d" % (travelerID)
    if startTime:
        timeStamp = startTime
        sql += " and tripDate >= '%s'" % (timeStamp)
    if endTime:
        timeStamp = endTime
        sql += " and tripDate <= '%s'" % (timeStamp)
    if turnDir:
        sql += " and turnDirection = '%s'" % (turnDir)
    if seqNo:
        sql += " and seqNo = '%s'" % (seqNo)
        
    sql += ";"
    
    cur = db.engine.execute(sql).fetchone()
    if cur:
        result = cur[0]
        if result == None:
            result = 0

    return result
    
    
def getEventTravelerTripTotal(countEventID = 0, travelerID =0):
    result = 0
    countEventID = cleanRecordID(countEventID)
    travelerID = cleanRecordID(travelerID)
    sql =  "select sum(tripCount) as tripTotal from trip where countEvent_ID = %d and traveler_ID = %d;" % (countEventID, travelerID)
    cur = db.engine.execute(sql).fetchone()
    if cur:
        result = cur[0]
        if result == None:
            result = 0
            
    return result

def getCountEventTripTotal(countEventID):
    result = 0
    countEventID = cleanRecordID(countEventID)
    sql =  "select sum(tripCount) as tripTotal from trip where countEvent_ID = %d;" % (countEventID)
    cur = db.engine.execute(sql).fetchone()
    if cur:
        result = cur[0]
        if result == None:
            result = 0
            
    return result

def getLocationTripTotal(locationID):
    result = 0
    locationID = cleanRecordID(locationID)
    sql =  "select sum(tripCount) as tripTotal from trip where location_ID = %d;" % (locationID)
    cur = db.engine.execute(sql).fetchone()
    if cur:
        result = cur[0]
        if result == None:
            result = 0
            
    return result

def queryTripData(searchOrgs, searchEvents, searchType='summary'):

    # the columns output are:
    #   Location Name, Location ID, Latitude, Longitude, sum(tripCount), tripCount, 
    #      tripDate, Event Start, Event End, Turn direction, Traveler name
    
    #format the search criteria for query
    orgIDs = ""
    if searchOrgs and '0' not in searchOrgs:
        for i in searchOrgs:
            if i.isdigit():
                orgIDs += i + ","
    if len(orgIDs) > 0:
        orgIDs = orgIDs[0:-1] # remove trailing comma
    
    eventIDs = ""
    if searchEvents and '0' not in searchEvents:
        for i in searchEvents:
            if i.isdigit():
                eventIDs += i + ","
    if len(eventIDs) > 0:
        eventIDs = eventIDs[0:-1] # remove trailing comma
    
    # the first 5 fields are used for map display
    sql = "Select "
    if searchType == 'map':
        sql += " distinct "
    sql += "location.locationName, "
    sql += "location.ID, "
    sql += "location.latitude, "
    sql += "location.longitude, "
    
    if searchType == 'map':
        sql += "(select sum(trip.tripCount) from trip where \
                trip.countEvent_ID in (%s) and location.ID = trip.location_ID) as locationTotal " % (eventIDs)
    if searchType != 'map':
        if searchType == "summary" :
            sql += "sum(tripCount), " #using a summary function will compress detail
        if searchType in ("detail", "listing") :
            sql += " tripCount, "
        sql += "strftime('%Y-%m-%d %H:%M:%S', tripDate), "
        sql += "trip.turnDirection, "
        sql += "traveler.name as travelerName, "
        sql += "organization.name, "
        sql += "count_event.title as eventTitle, "
        sql += "strftime('%Y-%m-%d %H:%M', count_event.startDate), "
        sql += "strftime('%Y-%m-%d %H:%M', count_event.endDate) "
        if searchType == 'listing':
            sql += ", trip.ID, tripDate "
            
    sql += "from trip JOIN location, organization, count_event, traveler "
    sql += "Where "

    if len(orgIDs) > 0:
        sql += "(organization.ID in ( %s)) " % (orgIDs)

    if len(eventIDs) > 0:
        if len(orgIDs) >0:
            sql += " and "
        sql += "(count_event.ID in (%s)) " % (eventIDs)

    if len(orgIDs)+len(eventIDs) > 0:
        sql += " and "

    sql += "trip.countEvent_ID = count_event.ID and "
    sql += "trip.location_ID = location.ID and "
    sql += "trip.traveler_ID = traveler.ID and "
    sql += "count_event.organization_ID = organization.ID "
    if searchType == "summary":
        sql += "Group by organization.name, count_event.ID, location.Locationname "
        sql += "Order by organization.name, count_event.startDate, location.locationName"

    else:
        #Detail
        sql += "Order by organization.name, count_event.startDate, location.locationName, trip.tripDate, trip.turnDirection, traveler.name"

    print sql

    return db.engine.execute(sql).fetchall()