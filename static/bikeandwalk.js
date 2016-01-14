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

function locationItemClicked(target, loc){
	$('.location-item').css('background-color','white');
	$('#location_ID').attr('value',loc);
	$(target).css('background-color','#333');
}

function editAssignmentFromList(editFormURL) {
	setModal('dialog',true);
	$('#modal-form-contain').show();
	$('#modal-form').show();
	$('#modal-form').load(editFormURL)
}

function modalFormSuccess(data){
	// return true if the update was successful
	// also return true if the update failed for a reason
	// other than a validation error
	var result = true;
	if ((data == "success") || (data.substr(0,9) == 'failure: ')){
		if (data != "success"){ 
			// display an error message
			alert(data.substr(9)) 
		}
	} else { result = false; }
	return result;
}

function submitModalForm(formID, postingURL, successTarget, successURL){
	$("#modal-form").load(postingURL,formToJson(formID),function(data){
		if (modalFormSuccess(data)){
			cancelModalForm();
			$("#"+successTarget).load(successURL);
		} else {
			// there were errors, so the form will redisplay
		}
	}
	,"html");
}

function formToJson(formID){
	var raw = $("#"+formID).serializeArray();
	var obj = {};
	jQuery.each( raw, function( i, field ) { 
		if (obj[field.name] !== undefined) {
			if (!obj[field.name].push) {
				obj[field.name] = [obj[field.name]];
			}
			obj[field.name].push(field.value || '');
		} else {
			obj[field.name] = field.value || '';
		}
		
	});
	return obj;
}

function deleteAssignmentFromList(deleteActionURL, successTarget){
	if (confirmRecordDelete()) {
		$.get(deleteActionURL, function(data){
		if(data == "success"){
			$("#"+successTarget).text('').hide();
		} else {
			alert(data)
		}
	})
	}
}
function loadAssignmentList(data, target, successURL){
	if (modalFormSuccess(data)){
		cancelModalForm();
		$(target).load(successURL);
	}else {
	// the form is (re-)displayed in modal-form div
	}
}

function cancelModalForm(){
	setModal("dialog",false);
	$("#modal-form, #modal-form-contain").hide();
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