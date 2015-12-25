/* bikeandwalk.js for app */

function confirmRecordDelete(){
	return confirm("Are you sure you want to delete this record?");
}

function orgSwitch(which) {
	location = "/orgSwitch/" + which.options[which.selectedIndex].value + "/"
}

function updateImage(imageSource,imageID) {
	$(imageID).attr("src",imageSource);
}