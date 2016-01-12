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

function submitModalForm(formID, postingURL, successTarget, successURL){
	$("#modal-form").load(postingURL,formToJson(formID),function(data){
		if (data == "success"){
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


function loadAssignmentList(data, target, successURL){
	if (data == "success"){
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