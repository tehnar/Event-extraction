/**
 * Created by rebryk on 07/05/16.
 */

loadEventsMerge();

function loadEventsMerge() {
    $.post($SCRIPT_ROOT + '/_load_events_merge', {}, function(data) {
            var table = document.getElementById("events");
            var events = data.result;
            for (var index in events) {
                table.innerHTML += drawEventsMerge(events[index][0], events[index][1]);
            }
        });
}