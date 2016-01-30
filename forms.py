from wtforms import Form, BooleanField, StringField, HiddenField, SelectField, IntegerField, validators, TextAreaField

    
class AssignmentForm(Form):
    #ID = HiddenField('ID')
    #assignmentUID = StringField('Assignment ID', )
    weather = SelectField("Weather",
        choices=[("","Select Weather Type"),("Fair", "Fair"),("Rainy","Rainy"),("Very Cold", "Very Cold")], )
    countEvent_ID = SelectField("Count Event",
        [validators.NumberRange(min=1, message="You must select a count event")], 
        coerce=int, choices=[], )
    user_ID = SelectField("User Name", coerce=int, choices=[], )
    location_ID = SelectField("Location",
        [validators.NumberRange(min=1, message="You must select a location")], 
        coerce=int, choices=[], )
    locationName = HiddenField("Location Name",)
    userName = HiddenField("User Name",)

class AssignmentEditFromListForm(AssignmentForm):
    ID = HiddenField('ID')
    assignmentUID = HiddenField('Assignment ID', )
    countEvent_ID = HiddenField("Count Event ID")
    location_ID = HiddenField("Location ID")


  
class LocationForm(Form):
    #ID = HiddenField("ID")
    locationName = StringField("Location Name", [validators.DataRequired(),], )
    NS_Street = StringField("North South St.", [validators.DataRequired(),], )
    EW_Street = StringField("East West St.", [validators.DataRequired(),], )
    locationType = SelectField("Count Type", default="intersection",
        choices=[("intersection", "Intersection"),("screenline","Screen Line")], )
    city = StringField("City", [validators.DataRequired(),], )
    state = StringField("State", [validators.DataRequired(),], )
    latitude = StringField("Latitude",  )
    longitude = StringField("Longitude", )
    #organization_ID = IntegerField("Organization ID", [validators.DataRequired(),], )

class TripForm(Form):
    #ID = HiddenField("ID")
    tripCount = IntegerField("Count", [validators.DataRequired(),],)
    tripDate = StringField("Date/Time", [validators.DataRequired(),], )
    turnDirection = SelectField("Turn Direction",
        [validators.Length(min=1, message="You must indicate the turn direction")], 
        choices=[], )
    seqNo = StringField("SeqNo", default="0", )
    location_ID = SelectField("Location",
        [validators.NumberRange(min=1, message="You must select a location")], 
        coerce=int, choices=[], )
    traveler_ID = SelectField("Traveler",
        [validators.NumberRange(min=1, message="You must select a Traveler")], 
        coerce=int, choices=[], )
    countEvent_ID = SelectField("Count Event",
        [validators.NumberRange(min=1, message="You must select a Count Event")], 
        coerce=int, choices=[], )

class TravelerListEditForm(Form):
    ID = IntegerField("ID", [validators.DataRequired()])
    name = StringField("Name", [validators.DataRequired()])
    description = TextAreaField("Description", [validators.DataRequired()])
    iconURL = StringField("Icon URL")
    travelerCode = IntegerField("Traveler Code Name", [validators.DataRequired()])
    
class EventTravelerForm(Form):
    ID = IntegerField("ID", [validators.DataRequired()])
    countEvent_ID = HiddenField("Count Event ID", [validators.DataRequired()])
    traveler_ID = HiddenField("Traveler ID", [validators.DataRequired()])
    sortOrder = IntegerField("Sort Order")
    