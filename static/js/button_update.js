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