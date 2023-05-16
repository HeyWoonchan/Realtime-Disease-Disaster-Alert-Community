$(document).ready(function() {
    $('#updateButton').on('click', function() {
        $.ajax({
            url: '/update_safekorea',
            type: 'POST',
            dataType: 'json',
            success: function(data) {
                $('#contentArea').text(data.content);
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
    $('#newsButton').on('click', function() {
        $.ajax({
            url: '/update_news',
            type: 'POST',
            dataType: 'json',
            success: function(data) {
                $('#newsArea').html(data.content);
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
    $('#newsnaverButton').on('click', function() {
        $.ajax({
            url: '/update_news_naver',
            type: 'POST',
            dataType: 'json',
            success: function(data) {
                $('#newsnaverArea').text(data.content);
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
    $('#apimsgButton').on('click', function() {
        $.ajax({
            url: '/api_disaster_update',
            type: 'POST',
            dataType: 'json',
            success: function(data) {
                $('#apimsgArea').text(JSON.stringify(data));
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
    $('#apimsgButton_db').on('click', function() {
        $.ajax({
            url: '/update_msg_db',
            type: 'POST',
            dataType: 'json',
            success: function(data) {
                $('#apimsgArea_db').text(data.data);
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
});