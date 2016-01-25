from bikeandwalk import db, app
import csv
import StringIO


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
    return result

