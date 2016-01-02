from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint
from bikeandwalk import db, app
from views.db import nowString
from models import Traveler, EventTraveler, TravelerFeature, Feature, Trip
from views.db import printException

mod = Blueprint('traveler',__name__)


def setExits():
    g.listURL = url_for('.traveler_list')
    g.editURL = url_for('.traveler_edit')
    g.deleteURL = url_for('.traveler_delete')
    g.title = 'Traveler'

@mod.route('/traveler/')
def traveler_list():
    if db :
        cur = Traveler.query.all()
        setExits()
        return render_template('traveler/traveler_list.html', recs=cur)

    flash('Could not open Database')
    return redirect(url_for('home'))
    

@mod.route('/traveler/edit', methods=['POST', 'GET'])
@mod.route('/traveler/edit/', methods=['POST', 'GET'])
@mod.route('/traveler/edit/<id>/', methods=['POST', 'GET'])
def traveler_edit(id=0):
    if db:
        setExits()
        if not request.form:
            """ if no form object, send the form page """
            # get the Org record if you can
            cur = None
            if int(id) > 0:
                cur = Traveler.query.filter_by(ID=id).first_or_404()
            #get a cursor of all features
            features = getFeatureSet(int(id))
            #app.logger.info("Feature set len = " +str(len(features)))
            return render_template('traveler/traveler_edit.html', rec=cur, features=features, lastFeature=len(features))

        #have the request form
        if validForm():
            try:
                if int(id) > 0:
                    cur = Traveler.query.get(id)
                else:
                    ## create a new record stub
                    cur = Traveler(request.form['name'],request.form['travelerCode'])
                    db.session.add(cur)
                    db.session.commit() ## ID now has a value
                #update the record
                cur.name = request.form['name']
                cur.travelerCode = request.form['travelerCode']
                cur.description = request.form['description']
                cur.iconURL = request.form['iconURL']
                db.session.commit()
                id = cur.ID
                
                # now update the features
                #delete the old ones first
                tf = TravelerFeature.query.filter_by(traveler_ID = str(id)).delete(synchronize_session='fetch')
                db.session.commit()
                
                #create new ones
                featureSet = request.form.getlist('featureSet')
                for feat in featureSet:
                    tf = TravelerFeature(id,int(feat))
                    db.session.add(tf)
                db.session.commit()    
                    
                return redirect(url_for('.traveler_list'))

            except Exception as e:
                flash(printException('Could not Update '+g.title+' record.',"error",e))
                db.session.rollback()

        # form not valid - redisplay
        features = getFeatureSet(id)
        app.logger.info("Feature set len = " +str(features))
        return render_template('traveler/traveler_edit.html', rec=request.form, features=features, lastFeature=len(features))

    else:
        flash('Could not open database')

    return redirect(url_for('.traveler_list'))

@mod.route('/traveler/delete/', methods=['GET'])
@mod.route('/traveler/delete/<id>/', methods=['GET'])
def traveler_delete(id=0):
    setExits()
    if int(id) > 0:
        try:
            rec = Traveler.query.get(id)
            if rec:
                ## Can't delete Traveler that has been used in a trip
                trip = Trip.query.filter_by(traveler_ID = str(id)).all()
                if trip:
                    #can't delete
                    flash("You can't delete this Traveler because there are Trip records that use it")
                    return redirect(url_for('.traveler_list'))
                
                # Delete the related records
                et = EventTraveler.query.filter_by(traveler_ID = str(id)).delete(synchronize_session='fetch')
                tf = TravelerFeature.query.filter_by(traveler_ID = str(id)).delete(synchronize_session='fetch')
                ## delete the traveler
                db.session.delete(rec)
                db.session.commit()
            else:
                flash("Record could not be deleted.")
        except Exception as e:
            flash(printException('Error attempting to delete '+g.title+' record.',"error",e))
            db.session.rollback()
            return traveler_edit(str(id))

    return redirect(url_for('.traveler_list'))


@mod.route('/traveler/select/', methods=['GET'])
@mod.route('/traveler/select/<id>/', methods=['GET'])
def traveler_select(id=0):
    return "Traveler Select goes here!"

    
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
