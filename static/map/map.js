
function createMap() {
    // todo - this is a test placeholder

    // initialize the map on the "map" div with a given center and zoom
    var map = L.map('map', {
        center: [38.551253, -121.488683],
        zoom: 13
    });

    L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
        attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, ' +
            '<a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
        maxZoom: 18,
        id: 'jimryan.p0f37ng8',
        accessToken: 'pk.eyJ1IjoiamltcnlhbiIsImEiOiJjaWp4Z2NmZ3QweTk1dmdsejM0NTk3cXZnIn0.BEc764xfxFGOr8HBQvmN7g'
    }).addTo(map);
}
