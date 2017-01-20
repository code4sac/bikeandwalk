/**
 * Bike And Walk App (BAWA) Map Implementation
 *
 * @param mapboxProjectId
 * @param mapboxAccessToken
 * @param mapDivId
 * @param zoomLevel
 * @constructor
 */
function BAWAMap(mapboxProjectId, mapboxAccessToken, mapDivId, zoomLevel) {
    this.map = L.map(mapDivId, {
        center: [38.551253, -121.488683],
        zoom: zoomLevel
    });

    L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
        attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, ' +
        '<a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
        zoom: zoomLevel,
        id: mapboxProjectId,
        accessToken: mapboxAccessToken
    }).addTo(this.map);

    if (L.markerClusterGroup !== undefined) {
        this.cluster = L.markerClusterGroup();
    }

    this.locations = [];
    this.geocodes = [];
}

BAWAMap.prototype = {
    constructor: BAWAMap,

    /**
     * Add a simple location marker.
     *
     * @param locationName
     * @param latitude
     * @param longitude
     * @param draggable
     */
    addSimpleLocation: function(locationName, latitude, longitude, draggable)  {
        this.pushNewLocation(locationName, latitude, longitude);
        this.setLocationMarkers(true, draggable, false);
    },

    /**
     * Add a Trip location marker.
     *
     * @param locationName
     * @param latitude
     * @param longitude
     * @param tripCount
     */
    addTripLocation: function(locationName, latitude, longitude, tripCount) {
		// Test if there are any locations and if this one exists...
        if (this.locations.length > 0 && this.mapHasMarkerAt(latitude,longitude)){
			// if the location already exists, add count to existing trip
			this.addTripCountToExistingLocation(this.locations[trip], tripCount);
			return;
		}
		// location doesn't exist, so push it to trips
		this.pushNewLocation(locationName, latitude, longitude, tripCount);
    },

	/**
	Add markers using JSON object
	*
	* @param JSON object with all marker data
	* @param url of error response page
	*
	*/
	addMarkersFromJSON: function(data,errorPage){
		var markerData;
		var parseError =false;
		var errorMess = '';
		//console.log('the Data: ' + data);

		try{
			markerData = JSON.parse(data);
		}catch(errorMess){
			alert("err '" + errorMess + "'");
			parseError = true;
		}
		if(!parseError){
			/*
				for each:
					extract and validate data
					if valid data:
						create Marker

				if bbox specified:
					set bounding box
					if zoomLevel specified & >=0:
						set zoom level
					else:
						zoomToFit
				else:
					zoomToFit
			*/
			// create a cluster layer if needed
			if (markerData.cluster === true) {
	            this.map.addLayer(this.cluster);
			}

			for (var i = 0; i < markerData.markers.length; i++) {
			    data = markerData.markers[i]
				if(	data.latitude != undefined && 
					data.longitude != undefined && 
					!this.mapHasMarkerAt(data.latitude,data.longitude)
					){
					this.pushNewLocation(data.locationName, data.latitude, data.longitude)
					// create the marker
					var draggable = (data.draggable == true );
					var options = {"draggable": draggable};
					if (data.divIcon != undefined){
						var divIcon = new L.DivIcon({
					        className: 'divIcon',
					        html: data.divIcon,
							iconSize: new  L.Point(100, 100),
							iconAnchor: new L.Point(20, 80),
							popupAnchor: new L.Point(0, -80),
					    });
						options.icon = divIcon;
					}
					var marker = L.marker([data.latitude, data.longitude],options);
					// Put the maker into the cluster or map layer
					if (markerData.cluster === true) {
			            this.cluster.addLayer(marker);
			        } else { marker.addTo(this.map); }
			
					this.setDragFunction(marker);
					
					if (data.popup != undefined) {
						marker.bindPopup(data.popup);
					} else {
						if(data.locationName != undefined){
							marker.bindPopup(data.locationName);
						} else {
							marker.bindPopup("Unnamed Location");
						}
					
					} // bindPopup
					
				} // Mimimal Data
					
			} // end for
			if (markerData.bbox != undefined){
				alert("Bounding Box not implemented yet.")
				this.zoomToFitAllMarkers();
				/*
				set bounding box
				if zoomLevel specified & >=0:
					(zoom must be > 0 and < 13 {I think})
					set zoom level
				else:
					set max zoom that will show all the markers within the bounding box
					? is this last step needed?
				*/
			} else {
		        if (markerData.zoomToFit === undefined || markerData.zoomToFit != false) {
						this.zoomToFitAllMarkers();
		        }
			}
				
		}else{
			// error parsing JSON data
			// go to error page
			// document.location = errorPage + errorMess + "/";
		}
		// end of addManyLocations()
	},
	

    /**
     * Get and add current geolocation.
     *
     * @param locationName
     * @param latitudeFieldId
     * @param longitudeFieldId
     */
    addCurrentLocation: function(locationName, latitudeFieldId, longitudeFieldId) {
        if (navigator.geolocation) {
            var self = this;

            navigator.geolocation.getCurrentPosition(function(position) {
                // Add the location
                self.addSimpleLocation(locationName, position.coords.latitude, position.coords.longitude, true);

                // Update location input fields
                self.updateFormLocationFields(latitudeFieldId, longitudeFieldId,
                                     position.coords.latitude, position.coords.longitude);

            }, function(error) {
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        console.log("User denied the request for Geolocation.");
                        break;
                    case error.POSITION_UNAVAILABLE:
                        console.log("Location information is unavailable.");
                        break;
                    case error.TIMEOUT:
                        console.log("The request to get user location timed out.");
                        break;
                    case error.UNKNOWN_ERROR:
                        console.log("An unknown error occurred.");
                        break;
                }
            });
        } else {
            console.log("Geolocation is not supported by this browser.");
        }
    },

    /**
     * Push a new location to the locations array.
     * Also pushes the location lat/lon to the geocodes array (used to zoom map to markers).
     *
     * @param locationName
     * @param latitude
     * @param longitude
     * @param tripCount
     */
    pushNewLocation: function(locationName, latitude, longitude, tripCount) {
        this.locations.push(
            {
                locationName: locationName,
                latitude: latitude,
                longitude: longitude,
                tripCount: tripCount
            });

        this.geocodes.push([latitude, longitude]);
    },

	mapHasMarkerAt: function (lat,lng){
	    // Check if trip location already exists
	    for (var trip in this.locations) {
	        if (this.locations.hasOwnProperty(trip)) {
	            if (this.locations[trip].latitude == lat && this.locations[trip].longitude == lng) {
	                // if the location already exists return true
	                return true;
	            }
	        }
	    }
		return false
	},


    /**
     * If the location already exists in the locations array, then just increment the tripCount.
     *
     * @param trip
     * @param tripCount
     */
    addTripCountToExistingLocation: function(trip, tripCount) {
        trip.tripCount += tripCount;
    },

    /**
     * Add the locations to the map as markers.
     *
     * @param zoomToFit
     * @param draggable
     * @param cluster
     */
    setLocationMarkers: function(zoomToFit, draggable, cluster) {
        for (var trip in this.locations) {
            if (this.locations.hasOwnProperty(trip)) {
                this.addLocationMarker(
                    this.locations[trip].locationName,
                    this.locations[trip].latitude,
                    this.locations[trip].longitude,
                    this.locations[trip].tripCount,
                    draggable, cluster);
            }
        }

        if (cluster === true) {
            this.map.addLayer(this.cluster);
        }

        if (zoomToFit === true) {
            this.zoomToFitAllMarkers();
        }
    },

    /**
     * Add a location marker to the map.
     *
     * @param locationName
     * @param latitude
     * @param longitude
     * @param tripCount
     * @param draggable
     * @param cluster
     */
    addLocationMarker: function(locationName, latitude, longitude, tripCount, draggable, cluster) {
        var self = this;

        // Create marker
        var options = {"draggable": draggable === true};
        var marker = L.marker([latitude, longitude], options);
        if (cluster === false) {
            marker.addTo(this.map);
        }
		this.setDragFunction(marker);


        if (locationName !== undefined && locationName !== "") {
            // Create trip marker popup string
            var tripString = "<b>" + locationName + "</b>";
            if (tripCount !== undefined) {
                tripString += "<br>" + "Trip Count: " + tripCount;
            }
            marker.bindPopup(tripString).openPopup();
        }

        if (cluster === true) {
            this.cluster.addLayer(marker);
        }
    },

    /**
     * Zoom the map to fit the location markers.
     */
    zoomToFitAllMarkers: function() {
        var bounds = new L.LatLngBounds(this.geocodes);
        this.map.fitBounds(bounds);
    },
	setDragFunction: function(theMarker){
		var self = this;
		// 'draggable' is in the 'options' object
        if (theMarker.options.draggable === true) {
            // Add drag event handler
            theMarker.on('dragend', function (event) {
                var marker = event.target;
                var position = marker.getLatLng();

                self.updateFormLocationFields("latitude", "longitude", position.lat, position.lng);
            });
		}
    },

    /**
     * Update the location form input fields.
     *
     * @param latitudeFieldId
     * @param longitudeFieldId
     * @param latitude
     * @param longitude
     */
    updateFormLocationFields: function(latitudeFieldId, longitudeFieldId, latitude, longitude) {
        if (latitudeFieldId !== undefined && longitudeFieldId !== undefined) {
			var theID = document.getElementById(latitudeFieldId);
			if(theID != null){theID.value = latitude;}
			theID = document.getElementById(longitudeFieldId);
			if(theID != null){theID.value = longitude;}
			theID = document.getElementById('mapURL');
			if(theID != null){theID.value = "https://www.google.com/maps/place//@"+ latitude +","+ longitude +",17z";}
        }
    }
};
