// いいねボタン
$(document).ready(function(event){
    $(document).on('click', '#like', function(event){
        event.preventDefault();
        var liked = $(this).attr('value');
        $.ajax({
            type: 'POST',
            url: '{% url "favolo:likes" page_accesskey %}',
            data: {'liked': liked, 'csrfmiddlewaretoken': '{{ csrf_token }}'},
            dataType: 'json',
            success: function(response){
                $('#like').html(response['form'])
                console.log($('#like').html(response['form']));
            },
            error: function(rs, e){
                console.log(rs.responseText);
            }
        });
    });
});
