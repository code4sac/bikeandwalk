from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint
from bikeandwalk import db, app
from views.utils import nowString
from models import Traveler, EventTraveler, TravelerFeature, Feature, Trip
from views.utils import printException, cleanRecordID
from views.trip import getEventTravelerTripTotal
from forms import EventTravelerForm

mod = Blueprint('traveler',__name__)


def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.delete')
    g.title = 'Traveler'

@mod.route('/traveler/')
def display():
    if db :
        rec = Traveler.query.all()
        setExits()
        return render_template('traveler/traveler_list.html', recs=rec)

    flash('Could not open Database')
    return redirect(url_for('home'))
    

@mod.route('/traveler/edit', methods=['POST', 'GET'])
@mod.route('/traveler/edit/', methods=['POST', 'GET'])
@mod.route('/traveler/edit/<id>/', methods=['POST', 'GET'])
def edit(id=0):
    setExits()
    id = cleanRecordID(id)
    if id < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
    
    if not request.form:
        """ if no form object, send the form page """
        # get the Org record if you can
        rec = None
        if id > 0:
            rec = Traveler.query.get(id)
        #get a cursor of all features
        features = getFeatureSet(id)

        return render_template('traveler/traveler_edit.html', rec=rec, features=features, lastFeature=len(features))

    #have the request form
    if validForm():
        if id > 0:
            rec = Traveler.query.get(id)
        else:
            ## create a new record stub
            rec = Traveler(request.form['name'],request.form['travelerCode'])
            db.session.add(rec)
        try:
            db.session.commit() ## ID now has a value
        except Exception as e:
            db.session.rollback()
            flash(printException('Could not '+g.title+' record.',"error",e))
            return redirect(g.listURL)
            
        #update the record
        rec.name = request.form['name']
        rec.travelerCode = request.form['travelerCode']
        rec.description = request.form['description']
        rec.iconURL = request.form['iconURL']
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(printException('Could not Update '+g.title+' record (ID ='+str(id)+').',"error",e))
            return redirect(g.listURL)
            
        id = rec.ID
        
        # now update the features
        #delete the old ones first
        tf = TravelerFeature.query.filter_by(traveler_ID = str(id)).delete(synchronize_session='fetch')
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(printException('Could not Delete Feature records for '+g.title+' record (ID ='+str(id)+').',"error",e))
            return redirect(g.listURL)
           
        #create new ones
        featureSet = request.form.getlist('featureSet')
        for feat in featureSet:
            tf = TravelerFeature(id,int(feat))
            db.session.add(tf)
            
        try:
            db.session.commit()    
        except Exception as e:
            db.session.rollback()
            flash(printException('Could not Create Feature records for '+g.title+' record (ID ='+str(id)+').',"error",e))
            return redirect(g.listURL)
                 
        return redirect(g.listURL)

    # form not valid - redisplay
    features = getFeatureSet(id)
    app.logger.info("Feature set len = " +str(features))
    return render_template('traveler/traveler_edit.html', rec=request.form, features=features, lastFeature=len(features))


@mod.route('/traveler/delete/', methods=['GET'])
@mod.route('/traveler/delete/<id>/', methods=['GET'])
def delete(id=0):
    setExits()
    id = cleanRecordID(id)
    if id < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
 
    rec = Traveler.query.get(id)
    if rec:
        ## Can't delete Traveler that has been used in a trip
        trip = Trip.query.filter_by(traveler_ID = str(id)).all()
        if trip:
            #can't delete
            flash("You can't delete this Traveler because there are Trip records that use it")
            return redirect(g.listURL)
        
        # Delete the related records
        et = EventTraveler.query.filter_by(traveler_ID = str(id)).delete(synchronize_session='fetch')
        tf = TravelerFeature.query.filter_by(traveler_ID = str(id)).delete(synchronize_session='fetch')
        ## delete the traveler
    try:
        db.session.delete(rec)
        db.session.commit()
    except Exception as e:
        flash(printException('Error attempting to delete '+g.title+' record.',"error",e))
        db.session.rollback()

    return redirect(g.listURL)

    
def validForm():
    # Validate the form
    goodForm = True

    if request.form['travelerCode'] == '':
        goodForm = False
        flash('Traveler Code may not be blank')
        
    if request.form['travelerCode'] != '':
        val = Traveler.query.filter(Traveler.travelerCode == request.form['travelerCode'], Traveler.ID != request.form['ID']).count()
        if val > 0:
            goodForm = False
            flash('That Traveler Code is in use already')
            
    if len(request.form.getlist('featureSet')) == 0:
            goodForm = False
            flash('You must select at least one Feature')
        
    return goodForm
    
def getFeatureSet(id=0):
    f = Feature.query.all()
    rows = Feature.query.count()
    #app.logger.info("Row Count = " + str(rows))
    records = dict()
    for elem in range(rows):
        feature = dict()
        feature['ID'] = f[elem].ID
        feature['featureClass'] = f[elem].featureClass
        feature['featureValue'] = f[elem].featureValue
        feature['featureSelected'] = False
        if id > 0:
            tf = TravelerFeature.query.filter_by(traveler_ID = id, feature_ID = f[elem].ID).all()
            if tf:
                feature['featureSelected'] = True
        records[elem] = feature
    return records

