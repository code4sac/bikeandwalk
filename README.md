# The Bike and Walk Project

The goal of this project is to create an on-line traffic counting tool to aid groups promoting 
active transportation in their communities. We hope that it will provide a convenient way 
to collect, store and share traffic count information.

All of the count data is centrally stored and is immediately available via the internet for viewing,
download and analysis by anyone. The count data is geocoded so it is possible to compare data from different 
locations and to compare the information collected by the organizations that are using the system.

The whole system is web based and so requires no download. The "client" application is designed
primarily for use on a smart phone or tablet but ought to work fine with any (modern) device that can connect
to the internet. 

An internet connection is _**not**_ required when counting. Users who may be counting in remote locations can
do so without a connection to the internet. Later, when a connection is available, their count data will be uploaded 
to the central data bank. (For the technically inclined, we're using localStorage for this.)

The instructions on [using the system for counting](http://bikeandwalk.org/help/counting/) may give you a
better idea of how it works from the stand point of the people in the field.

If you'd like to try it out yourself, the link that follows will let you play around with it. 
Still not quite the final appearance
but functional: [app.bikeandwalk.org/count/10fe1c1603416a0d9ee6d958026acd57/](http://app.bikeandwalk.org/count/10fe1c1603416a0d9ee6d958026acd57/)

## Administration
Administration of the system and its data is divided into two components. System administration is handled by the
core team. Count Administration is handled by the local organizations.

The roles are as follows:

### System Administration
* Creating and maintaining the records related to the Organizations using the system
* Creating and maintaining the "Traveler" records.  
Travelers are what we call the things that we count.
A Traveler can represent a number of aspects of the person being counted. For example:
	* A Traveler may represent a person riding a bike or a person walking. 
	* Travelers may also represent behaviors such as wrong way riding or walking in the roadway. 
	* Each organization participating in the system is free to choose whichever Travelers they are interested
	in documenting for their count. 
	* If an organization would like to count something for which there isn't a Traveler type, the system admins
	will collaborate with them to create one. 
	
### Count Administration
* The actual counting activity is carried out by the various organizations that use the system. Count Administrators
determine:
	* When the count will be held.
	* Where the counters will be stationed.
	* Who will be counting and at which location.
	* Communication with counters to ensure that all counts are completed and uploaded to the data bank.
	
Additional information on the project is available at [BikeAndWalk.org](http://bikeandwalk.org/).

## Technical Details

This is an open source project written primarily in Python with the Flask web framework.

Additional dependencies include:

* SQLAlchemy
* Flask Mail
* WTForms
* Leaflet.js
* jQuery (of course)