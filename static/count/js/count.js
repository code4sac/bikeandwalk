/*
	count.js
	script for Bike and Walk counting page
*/

var lastTravelerSet = []; // will hold the last set of trips for undo-ing
var lastUploadSet = []; // will hold the sequence numbers of the last set of trips uploaded to the server
var undoTimer;

function startUp(){
	setLanes();
	setTravelers();
	$("#undoCounts").click(function(){undoCounts();});
	setUndo();
	hideMenu();
	showCountPage();
	showData();
	getTotalFromServer();
	uploadData();
	
}

function setUndo(){
	$("#undoCounts").text("Clear")
	if (lastTravelerSet.length > 0){
		$('#undoCounts').text("Undo")
	}
}

function undoCounts(){
	clearAll();
	undoTripsWithArray();
	setUndo();
	showData();
}

function clearUndo(){
	lastTravelerSet = [];
	setUndo();
}

function startUndoTimer(){
	// after a period of time, the "Undo" button changes to "Clear"
	if (undoTimer != undefined) {
		clearTimeout(undoTimer)
	}
	undoTimer = setTimeout(clearUndo,1000*15); // 15 seconds
}

function setLanes() {
	clearLanes();
	$(".entry").click(function(){laneClicked(this);});
}

function setTravelers(){
	$(".traveler").click(function(){travelerClicked(this)});
	clearTravelers();
}

// Traveler and Lanes UI

function clearTravelers() {
	$(".travelerCnt").text("0").hide();
}

function clearAll() {
	clearTravelers();
	clearLanes();
}

function clearLanes() {
	$(".entry").css('background-color','#bcf');
}

function travelerClicked(which){
	var y = "#Cnt_"+which.id;
	var cnt = $(y).text();
	cnt++;
	$(y).text(cnt).show();
	// user can no longer undo the last post
	lastTravelerSet = [];
	setUndo();
}

// end Traveler and Lanes UI

function laneClicked(which){
	var entryLane = which.id;
	var firstPass = true;
	// record the trip(s)...
	
	// compile each traveler type count as tab/return delimited text
	var tripTime = getTripTime(); // local time in ISO format
	$(".traveler").each(function(i){
		var cnt = $("#Cnt_traveler_" + i).text();
		if (cnt + 0 > 0){
			// change the lane color...
			$("#"+which.id).css('background-color','#3f3');
			seqNo = getNextSequenceNumber(); // returns zero if no localStorage
			if (firstPass) {
				firstPass = false;
				lastTravelerSet = [];
			}
			//if (seqNo > 0) lastTravelerSet.push(seqNo); // we can't undo without a sequence number
			if (seqNo > 0) { // we can't undo without a sequence number
				// push a data array into lastTravelerSet
				var undoSet = [seqNo, tripTime];
				lastTravelerSet.push(undoSet); 
			}
			startUndoTimer()
			
			var y = cnt + "\t" + entryLane + "\t"+  tripTime + "\t" + $("#traveler_"+i).attr("data-travelerID") + "\t" + seqNo;
			// saveData writes data to localStorage
			saveData(seqNo,y);
			updateTotal(cnt);
		}
		setUndo();
	})
	
	// use webworker to upload data to host when connection is available
	showData();
	setTimeout("clearAll()", 300) // feedback delay
}

// Data Handling...
/*
  add document.documentURI to storage item name
  to segragate data for different URLs. All localStorage
  data for a domain (example.com) is in the same store. 
*/

// localStorage needs to have a unique name for the storage location
// This uses the complete URI of the page eg: "http://app.bikeandwalk.org/count/12345/"
function getStorageDomain() {return document.documentURI; }

function getDataElementBaseKey() {
	var x = getStorageDomain() + "_data_";
	return getStorageDomain() + "_data_";
}

function saveData(seq,data){
	if(hasStorage()) {
		localStorage.setItem(getDataElementBaseKey()+seq, data);
	} else {
	    // Sorry! No Web Storage support..
		// append this data to any in the data area
		var s = $("pre#data").text();
		if (s.length > 0){
			data = s + '\n' + data
		}
		$("pre#data").text(s + data);
		uploadData();
	}
}

function readAllData(){
	data = "";
	if(hasStorage()) {
		for (i=0; i<=localStorage.length-1; i++)  
		    {   
		        key = localStorage.key(i);  
		 		if (isTripDataKey(key)) {
			        val = localStorage.getItem(key);
					data += val +"\n";
			  	}
		    }
	} else {
	    // Sorry! No Web Storage support..
		data = $("pre#data").text();
	}
	return data;
}