## return an HTML code segment to include in the count_event edit form
@mod.route("/traveler/getTravelerList", methods=['GET'])
@mod.route("/traveler/getTravelerList/<countEventID>/", methods=['GET','POST'])
def getTravelerList(countEventID = 0):
    countEventID = cleanRecordID(countEventID)
    out = ""

    if countEventID > 0:
        recs = getEventTravelers(countEventID)
        if recs:
            for eventTraveler in recs:
                traveler = Traveler.query.get(eventTraveler.traveler_ID)
                if traveler:
                    totalTrips = getEventTravelerTripTotal(countEventID, traveler.ID)
                    out += render_template('traveler/travelerListElement.html', eventTraveler=eventTraveler, traveler=traveler, totalTrips=totalTrips)

    return out

@mod.route('/eventtraveler/removeFromList', methods=["GET","POST"])
@mod.route('/eventtraveler/removeFromList/<eventTravelerID>/', methods=["GET","POST"])
def removeFromList(eventTravelerID):
    eventTravelerID=cleanRecordID(eventTravelerID)
    if eventTravelerID > 0:
        # remove the event_traveler record only if there are no trips for this traveler / event
        rec = EventTraveler.query.get(eventTravelerID)
        if rec:
            tripCnt = getEventTravelerTripTotal(eventTravelerID, rec.traveler_ID)
            if tripCnt == 0:
                db.session.delete(rec)
                db.session.commit()
                return "success"

    return "failure: Unable to Remove that record."
    
    
@mod.route("/eventTraveler/selectNew/", methods=['GET'])
@mod.route("/eventTraveler/selectNew/<countEventID>/", methods=['GET'])
def newEventTraveler(countEventID=0):
    g.countEventID =cleanRecordID(countEventID)
    return editEventTraveler(0)
    
## editing list called from within countEvent form
@mod.route("/eventTraveler/editFromList", methods=['GET',"POST"])
@mod.route("/eventTraveler/editFromList/<eventTravelerID>/", methods=['GET',"POST"])
def editEventTraveler(eventTravelerID=0):
    setExits()
    data = None
    rec = None
    traveler = None

    if request.form:
        eventTravelerID = cleanRecordID(request.form["ID"])
        g.countEventID = cleanRecordID(request.form["countEvent_ID"])
    else:
        eventTravelerID = cleanRecordID(eventTravelerID)
        
    travelerName = ""
    if eventTravelerID > 0:
        rec = EventTraveler.query.get(eventTravelerID)
        if rec:
            g.countEventID = rec.countEvent_ID
            traveler = Traveler.query.get(rec.traveler_ID)
            travelerName = traveler.name
            
#    print eventTravelerID
#    print g.countEventID
        
    if g.countEventID <= 0:
        return "failure: No Count Event ID was found."

    availableTravelers = None 
    if eventTravelerID == 0:
        #If creating a new record, get a list of unused travelers

        sql = 'select ID,name from traveler \
            where  \
            ID not in \
               (select traveler_ID from event_traveler where countEvent_ID  = %d);' \
            % (g.countEventID)

        ## It's important to call fetchcll() or fetchone() after executing sql this way or the
        ##  database will be left in a locked state.
        availableTravelers = db.engine.execute(sql).fetchall()
        if len(availableTravelers) == 0:
            return "failure: There are no more Travelers to use."
    
    travelerOrder = None
    #get a list of all the sort orders for the current set of travelers for this event
    et = getEventTravelers(g.countEventID)
    travelerOrder = []
    elem = {"travelerName" : "1st in list", "sortOrder": 0}
    lastSortOrder = 0
    travelerOrder.append(elem)
    for t in et:
        elem = {"travelerName": ("Before " + t.travelerName),"sortOrder": int((lastSortOrder + t.sortOrder) / 2)}
        lastSortOrder = t.sortOrder
        if traveler:
            currentID = traveler.ID
        else:
            currentID = 0
            
        if t.traveler_ID != currentID:
            travelerOrder.append(elem)
            
    elem = {"travelerName": "End of List","sortOrder": lastSortOrder + 100}
    travelerOrder.append(elem)
    
    form = EventTravelerForm(request.form, rec)
     
     
    if request.method == "POST" :
        #There is only one select element on the form so it always validates
        if not rec:
            rec = EventTraveler(form.countEvent_ID.data, form.traveler_ID.data)
            if  not rec:
                return "failure: Unable to create a new EventTraveler record"
                
            db.session.add(rec)
            
        rec.sortOrder = form.sortOrder.data
        try:
            db.session.commit()
            
        except Exception as e:
            printException("Unable to save Assignment from list", "error", e)
            return "failure: Sorry. Unable to save your changes."
        
        # "Normalize the sortOrders"
        recs = EventTraveler.query.filter(EventTraveler.countEvent_ID == g.countEventID).order_by(EventTraveler.sortOrder)
        if recs:
            next = 100
            for rec in recs:
                rec.sortOrder = next
                next += 100
            try:
                db.session.commit()
            except Exception as e:
                # this is not critical to the current operation, advise only
                printException("Unable to Normalize EventTraveler recs", "error", e)
                
        return "success" # the success function looks for this...
    
    return render_template('traveler/eventTravelerPopupEditForm.html', 
        form=form, 
        availableTravelers=availableTravelers,
        travelerOrder=travelerOrder, 
        travelerName=travelerName,
        )

    
def getEventTravelers(countEventID):
    countEventID = cleanRecordID(countEventID)
    return EventTraveler.query.filter(EventTraveler.countEvent_ID==countEventID).order_by(EventTraveler.sortOrder)