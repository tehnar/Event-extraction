/**
 * Created by rebryk on 19/04/16.
 */

// Array Remove - By John Resig (MIT Licensed)
function remove(array, from, to) {
    var rest = array.slice((to || from) + 1 || array.length);
    array.length = from < 0 ? array.length + from : from;
    return array.push.apply(array, rest);
}

function find(array, e) {
    for (var i = 0; i < array.length; ++i) {
        if (array[i] == e) {
            return i;
        }
    }
    return -1;
}

function removeElement(array, e) {
    var index = find(array, e);
    if (index != -1) {
        remove(array, index);
    }
}

var selected_events = [];
loadEvents();

function modifyEvent(id) {
    $.post($SCRIPT_ROOT + '/_get_event', {id: id}, function(data) {
        document.getElementById(id).innerHTML= drawEditEventInnerHtml(data.result[0], data.result[1], data.result[2]);
    });
}

function deleteEvent(id) {
    removeElement(selected_events, id);
    document.getElementById(id).remove();
    $.post($SCRIPT_ROOT + '/_delete_event', {id: id}, function(data) {});
}

function cancelEvent(id) {
    $.post($SCRIPT_ROOT + '/_get_event', {id: id}, function(data) {
        document.getElementById(id).innerHTML = drawEventInnerHtml(data.result[0], data.result[1], data.result[2]);
    });
}

function clickEvent(id) {
    var index = find(selected_events, id);
    if (index != -1) {
        remove(selected_events, index);
        document.getElementById(id).setAttribute("class", "");
    } else {
        selected_events.push(id);
        document.getElementById(id).setAttribute("class", "selected");
    }
}

function joinEvents() {
    if (selected_events.length < 2) {
        return;
    }

    var joinEntities1 = confirm("Do you want to merge 'Entity1' fields?");
    var joinActions = confirm("Do you want to merge 'Action' fields?");
    var joinEntities2 = confirm("Do you want to merge 'Entity2' fields?");

    $.post($SCRIPT_ROOT + '/_join_events',
        {ids: selected_events, joinEntities1: joinEntities1, joinActions: joinActions, joinEntities2: joinEntities2},
        function(data) {
            while (selected_events.length > 0) {
                clickEvent(selected_events[0]);
        }
    });
}

function saveEvent(id) {
    var event = document.getElementById(id);
    var entity1 = event.childNodes.item(1).firstChild.value;
    var action = event.childNodes.item(2).firstChild.value;
    var entity2 = event.childNodes.item(3).firstChild.value;
    //var sentence = event.childNodes.item(4).firstChild.value;

    $.post($SCRIPT_ROOT + '/_modify_event',
        {id: id, entity1: entity1, action: action, entity2: entity2},
        function(data) {
            if (data.error == null) {
                event.innerHTML = drawEventInnerHtml(data.result[0], data.result[1], data.result[2]);
            } else {
                alert(data.error)
            }
        });
}

function drawEvent(date, source, event) {
    return '<tr id=' + event.id + '>' + drawEventInnerHtml(date, source, event) + '</tr>';
}

function getSentence(event) {
    var words = (event["sentence"] + " ").replace(/, /g, " , ").replace(/\. /g, " . ").split(" ");

    var colors = ["red", "green", "blue"];
    var keys = ["entity1", "action", "entity2"];
    var data = [[]];
    for (var key in keys) {
        data[key] = event[keys[key]].split(" ");
    }

    for (var key in keys) {
        for (var i in data[key]) {
            for (var word in words) {
                if (words[word] == data[key][i]) {
                    words[word] = '<span class="' + colors[key] +'">' + words[word] + '</span>';
                    break;
                }
            }
        }
    }

    var result = "";
    for (var i in words) {
        if (words[i] == "") {
            continue;
        }
        if (i != 0 && words[i] != ',' && words[i] != '.') {
            result += " ";
        }
        result += words[i];
    }
    return result;
}

function drawEventInnerHtml(date, source, event) {
    var html = '<td onclick=clickEvent(' + event.id + ')>' + date + '</td>';
    //var html = '<td onclick=clickEvent(' + event.id + ')>' + event.id + ' (' + event.event_set + ')</td>';
    event.source = source;
    var keys = ["entity1", "action", "entity2", "source"];
    for (key in keys) {
        html += '<td onclick=clickEvent(' + event.id + ')>' + event[keys[key]] + '</td>';
    }
    html += '<td onclick=clickEvent(' + event.id + ')>' + getSentence(event) + '</td>';

    html += '<td class="buttons">';
    html += '<button class="modify" onclick=modifyEvent(' + event.id + ')>Modify</button>';
    html += '<button class="delete" onclick=deleteEvent(' + event.id + ')>Delete</button>';
    html += '</td>';
    return html;
}

function drawEditEventInnerHtml(date, source, event) {
    var html = '<td onclick=clickEvent(' + event.id + ')>' + date + '</td>';
    //var html = '<td onclick=clickEvent(' + event.id + ')>' + event.id + ' (' + event.event_set + ')</td>';
    event.source = source;
    var keys = ["entity1", "action", "entity2", "source"];
    for (var key in keys) {
        html += '<td><textarea>' + event[keys[key]] + '</textarea></td>';
    }
    html += '<td onclick=clickEvent(' + event.id + ')>' + event['sentence'] + '</td>';
    html += '<td onclick=clickEvent(' + event.id + ')>' + '<a href="' + source + '">' + source + '</a>' + '</td>';
    html += '<td class="buttons">';
    html += '<button class="save" onclick=saveEvent(' + event.id + ')>Save</button>';
    html += '<button class="cancel" onclick=cancelEvent(' + event.id + ')>Cancel</button>';
    html += '</td>';
    return html;
}

function loadEvents() {
    $.post($SCRIPT_ROOT + '/_load_events', {}, function(data) {
            var table = document.getElementById("events");
            var events = data.result;
            for (var index in events) {
                table.innerHTML += drawEvent(events[index][0], events[index][1], events[index][2]);
            }
        });
}

$(window).bind('scroll', _.throttle(function() {
    if($(this).scrollTop() + window.innerHeight + 50 >= $("#events").innerHeight()) {
        loadEvents();
    }
}, 100));