function clearData() {
	// delete all the stored trips
	if(hasStorage()) {
		// order of localStorage items is not defined so,
		// create an array of the keys you want to delete, then delete items
		var trips = new Array();
		var pending = 0
		for (i=0; i<=localStorage.length-1; i++) {
			key = localStorage.key(i); 
			if (isTripDataKey(key)){
				var isinarray = lastUploadSet.indexOf(key.substr(key.indexOf("_data_") + 6));
				if( isinarray >= 0 ){
					// the seqNo of the key must be in the lastUploadSet array
					// this is to avoid deleting a trip that happened between the start of upload and now
					trips.push(key);  
				} else {
					// this trip was not uploaded, it's still pending
					pendingData = JSON.parse(getJsonTripFrom(localStorage.getItem(key)));
					pending += pendingData["count"];
				}
			}
		}
		for(var i=0; i<trips.length; i++){
			localStorage.removeItem(trips[i])
		}
		showPending(pending);
	} else {
		// just clear the data stored in the page
		$("pre#data").text("");
	}
	showData(); // refresh the data list
}

function getNextSequenceNumber() {
	//return the next sequence number for data key
	if(hasStorage()){
		seqKey = getStorageDomain() + "_Sequence_"
		seq = localStorage.getItem(seqKey);
		if (seq === null){
			seq = 0
		}
		seq++
		localStorage.setItem(seqKey,seq);
		return seq;
		
	}else{ return 0 }
}

function showData() {
	var data = readAllData();
	// display the session data in the data div
	$("pre#data").text(data);
	//showTotal(data);
}

function showTotal(theTotal) {
	var theTotal = theTotal || 0
	$("#total").text(theTotal);
}

function showPending(pendingUpload) {
	var pendingUpload = pendingUpload || 0
	$("#pending").text(pendingUpload);
}

function updateTotal(increment){
	var current = parseInt($("#total").text())
	if (isNaN(current)) current = 0;
	var pending = parseInt($("#pending").text())
	if (isNaN(pending)) pending = 0;
	showTotal(current + parseInt(increment));
	showPending(pending + parseInt(increment));
}

function getTotalFromServer(){
	var dataString = getJsonHeader("total");
	dataString += ']}' 
	$.post("/count/trip/",dataString, function(data){handleTotalFromServer(data);},'json');
}

function hasStorage() {
	if(typeof(localStorage) !== "undefined") {
		return true;
	} else {
	    return false
	}	
}

function uploadData() {
	var hasData = false;
	var delayTime = 30000;
	var data = readAllData().trim();
	if (data != ""){
		// so we can delete successfully uploaded records
		lastUploadSet = [];
		
		// the upload object header
		var dataString = getJsonHeader("add");
		// get each trip data
	
		// create the json string from data lines
		trips = data.split('\n');
		for (var i=0; i<=trips.length-1; i++){
			if (hasData) { dataString += ","};
			if (trips[i] != "") {
				hasData = true;
				tripString = getJsonTripFrom(trips[i]);
				tripData = JSON.parse(tripString)
				lastUploadSet.push(tripData["seqNo"])
				dataString += tripString
				//alert(lastUploadSet)
			}
		}

		if (hasData){
			dataString += "]}";
			$("pre#data").text('Uploading...')
			$.post("/count/trip/",dataString, function(data){handleUploadResult(data);},'json');
		} else {
			// there was no trip data to post
		}
	} else { 
		// no data found 
	}
	
	setTimeout("uploadData()", delayTime) // wait till next upload
} // uploadData()

function undoTripsWithArray() {
	if (lastTravelerSet.length > 0) {
		if(hasStorage){
			for(var i=lastTravelerSet.length-1; i >= 0; i--){
				var recKey = getDataElementBaseKey() + lastTravelerSet[i][0]
				var temp = localStorage.getItem(recKey)
				if ((temp != undefined) && (temp != null)) {
					// the trip is still in localStorage
					var trip = getJsonTripFrom(temp);
					trip = JSON.parse(trip);
					updateTotal(parseInt(trip['count']) * -1)
					localStorage.removeItem(recKey)
					lastTravelerSet = lastTravelerSet.slice(0,-1); // remove the last item
				}
			}
		} // delete from local storage
		if (lastTravelerSet.length > 0) {
			// some elements were already written to the server or there is no local storage
			// the upload object header
			var dataString = getJsonHeader("undo");
			// create the json string with lastTravelerSet array
			var hasData = false;
			for (var i=0; i<=lastTravelerSet.length-1; i++){
				if (hasData) dataString += ",";
				hasData = true;
				dataString += '{"seqNo":"'+lastTravelerSet[i][0]+'", "tripDate": "'+lastTravelerSet[i][1]+'"}';
			}
			
			if (hasData){
				dataString += "]}";
				$.post("/count/trip/",dataString, 
				function(data){handleUploadResult(data);},'json'); 
			}
			
			lastTravelerSet = []; // just ot be sure
		} // delete from server
	} // array not empty
}  // undoTripsWithArray()

