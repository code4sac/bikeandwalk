from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint, Response
from bikeandwalk import db, app
import csv
import StringIO

mod = Blueprint('report',__name__)

def setExits():
    g.listURL = url_for('.display')
    #g.editURL = url_for('.edit')
    #g.deleteURL = url_for('.delete')
    g.title = 'Report'

@mod.route('/report')
@mod.route('/report/')
def display():
    setExits()
    return render_template("report/report_list.html")
    
    
@mod.route('/report/get_csv')
@mod.route('/report/get_csv/')
def getcsv():
    sql = 'select trip.tripCount, trip.turnDirection, trip.location_ID, trip.tripDate, \
    location.locationName, location.latitude, location.longitude, \
    traveler.name as travelerName \
    from trip, location, traveler \
    where location.latitude <> "" and location.longitude <> "";'
    recs = db.engine.execute(sql).fetchall()
    k = db.engine.execute(sql).keys()
    out = StringIO.StringIO()
    rowvalue = []
    if recs and k:
        writer = csv.writer(out)
        del rowvalue
        rowvalue = [field for field in k]
        writer.writerow(rowvalue)
        for rec in recs:
            del rowvalue
            rowvalue = [field for field in rec]
            writer.writerow(rowvalue)
    result = out.getvalue()
    out.close()
    result = result.replace("\r\n", chr(13))
    # setup the page headers for a file download
    return Response(result,
                           mimetype="text/csv",
                           headers={"Content-Disposition":
                                        "attachment;filename=bikeandwalkTrips.csv"})


