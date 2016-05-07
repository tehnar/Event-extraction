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
var progressTime = null;
loadEvents();

function modifyEvent(id) {
    $.post($SCRIPT_ROOT + '/_get_event', {id: id}, function(data) {
        $('tr#' + id + '.odd').html(drawEditEventInnerHtml(data.result[0], data.result[1], data.result[2]));
    });
}

function deleteEvent(id) {
    removeElement(selected_events, id);
    $('tbody#' + id).remove();
    //$('tr#' + id + '.even').remove();
    $.post($SCRIPT_ROOT + '/_delete_event', {id: id}, function(data) {});
}

function cancelEvent(id) {
    $.post($SCRIPT_ROOT + '/_get_event', {id: id}, function(data) {
        $('tr#' + id + '.odd').html(drawEventInnerHtml(data.result[0], data.result[1], data.result[2]));
    });
}

function clickEvent(id) {
    var index = find(selected_events, id);
    if (index != -1) {
        remove(selected_events, index);
    } else {
        selected_events.push(id);
    }
    $('tr#' + id + '.odd').toggleClass("selected");
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

function updateProgressBar() {
    $.post($SCRIPT_ROOT + '/_get_merge_progress', {},
        function (data) {
            var progress = data.result;
            document.getElementById("progress_bar").value = progress;
            if (progress == 100) {
                clearInterval(progressTimer);
                progressTimer = null;
                document.getElementById("progress_bar").value = 0;
            }
        });
}

function fullAutoMerge() {
    progressTimer = setInterval(updateProgressBar, 1000);
    $.post($SCRIPT_ROOT + '/_full_auto_merge', {}, function(data) {});
}

function saveEvent(id) {
    //var event = document.getElementById(id);
    var event = $('tr#' + id + '.odd');
    var children = event.children();
    var entity1 = children[1].firstChild.value;
    var action = children[2].firstChild.value;
    var entity2 = children[3].firstChild.value;
    //var sentence = event.childNodes.item(4).firstChild.value;

    $.post($SCRIPT_ROOT + '/_modify_event',
        {id: id, entity1: entity1, action: action, entity2: entity2},
        function(data) {
            if (data.error == null) {
                event.html(drawEventInnerHtml(data.result[0], data.result[1], data.result[2]));
            } else {
                alert(data.error)
            }
        });
}

function hideRow(id) {
    $('tr#' + id + '.even').toggle();
    var row = $('tbody#' + id);
    row.off("mouseleave").mouseleave(function() {});
    row.off("mouseenter").mouseenter(function() {
        mouseOver(id);
    });
}

function expandRow(id) {
    var row = $('tbody#' + id);
    row.mouseleave();
    row.off("mouseenter").mouseenter(function(){});
    row.off("mouseleave").mouseleave(function() {
        hideRow(id);
    });
    $('tr#' + id + '.even').toggle();
}

function mouseOver(id) {
    var row = $('tbody#' + id);
    row.mouseleave();
    timeout = setTimeout(function() {
        expandRow(id);
    }, 1000);

    row.off("mouseleave").mouseleave(function() {
        clearTimeout(timeout);
    });
}

function drawEvent(date, source, event) {
    return '<tbody id=' + event.id + ' onmouseenter=mouseOver(' + event.id + ')> <tr class=odd id=' + event.id + '>' + drawEventInnerHtml(date, source, event) + '</tr>' + 
        '<tr id=' + event.id + ' class=even style=display:none> <td colspan="7"> No same events! </td> </tr> </tbody>';
}

function getSentence(event) {
    var words = (event["sentence"]).replace(/[^\w\s]|_/g, function ($1) { return ' ' + $1 + ' ';}).split(/[ ]+/g);

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
    var skipSpace = true;
    for (var i = 0; i < words.length; ++i) {
        if (!skipSpace && !(/^[\/.,'’”:;^!?%+)\]\}]/.test(words[i]))) {
            result += " ";
        }
        result += words[i];

        skipSpace = /^[\/$'.’“(\[\{]/.test(words[i]);
    }
    return result;
}

function drawEventInnerHtml(date, source, event) {
    var html = '<td ondblclick=clickEvent(' + event.id + ')>' + date + '</td>';
    //var html = '<td onclick=clickEvent(' + event.id + ')>' + event.id + ' (' + event.event_set + ')</td>';
    var keys = ["entity1", "action", "entity2"];
    for (key in keys) {
        html += '<td ondblclick=clickEvent(' + event.id + ')>' + event[keys[key]] + '</td>';
    }
    html += '<td ondblclick=clickEvent(' + event.id + ')>' + getSentence(event) + '</td>';
    html += '<td ondblclick=clickEvent(' + event.id + ')>' + '<a href="' + source + '">' + source + '</a>' + '</td>';

    html += '<td class="buttons">';
    html += '<button class="modify" onclick=modifyEvent(' + event.id + ')>Modify</button>';
    html += '<button class="delete" onclick=deleteEvent(' + event.id + ')>Delete</button>';
    html += '</td>';
    return html;
}

function drawEditEventInnerHtml(date, source, event) {
    var html = '<td ondblclick=clickEvent(' + event.id + ')>' + date + '</td>';
    //var html = '<td onclick=clickEvent(' + event.id + ')>' + event.id + ' (' + event.event_set + ')</td>';
    var keys = ["entity1", "action", "entity2"];
    for (var key in keys) {
        html += '<td><textarea>' + event[keys[key]] + '</textarea></td>';
    }
    html += '<td ondblclick=clickEvent(' + event.id + ')>' + event['sentence'] + '</td>';
    html += '<td ondblclick=clickEvent(' + event.id + ')>' + '<a href="' + source + '">' + source + '</a>' + '</td>';
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