function getJsonHeader(action){
	action = action || "add";
	return '{"action":"'+action+'", "countEvent":'+ $('#countEvent').val() +', "location":'+ $('#location').val() +', "trips":[';
}

function getJsonTripFrom(val){
	// convert a tab delimted string into a json string
	var s = val.split("\t");
	var aTrip = "";
	if (s.length > 4) {
		aTrip += '{"count":'+s[0];
		aTrip += ',"direction":"'+s[1]+'"';
		aTrip += ',"tripDate":"'+s[2]+'"';
		aTrip += ',"traveler":'+s[3];
		aTrip += ',"seqNo":"'+s[4]+'"';
		aTrip += "}";
	}
	return aTrip;
}

function isTripDataKey(key) {
	if ((key.indexOf('_data_') >= 0) && (key.indexOf(getStorageDomain()) >= 0)){
		return true;
	}
	return false;
}

function handleTotalFromServer(data){
	var total = parseInt(data['total']);
	if(total != undefined ) showTotal(total);
}

function handleUploadResult(data){
	// do something about what happened with your data upload
	var result = data['result'];
	$("pre#data").text(result)
	if (result.toUpperCase() == "SUCCESS"){
		clearData();
		handleTotalFromServer(data)
	} else {
		// some error occured
		$("pre#data").text(result);
	}
}

// End Data handling

/* handle the menu items */
function showMenu(){
	setModal("modalDiv",true);
	$("#modalDiv").click(function() {hideMenu();}).css("z-index","500");
	$("#menuList").css("z-index","1000").show();
}
function hideMenu() {
	setModal("modalDiv",false);
	$("#modalDiv").unbind("click");
	$("#menuList").hide();
}
function showCountPage(){
	$("#countContain").show();
	$("#infoContain").hide();
	hideMenu();
}
function showFormPage(){
	$("#countContain").hide();
	$("#infoContain").show();
	hideMenu();
	
}
function submitReport(){
	alert("Report Submitted!")
	hideMenu();
}

// Paint the screen with a div to simulate a modal dialog
function setModal(objectID,modalState) {
	var objectID = "#"+objectID;
	var docHeight = $(document).height()+"px";
	var docWidth = $(document).width()+"px";
	$(objectID).css("position","absolute").css("top","0").css("left","0");
	if(modalState) {
		// display the div
		$(objectID).css("height",docHeight).css("width",docWidth).show();
	}
	else {
		//hide the div
		docHeight = "1px";
		docWidth = "1px";
		$(objectID).css("height",docHeight).css("width",docWidth).hide();
	}
}


function getTripTime() {
	// format the LOCAL time string into the ISO formatted string that the db expects
    var d = new Date();
    //var n = d.toISOString(); // toISOString always returns UTC time, not ISO formatted local time
	var timeString = (d.getFullYear() + "-");
	timeString += ("0" + (d.getMonth()+1)).substr(-2)+"-"
	timeString += ("0" + d.getDate()).substr(-2)+"T"
	timeString += ("0" + d.getHours()).substr(-2)+":"
	timeString += ("0" + d.getMinutes()).substr(-2)+":"
	timeString += ("0" + d.getSeconds()).substr(-2)
    return timeString;
}

// swap the directional lane markers for Screenline counts
var swapState  = 0;
function swapDirections(leftDirID,rightDirID,leftDirName,rightDirName){
	if(swapState == 1){
		$(leftDirID).insertBefore("#laneSpacer");
		$(leftDirID).removeClass('E_Entry').addClass('W_Entry');
		$(rightDirID).insertAfter("#laneSpacer");
		$(rightDirID).removeClass('W_Entry').addClass('E_Entry');
		$(leftDirName).insertBefore("#dirSpacer");
		$(rightDirName).insertAfter("#dirSpacer");
		swapState = 0;
	} else {
		$(leftDirID).insertAfter("#laneSpacer");
		$(leftDirID).removeClass('W_Entry').addClass('E_Entry');
		$(rightDirID).insertBefore("#laneSpacer");
		$(rightDirID).removeClass('E_Entry').addClass('W_Entry');
		$(leftDirName).insertAfter("#dirSpacer");
		$(rightDirName).insertBefore("#dirSpacer");
		swapState = 1;
	}
}
