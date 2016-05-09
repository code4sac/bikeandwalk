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
        if (this.locations.length == 0) {
            this.pushNewLocation(locationName, latitude, longitude, tripCount)
        } else {
            // Check if trip location already exists
            for (var trip in this.locations) {
                if (this.locations.hasOwnProperty(trip)) {
                    if (this.locations[trip].latitude == latitude && this.locations[trip].longitude == longitude) {
                        // if the location already exists, add count to existing trip
                        this.addTripCountToExistingLocation(this.locations[trip], tripCount);
                        return;
                    }
                }
            }

            // location doesn't exist, so push it to trips
            this.pushNewLocation(locationName, latitude, longitude, tripCount);
        }
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
                map.addSimpleLocation(locationName, position.coords.latitude, position.coords.longitude, true);

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

        if (draggable === true) {
            // Add drag event handler
            marker.on('dragend', function (event) {
                var marker = event.target;
                var position = marker.getLatLng();

                self.updateFormLocationFields("latitude", "longitude", position.lat, position.lng);
            });
        }

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
            document.getElementById(latitudeFieldId).value = latitude;
            document.getElementById(longitudeFieldId).value = longitude;
			// update the url for google maps
			document.getElementById('mapURL').value = "https://www.google.com/maps/place//@"+ latitude +","+ longitude +",17z";
        }
    }
};
