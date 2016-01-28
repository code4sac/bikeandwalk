/**
 * Bike And Walk App (BAWA) Map Implementation
 *
 * @param mapDivId
 * @param zoomLevel
 * @constructor
 */
function BAWAMap(mapDivId, zoomLevel) {
    this.map = L.map(mapDivId, {
        center: [38.551253, -121.488683],
        zoom: zoomLevel
    });

    L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
        attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, ' +
        '<a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
        maxZoom: zoomLevel,
        id: 'jimryan.p0f37ng8',
        accessToken: 'pk.eyJ1IjoiamltcnlhbiIsImEiOiJjaWp4Z2NmZ3QweTk1dmdsejM0NTk3cXZnIn0.BEc764xfxFGOr8HBQvmN7g'
    }).addTo(this.map);

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
     */
    addSimpleLocation: function(locationName, latitude, longitude)  {
        this.pushNewLocation(locationName, latitude, longitude);
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
     */
    setLocationMarkers: function(zoomToFit) {
        for (var trip in this.locations) {
            if (this.locations.hasOwnProperty(trip)) {
                this.addLocationMarker(
                    this.locations[trip].locationName,
                    this.locations[trip].latitude,
                    this.locations[trip].longitude,
                    this.locations[trip].tripCount);
            }
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
     */
    addLocationMarker: function(locationName, latitude, longitude, tripCount) {
        var marker = L.marker([latitude, longitude]).addTo(this.map);

        var tripString = "<b>" + locationName + "</b>";

        if (tripCount !== undefined) {
            tripString += "<br>" + "Trip Count: " + tripCount;
        }

        marker.bindPopup(tripString).openPopup();
    },

    /**
     * Zoom the map to fit the location markers.
     */
    zoomToFitAllMarkers: function() {
        var bounds = new L.LatLngBounds(this.geocodes);
        this.map.fitBounds(bounds);
    }
};
