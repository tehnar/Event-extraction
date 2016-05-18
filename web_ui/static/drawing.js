/**
 * Created by rebryk on 07/05/16.
 */

function drawEventWithButtons(events) {
    var event = events[0];
    var html = '<tbody id=' + event.id + ' onmouseenter=mouseOver(' + event.id + ')> <tr class=odd id=' + event.id + '>' + drawEventInnerHtmlWithButtons(event, 'odd') + '</tr>';
    if (events.length == 1) {
        //style=display:none
        //html += '<tr id=' + event.id + ' class=even> <td colspan="7"> No same events! </td></tr>';
    } else {
        for (var i = 1; i < events.length; ++i) {
            html += '<tr id=' + events[i].id + ' class=even>' + drawEventInnerHtmlWithButtons(events[i], 'even') + '</tr>';
        }
    }
    html += '</tbody>';
    return html;
}

function updateMergingButton() {
    $.post($SCRIPT_ROOT + '/_get_events_merge_count', {}, function(data) {
        var text = "Merging";
        if (data.result > 0) {
            text += ' (' + data.result + ')';
        }
        document.getElementById("merging").textContent = text;
    });
}

function getHighlightedSentence(event) {
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
                    if (key == 0) {
                        words[word] = '<a class="' + colors[key] + '" onclick=search("' + words[word] + '")>' + words[word] + '</a>';
                    } else {
                        words[word] = '<span class="' + colors[key] + '">' + words[word] + '</span>';
                    }
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

function drawEventInnerHtmlWithoutButtons(event, type) {
    var html = '<td ondblclick=clickEvent(' + event.id + ',"' + type + '")>' + event['pdate'] + '</td>';
    var keys = ["entity1", "action", "entity2"];
    for (key in keys) {
        html += '<td ondblclick=clickEvent(' + event.id + ',"' + type + '")>' + event['main_' + keys[key]] + '</td>';
    }
    html += '<td ondblclick=clickEvent(' + event.id + ',"' + type + '")>' + getHighlightedSentence(event) + '</td>';
    html += '<td ondblclick=clickEvent(' + event.id + ',"' + type + '")>' + '<a href="' + event['url'] + '">' + event['url'] + '</a>' + '</td>';
    return html;
}

function drawEventInnerHtmlWithButtons(event, type) {
    var html = drawEventInnerHtmlWithoutButtons(event, type);
    html += '<td class="buttons">';
    html += '<button class="modify" onclick=modifyEvent(' + event.id + ',"' + type + '")>Modify</button>';
    html += '<button class="delete" onclick=deleteEvent(' + event.id + ',"' + type + '")>Delete</button>';
    html += '</td>';
    return html;
}

function drawEditEventInnerHtmlWithButtons(event, type) {
    var html = '<td ondblclick=clickEvent(' + event.id + ',"' + type + '")>' + event['pdate'] + '</td>';
    var keys = ["entity1", "action", "entity2"];
    for (var key in keys) {
        html += '<td><textarea>' + event[keys[key]] + '</textarea></td>';
    }
    html += '<td ondblclick=clickEvent(' + event.id + ',"' + type + '")>' + event['sentence'] + '</td>';
    html += '<td ondblclick=clickEvent(' + event.id + ',"' + type + '")>' + '<a href="' + event['url'] + '">' + event['url'] + '</a>' + '</td>';
    html += '<td class="buttons">';
    html += '<button class="save" onclick=saveEvent(' + event.id + ',"' + type + '")>Save</button>';
    html += '<button class="cancel" onclick=cancelEvent(' + event.id + ',"' + type + '")>Cancel</button>';
    html += '</td>';
    return html;
}

function drawEventWithoutButtons(event) {
    return '<tr class=odd id=' + event.id + '>' + drawEventInnerHtmlWithoutButtons(event) + '</tr>';
}

function drawEventsMerge(id, event1, event2) {
    var html = '<tbody id=' + id + '><tr class="odd"><td><span class="block">' + event1['pdate'] + '</span><span class="block">' + event2['pdate'] + '</span></td>';
    var keys = ["entity1", "action", "entity2"];
    for (key in keys) {
        html += '<td><span class="block">' + event1[keys[key]] + '</span><span class="block">' + event2[keys[key]] + '</span></td>';
    }
    html += '<td><span class="block">' + getHighlightedSentence(event1) + '</span><span class="block">' + getHighlightedSentence(event2) + '</span></td>';
    html += '<td><span class="block"><a href="' + event1['url'] + '">' + event1['url'] + '</a></span><span class="block"><a href="' + event2['url'] + '">' + event2['url'] + '</a></span></td>';
    html += '<td class="buttons">';
    html += '<button class="save" onclick=joinEventsMerge(' + id + ')>Merge</button>';
    html += '<button class="cancel" onclick=deleteEventsMerge(' + id + ')>Cancel</button>';
    html += '</td></tr></tbody>';
    return html;
}
