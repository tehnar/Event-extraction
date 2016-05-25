/**
 * Created by rebryk on 19/04/16.
 */

// Array Remove - By John Resig (MIT Licensed)
function remove(array, from, to) {
    var rest = array.slice((to || from) + 1 || array.length);
    array.length = from < 0 ? array.length + from : from;
    return array.push.apply(array, rest);
}

function getUrlParameter(sParam) {
    var sPageURL = decodeURIComponent(window.location.search.substring(1)),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');
        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : sParameterName[1];
        }
    }
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
var progressTimer = null;

updateMergingButton();
loadEvents();
fullAutoMerge();

function modifyEvent(id, type) {
    $.post($SCRIPT_ROOT + '/_get_event', {id: id}, function(data) {
        $('tr#' + id + '.' + type).html(drawEditEventInnerHtmlWithButtons(data.result, type));
    });
}

function deleteEvent(id, type) {
    var replace_id = -1;
    $('tbody#' + id).find('tr').each(function() {
        if ($(this).attr('class') == 'even') {
            replace_id = $(this).attr('id');
        }
    });

    removeElement(selected_events, id);
    $('tr#' + id + '.' + type).remove();
    $.post($SCRIPT_ROOT + '/_delete_event', {id: id}, function(data) {
        if (type == 'odd' && replace_id != -1) {
            updateBlock(id, replace_id);
        }
    });
}

function cancelEvent(id, type) {
    $.post($SCRIPT_ROOT + '/_get_event', {id: id}, function(data) {
        $('tr#' + id + '.' + type).html(drawEventInnerHtmlWithButtons(data.result, type));
    });
}

function clickEvent(id, type) {
    if (type == 'even') {
        return;
    }
    var index = find(selected_events, id);
    if (index != -1) {
        remove(selected_events, index);
        cancelEvent(id, type);
    } else {
        selected_events.push(id);
    }
    $('tr#' + id + '.' + type).toggleClass("selected");
}

function joinEventsAction(joinEntities1, joinActions, joinEntities2) {
    $.post($SCRIPT_ROOT + '/_join_events',
        {ids: selected_events, joinEntities1: joinEntities1, joinActions: joinActions, joinEntities2: joinEntities2},
        function() {
            var id = selected_events[0];
            while (selected_events.length > 0) {
                 if (selected_events[0] != id) {
                     $('tbody#' + selected_events[0]).remove();
                 }
                clickEvent(selected_events[0], 'odd');
            }
            updateBlock(id, id);
        });
}

function joinEvents() {
    if (selected_events.length > 1) {
        popupMergeDialog();
    }
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
    $.post($SCRIPT_ROOT + '/_auto_merge', {}, function (data) {});
}

function saveEvent(id, type) {
    var event = $('tr#' + id + '.' + type);
    var children = event.children();
    var entity1 = children[1].firstChild.value;
    var action = children[2].firstChild.value;
    var entity2 = children[3].firstChild.value;

    $.post($SCRIPT_ROOT + '/_modify_event',
        {id: id, entity1: entity1, action: action, entity2: entity2},
        function(data) {
            if (data.error == null) {
                event.html(drawEventInnerHtmlWithButtons(data.result, type));
            } else {
                alert(data.error)
            }
        });
}

function hideRow(id) {
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

function updateBlock(id, new_id) {
    $.post($SCRIPT_ROOT + '/_get_group', {id: new_id}, function(data) {
        var events = data.result;
        $('tbody#' + id).replaceWith(drawEventWithButtons(events));
    });
}

function loadEvents() {
    $.post($SCRIPT_ROOT + '/_load_events', {event_cnt: $('.odd').length, query: getUrlParameter('query')}, function(data) {
            var table = document.getElementById("events");
            var events = data.result;
            for (var index in events) {
                table.innerHTML += drawEventWithButtons(events[index]);
            }
        });
}

$(window).bind('scroll', _.throttle(function() {
    if($(this).scrollTop() + window.innerHeight + 50 >= $("#events").innerHeight()) {
        loadEvents();
    }
}, 200));

$(document).ready(function () {
	$('a.btn-ok, #dialog-ok').click(function () {
		$('#dialog-overlay, #dialog-box').hide();
        joinEventsAction($('#dialog-entity1').is(":checked"),
            $('#dialog-action').is(":checked"),
            $('#dialog-entity2').is(":checked"));
		return false;
	});

	$(window).resize(function () {
		if (!$('#dialog-box').is(':hidden')) popupMergeDialog();
	});
});

function popupMergeDialog() {
	var maskHeight = $(document).height();
	var maskWidth = $(window).width();

	$('#dialog-entity1').prop("checked", false);
    $('#dialog-action').prop("checked", false);
    $('#dialog-entity2').prop("checked", false);

    $('#dialog-overlay').css({height:maskHeight, width:maskWidth}).show();
    $('#dialog-box').show();
}
