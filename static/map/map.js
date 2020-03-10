/**
 * Bike And Walk App (BAWA) Map Implementation
 *
 * @param mapboxProjectId
 * @param mapboxAccessToken
 * @param mapDivId
 * @param flowMarkerMinZoom
 * @constructor
 */
	
function BAWAMap(mapboxProjectId, mapboxAccessToken, mapDivId, flowMarkerMinZoom) {
	// create a layerGroup each for pushpin and canvas markers
	this.pushPinLayer = new L.LayerGroup();
	this.canvasLayer = new L.LayerGroup();
	if(flowMarkerMinZoom == undefined){
	    flowMarkerMinZoom = 15;
	}
	initialZoom = 2;
    this.map = L.map(mapDivId, {
        center: [43.551253, -121.488683],
        zoom: initialZoom,
        flowMarkerMinZoom: flowMarkerMinZoom
    });
	
    // L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
    //     attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, ' +
    //     '<a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
    //     zoom: this.map.options.zoom,
    //     id: mapboxProjectId,
    //     accessToken: mapboxAccessToken
    // }).addTo(this.map);
    
    // map box v8 3/10/20
    L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}', {
        attribution: '© <a href="https://www.mapbox.com/about/maps/">Mapbox</a> © <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> <strong><a href="https://www.mapbox.com/map-feedback/" target="_blank">Improve this map</a></strong>',
        tileSize: 512,
        zoom: this.map.options.zoom,
        zoomOffset: -1,
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
		var options = {};
 		options.draggable = draggable;

 		var marker = L.marker([latitude, longitude],options);
 		marker.addTo(this.map);
 		marker.bindPopup(locationName);
		this.zoomToFitAllMarkers();
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
			
			for (var i = 0; i < markerData.markers.length; i++) {
			    data = markerData.markers[i]
				if(	data.latitude != undefined && 
					data.longitude != undefined && 
					!this.mapHasMarkerAt(data.latitude,data.longitude)
					){
					this.pushNewLocation(data.locationName, data.latitude, data.longitude)
					//var pushPinMarker = this.makePushpinMarker(data);
					//var canvasMarker = this.makeCanvasMarker(data);
					// create the push pin marker
					
					var options = {};
					var draggable = false;
					if (data.draggable != undefined){
						draggable = (data.draggable == true );
					}
					options.draggable = draggable;
					
					var marker = L.marker([data.latitude, data.longitude],options);
					
					this.setDragFunction(marker);
					
					popper = "Unnamed Location"
					if (data.popup != undefined) {
						popper = data.popup;
					} else {
						if(data.locationName != undefined){
							popper = data.locationName;
						}
					
					} // bindPopup
					marker.bindPopup(popper);
					
					if (data.divIcon != undefined){
						var divIcon = new L.DivIcon({
					        className: 'divIcon',
					        html: data.divIcon,
							iconAnchor: new L.Point(20, 80),
							popupAnchor: new L.Point(0, -80),
					    });
    					marker.options.icon = divIcon;
					}
					// Put the maker into the cluster layer if reqested
					if (markerData.cluster === true) {
			            this.cluster.addLayer(marker);
			        } 
					// add the marker (layer) to the pushPinLayer LayerGroup
					this.pushPinLayer.addLayer(marker);
					if(data.flowData != undefined){
						// draw marker with canvas
    					/*
    					data.flowData = {
    								"south":{"inbound":0.8, "outbound":0.8, "heading": 10},
    								"west":{"inbound":0.5,"outbound":0.5, "heading": 10},
    								"north":{"inbound":0.25,"outbound":0.15, "heading": 10},
    								"east":{"inbound":0.1,"outbound":0.2, "heading": 10}
    								}
    					*/			
						var marker2 = L.flowMarker([data.latitude, data.longitude],options,data.flowData);
						//marker2.bindTooltip("110", { permanent: true, direction: "top","offset": [35,-55] });
					} else {
						// use the standard icon
						var marker2 = marker;
					}
					
					marker2.bindPopup(popper);
					this.canvasLayer.addLayer(marker2);
					
				} // Have minimal Data
					
			} // end for: all markers created

			if (markerData.cluster === true) {
				this.pushPinLayer = this.cluster;
			}
			this.setZoomFunction(this.map,this.pushPinLayer,this.canvasLayer);
			//this.map.setZoom(initialZoom-1);
            
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
		        } else {
		            // Show the whole world
					this.map.fitWorld();
		        }
			}
				
		}else{
			// error parsing JSON data
			// go to error page
			document.location = errorPage + errorMess + "/";
		}
		// end of addMarkersFromJSON()
	},
	

    /**
     * Get and add current geolocation.
     *
     * @param locationName
     * @param latitudeFieldId
     * @param longitudeFieldId
     */
    addCurrentLocation: function(locationName, defaultLat, defaultLng, latitudeFieldId, longitudeFieldId, NSheadingFieldID, EWheadingFieldID) {
        if (navigator.geolocation) {
            var self = this;

            navigator.geolocation.getCurrentPosition(function(position) {
                // Add the location
                //self.addSimpleLocation(locationName, position.coords.latitude, position.coords.longitude, true);
								var NSheading = 0;
								var EWheading = 90;
                self.addLocationMarker(locationName, position.coords.latitude, position.coords.longitude, NSheading, EWheading);

                // Update location input fields
                self.updateFormLocationFields(latitudeFieldId, longitudeFieldId,
                                     position.coords.latitude, position.coords.longitude, NSheadingFieldID, EWheadingFieldID, NSheading, EWheading);

            }, self.setDefaultLocation(locationName, defaultLat, defaultLng, latitudeFieldId, longitudeFieldId, NSheadingFieldID, EWheadingFieldID));
        } else {
            console.log("Geolocation is not supported by this browser.");
						self.setDefaultLocation(locationName, defaultLat, defaultLng, latitudeFieldId, longitudeFieldId, NSheadingFieldID, EWheadingFieldID);
        }
    },

		setDefaultLocation: function(locationName, defaultLat, defaultLng, latitudeFieldId, longitudeFieldId, NSheadingFieldID, EWheadingFieldID){
			// set a default location if geolocation is not available
      console.log("Setting default locaiton.");
			var self = this;
			// Davis Bike Hall of Fame
			//var lng = -121.74439430236818;
			//var lat = 38.54422161206573;
			var NSheading = 0;
			var EWheading = 90;
			//alert("Could not determine your current location, so we placed a marker at the default location");
      self.addLocationMarker(locationName, defaultLat, defaultLng, NSheading, EWheading);
      // Update location input fields
      self.updateFormLocationFields(latitudeFieldId, longitudeFieldId,
                          defaultLat, defaultLng, NSheadingFieldID, EWheadingFieldID, NSheading, EWheading);
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
     
     Feb 7, 2017 BL
     This fuction now creates a 4 legged marker used when editing a location record
     The marker can be aligned with the map to set the headings for the streets
     */
     
     lastLocationMarker: undefined,
     
    //addLocationMarker: function(locationName, latitude, longitude, tripCount, draggable, cluster) {
    addLocationMarker: function(locationName, latitude, longitude, northHeading, eastHeading) {
        //distroy the old marker if one exists
        if(this.lastLocationMarker != undefined){
            this.lastLocationMarker.remove();
            this.lastLocationMarker = undefined;
        }
        // Create marker
        var options = {draggable: true};
        var marker = L.alignmentMarker([latitude, longitude],options,northHeading,eastHeading)
        marker.addTo(this.map);
    	this.setDragFunction(marker);
        this.lastLocationMarker = marker;

        var position = marker.getLatLng();
        this.updateFormLocationFields("latitude", "longitude", position.lat, position.lng);


        if (locationName !== undefined && locationName !== "") {
            // Create trip marker popup string
            var tripString = "<b>" + locationName + "</b>";
            marker.bindPopup(tripString);
        }
        
        this.map.fitBounds([marker.getLatLng()]);
        return marker;
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
	setZoomFunction: function(theMap,clusterLayer,canvasLayer){
		if(theMap != undefined){
			theMap.on("zoomend", function (event) {
				var theZoom = theMap.getZoom()
				if (theZoom > this.options.flowMarkerMinZoom) {
					clusterLayer.remove();
					canvasLayer.addTo(theMap);
				} else {
					canvasLayer.remove();
					clusterLayer.addTo(theMap);
				}
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
     * @param NSheadingFieldID
     * @param EWheadingFieldID
     * @param NSheading
     * @param EWheading
     */

    updateFormLocationFields: function(latitudeFieldId, longitudeFieldId, latitude, longitude, NSheadingFieldID, EWheadingFieldID, NSheading, EWheading) {
        if (latitudeFieldId !== undefined && longitudeFieldId !== undefined) {
			var theID = document.getElementById(latitudeFieldId);
			if(theID != null){theID.value = latitude;}
			theID = document.getElementById(longitudeFieldId);
			if(theID != null){theID.value = longitude;}
			theID = document.getElementById(NSheadingFieldID);
			if(theID != null){theID.value = NSheading;}
			theID = document.getElementById(EWheadingFieldID);
			if(theID != null){theID.value = EWheading;}
			theID = document.getElementById('mapURL');
			if(theID != null){theID.value = "https://www.google.com/maps/place//@"+ latitude +","+ longitude +",17z";}
        }
    }

};

