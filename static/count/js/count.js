/*
	count.js
	script for Bike and Walk counting page
*/


function startUp(){
	//clearData();
	setLanes();
	setTravelers();
	setUndo();
	hideMenu();
	showCountPage();
	showData();
	uploadData();
	
}

function setUndo(){
	$("#undoCounts").click(function(){undoCounts();}).text("Clear")
	if (lastSaveSet.length > 0){
		$('#undoCounts').text("Undo")
	}
	
}

function undoCounts(){
	clearAll();
	undoTripsWithArray();
	setUndo();
	showData();
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
	lastSaveSet = [];
	setUndo();
}

// end Traveler and Lanes UI
var lastSaveSet = []; // will hold the last set of trips for undo-ing

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
				lastSaveSet = [];
			}
			if (seqNo > 0) lastSaveSet.push(seqNo); // we can't undo without a sequence number
			var y = cnt + "\t" + entryLane + "\t"+  tripTime + "\t" + $("#traveler_"+i).attr("name") + "\t" + seqNo;
			// saveData writes data to localStorage
			saveData(seqNo,y);
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
		for (i=0; i<=localStorage.length-1; i++) {
			key = localStorage.key(i); 
			if (isTripDataKey(key)){
				trips.push(key);  
			}
		}
		for(var i=0; i<trips.length; i++){
			localStorage.removeItem(trips[i])
		}
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
	showTotal(data);
}

function showTotal() {
	var theTotal = 0
	if (hasStorage()){
		for (i=0; i<=localStorage.length-1; i++) {   
	        key = localStorage.key(i); 
			if (isTripDataKey(key)){
				var s = JSON.parse(getJsonTripFrom(localStorage.getItem(key)));
				if (s["count"]){ theTotal += s["count"]};
			}
	    }
		$("#total").text(theTotal);
	} else {
		// get the count someother how...
		$("#total").text("unknown");
	}
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
		// the upload object header
		var dataString = getJsonHeader("add");
		// get each trip data
	
		// create the json string from data lines
		trips = data.split('\n');
		for (var i=0; i<=trips.length-1; i++){
			if (hasData) { dataString += ","};
			if (trips[i] != "") {
				hasData = true;
				dataString += getJsonTripFrom(trips[i]);
			}
		}

		if (hasData){
			dataString += "]}";
			$("pre#data").text('Uploading...')
			$.post("/count/trip/",dataString, function(data){getUploadResult(data);},'json');
		} else {
			// there was no trip data to post
		}
	} else { 
		// no data found 
	}
	
	setTimeout("uploadData()", delayTime) // wait till next upload
} // uploadData()

function undoTripsWithArray() {
	if (lastSaveSet.length > 0) {
		if(hasStorage){
			for(var i=lastSaveSet.length-1; i >= 0; i--){
				var temp = localStorage.getItem(getDataElementBaseKey() + lastSaveSet[i])
				if ((temp != undefined) && (temp != null)) {
					localStorage.removeItem(getDataElementBaseKey() + lastSaveSet[i])
					lastSaveSet = lastSaveSet.slice(0,-1); // remove the last item
				}
			}
		} // delete from local storage
		if (lastSaveSet.length > 0) {
			// some elements were already written to the server or there is no local storage
			// the upload object header
			var dataString = getJsonHeader("undo");
			// create the json string with lastSaveSet array
			var hasData = false;
			for (var i=0; i<=lastSaveSet.length-1; i++){
				if (hasData) dataString += ",";
				hasData = true;
				dataString += '{"seqNo":"'+lastSaveSet[i]+'"}';
			}
			
			if (hasData){
				dataString += "]}";
				$.post("/count/trip/",dataString); // ignore the response from the server
			}
			
			lastSaveSet = []; // just ot be sure
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

function getUploadResult(data){
	// do something about what happened with your data upload
	var result = data['result']
	$("pre#data").text(result)
	if (result.toUpperCase() == "SUCCESS"){
		clearData();
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
