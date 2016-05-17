/**
 * Created by rebryk on 07/05/16.
 */

updateMergingButton();
loadEventsMerge();

function loadEventsMerge() {
    $.post($SCRIPT_ROOT + '/_load_events_merge', {}, function(data) {
            var table = document.getElementById("events");
            var events = data.result;
            for (var index in events) {
                table.innerHTML += drawEventsMerge(events[index][0], events[index][1], events[index][2]);
            }
        });
}

function joinEventsMergeAction(id, joinEntities1, joinActions, joinEntities2) {
    $('tbody#' + id).remove();
    $.post($SCRIPT_ROOT + '/_join_events_merge',
        {id: id, joinEntities1: joinEntities1, joinActions: joinActions, joinEntities2: joinEntities2},
        function(data) {
            updateMergingButton();
        });
}

function joinEventsMerge(id) {
    /*
    var joinEntities1 = confirm("Do you want to merge 'Entity1' fields?");
    var joinActions = confirm("Do you want to merge 'Action' fields?");
    var joinEntities2 = confirm("Do you want to merge 'Entity2' fields?");*/
    popupMergeDialog(id);
}

function deleteEventsMerge(id) {
    $('tbody#' + id).remove();
    $.post($SCRIPT_ROOT + '/_delete_events_merge', {id: id},
        function(data) {
            updateMergingButton();
    });
}

$(document).ready(function () {
	$(window).resize(function () {
		if (!$('#dialog-box').is(':hidden')) popup();
	});
});

function popupMergeDialog(id) {
	var maskHeight = $(document).height();
	var maskWidth = $(window).width();

	var dialogTop = (maskHeight/3) - ($('#dialog-box').height());
	var dialogLeft = (maskWidth/2) - ($('#dialog-box').width()/2);

    $('#dialog-entity1').prop("checked", false);
    $('#dialog-action').prop("checked", false);
    $('#dialog-entity2').prop("checked", false);
    $('#dialog-ok').click(function() {
        $('#dialog-overlay, #dialog-box').hide();
        joinEventsMergeAction(id,
            $('#dialog-entity1').is(":checked"),
            $('#dialog-action').is(":checked"),
            $('#dialog-entity2').is(":checked"));
    });

    $('#dialog-overlay').css({height:maskHeight, width:maskWidth}).show();
	$('#dialog-box').css({top:dialogTop, left:dialogLeft}).show();
}