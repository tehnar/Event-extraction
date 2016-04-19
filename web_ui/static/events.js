/**
 * Created by rebryk on 19/04/16.
 */

loadEvents();

function modifyEvent(id) {
    $.getJSON($SCRIPT_ROOT + '/_get_event', {id: id}, function(data) {
        document.getElementById(id).innerHTML= drawEditEventInnerHtml(data.result[0], data.result[1]);
    });
}

function deleteEvent(id) {
    document.getElementById(id).remove();
    $.getJSON($SCRIPT_ROOT + '/_delete_event', {id: id}, function(data) {});
}

function cancelEvent(id) {
    $.getJSON($SCRIPT_ROOT + '/_get_event', {id: id}, function(data) {
        document.getElementById(id).innerHTML = drawEventInnerHtml(data.result[0], data.result[1]);
    });
}

function saveEvent(id) {
    var event = document.getElementById(id);
    var entity1 = event.childNodes.item(1).firstChild.value;
    var action = event.childNodes.item(2).firstChild.value;
    var entity2 = event.childNodes.item(3).firstChild.value;
    var sentence = event.childNodes.item(4).firstChild.value;

    $.getJSON($SCRIPT_ROOT + '/_modify_event',
        {id: id, entity1: entity1, action: action, entity2: entity2, sentence: sentence},
        function(data) {
            if (data.error == null) {
                event.innerHTML = drawEventInnerHtml(data.result[0], data.result[1]);
            } else {
                alert(data.error)
            }
        });
}

function drawEvent(date, event) {
    return '<tr id=' + event.id + '>' + drawEventInnerHtml(date, event) + '</tr>';
}

function drawEventInnerHtml(date, event) {
    var html = '<td>' + date + '</td>';
    var keys = ["entity1", "action", "entity2", "sentence"];
    for (var key in keys) {
        html += '<td>' + event[keys[key]] + '</td>';
    }
    html += '<td class="buttons">';
    html += '<button class="modify" onclick=modifyEvent(' + event.id + ')>Modify</button>';
    html += '<button class="delete" onclick=deleteEvent(' + event.id + ')>Delete</button>';
    html += '</td>';
    return html;
}

function drawEditEventInnerHtml(date, event) {
    var html = '<td>' + date + '</td>';
    var keys = ["entity1", "action", "entity2", "sentence"];
    for (var key in keys) {
        html += '<td><textarea>' + event[keys[key]] + '</textarea></td>';
    }
    html += '<td class="buttons">';
    html += '<button class="save" onclick=saveEvent(' + event.id + ')>Save</button>';
    html += '<button class="cancel" onclick=cancelEvent(' + event.id + ')>Cancel</button>';
    html += '</td>';
    return html;
}

function loadEvents() {
    $.getJSON($SCRIPT_ROOT + '/_load_events', {}, function(data) {
            var table = document.getElementById("events");
            var events = data.result;
            for (var index in events) {
                table.innerHTML += drawEvent(events[index][0], events[index][1]);
            }
        });
}

$(window).bind('scroll', function() {
    if($(this).scrollTop() + window.innerHeight + 50 >= $("#events").innerHeight()) {
        loadEvents();
    }
});
