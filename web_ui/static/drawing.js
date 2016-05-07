/**
 * Created by rebryk on 07/05/16.
 */

function drawEventWithButtons(event) {
    return '<tbody id=' + event.id + ' onmouseenter=mouseOver(' + event.id + ')> <tr class=odd id=' + event.id + '>' + drawEventInnerHtmlWithButtons(event) + '</tr>' +
        '<tr id=' + event.id + ' class=even style=display:none> <td colspan="7"> No same events! </td> </tr> </tbody>';
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

function drawEventInnerHtmlWithButtons(event) {
    var html = '<td ondblclick=clickEvent(' + event.id + ')>' + event['pdate'] + '</td>';
    var keys = ["entity1", "action", "entity2"];
    for (key in keys) {
        html += '<td ondblclick=clickEvent(' + event.id + ')>' + event[keys[key]] + '</td>';
    }
    html += '<td ondblclick=clickEvent(' + event.id + ')>' + getHighlightedSentence(event) + '</td>';
    html += '<td ondblclick=clickEvent(' + event.id + ')>' + '<a href="' + event['url'] + '">' + event['url'] + '</a>' + '</td>';

    html += '<td class="buttons">';
    html += '<button class="modify" onclick=modifyEvent(' + event.id + ')>Modify</button>';
    html += '<button class="delete" onclick=deleteEvent(' + event.id + ')>Delete</button>';
    html += '</td>';
    return html;
}

function drawEditEventInnerHtmlWithButtons(event) {
    var html = '<td ondblclick=clickEvent(' + event.id + ')>' + event['pdate'] + '</td>';
    var keys = ["entity1", "action", "entity2"];
    for (var key in keys) {
        html += '<td><textarea>' + event[keys[key]] + '</textarea></td>';
    }
    html += '<td ondblclick=clickEvent(' + event.id + ')>' + event['sentence'] + '</td>';
    html += '<td ondblclick=clickEvent(' + event.id + ')>' + '<a href="' + event['url'] + '">' + event['url'] + '</a>' + '</td>';
    html += '<td class="buttons">';
    html += '<button class="save" onclick=saveEvent(' + event.id + ')>Save</button>';
    html += '<button class="cancel" onclick=cancelEvent(' + event.id + ')>Cancel</button>';
    html += '</td>';
    return html;
}

function drawEventsMerge(event1, event2) {
    return drawEventWithButtons(event1) + drawEventWithButtons(event2);
}
