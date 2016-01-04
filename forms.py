from wtforms import Form, BooleanField, StringField, PasswordField, HiddenField, SelectField, validators

    
class CountingLocationForm(Form):
    #ID = HiddenField('ID')
    #countingLocationUID = StringField('Counting Location ID', [validators.DataRequired(),], )
    weather = SelectField("Weather",
        choices=[("","Select Weather Type"),("Fair", "Fair"),("Rainy","Rainy"),("Very Cold", "Very Cold")], )
    countType = SelectField("Count Type", 
        choices=[("Intersection", "Intersections"),("Screen Line","Screen Line")], )
    countEvent_ID = SelectField("Count Event",
        [validators.NumberRange(min=1, message="You must select a count event")], 
        coerce=int, choices=[], )
    user_ID = SelectField("User Name",
        [validators.NumberRange(min=1, message="You must select a someone to count")], 
        coerce=int, choices=[], )
    location_ID = SelectField("Location",
        [validators.NumberRange(min=1, message="You must select a location")], 
        coerce=int, choices=[], )

  