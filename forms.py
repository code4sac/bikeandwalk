from wtforms import Form, BooleanField, StringField, HiddenField, SelectField, IntegerField, validators

    
class CountingLocationForm(Form):
    #ID = HiddenField('ID')
    #countingLocationUID = StringField('Counting Location ID', [validators.DataRequired(),], )
    weather = SelectField("Weather",
        choices=[("","Select Weather Type"),("Fair", "Fair"),("Rainy","Rainy"),("Very Cold", "Very Cold")], )
    countType = SelectField("Count Type", 
        choices=[("Intersection", "Intersection"),("Screen Line","Screen Line")], )
    countEvent_ID = SelectField("Count Event",
        [validators.NumberRange(min=1, message="You must select a count event")], 
        coerce=int, choices=[], )
    user_ID = SelectField("User Name",
        [validators.NumberRange(min=1, message="You must select a someone to count")], 
        coerce=int, choices=[], )
    location_ID = SelectField("Location",
        [validators.NumberRange(min=1, message="You must select a location")], 
        coerce=int, choices=[], )

  
class LocationForm(Form):
    #ID = HiddenField("ID")
    locationName = StringField("Location Name", [validators.DataRequired(),], )
    NS_Street = StringField("North South St.", [validators.DataRequired(),], )
    EW_Street = StringField("East West St.", [validators.DataRequired(),], )
    city = StringField("City", [validators.DataRequired(),], )
    state = StringField("State", [validators.DataRequired(),], )
    latitude = StringField("Latitude",  )
    longitude = StringField("Longitude", )
    #organization_ID = IntegerField("Organization ID", [validators.DataRequired(),], )
