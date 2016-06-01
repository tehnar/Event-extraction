/**
 * Created by rebryk on 08/05/16.
 */

updateMergingButton();

var fetchTimer = setInterval(updateFetchInfo, 1000);

function updateFetchInfo() {
    $.post($SCRIPT_ROOT + '/_get_fetch_info', {},
        function (data) {
            $('td.fetch_status').each(function(index) {
                $(this).html("No articles are being downloaded now");
            });
            console.log(data.result);
            for (var key in data.result) {
                var idKey = key;
                idKey = idKey.replace('\.','\\.');
                console.log(key, idKey, data.result[key], $('td#' + idKey).html());
                $('td#' + idKey).html(data.result[key]);
            }
        });
}


function fetchArticles(siteName) {
    $.post($SCRIPT_ROOT + '/_fetch_articles', {site_name: siteName}, function(data) {
    });
}