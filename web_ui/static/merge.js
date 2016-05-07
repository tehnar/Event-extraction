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

function joinEventsMerge(id) {
    var joinEntities1 = confirm("Do you want to merge 'Entity1' fields?");
    var joinActions = confirm("Do you want to merge 'Action' fields?");
    var joinEntities2 = confirm("Do you want to merge 'Entity2' fields?");

    $('tbody#' + id).remove();
    $.post($SCRIPT_ROOT + '/_join_events_merge',
        {id: id, joinEntities1: joinEntities1, joinActions: joinActions, joinEntities2: joinEntities2},
        function(data) {
            updateMergingButton();
        });
}


function deleteEventsMerge(id) {
    $('tbody#' + id).remove();
    $.post($SCRIPT_ROOT + '/_delete_events_merge', {id: id},
        function(data) {
            updateMergingButton();
    });
}