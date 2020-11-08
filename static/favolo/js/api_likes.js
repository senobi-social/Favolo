// いいねボタン
function api_likes() {
    var api_url = "{% url 'favolo:api_likes' page_accesskey %}";
    var btn = document.getElementById("like"); // HTMLに記述した取得したいid要素を記述する
    var request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (request.readyState === 4 && request.status === 200) {
            var received_data = JSON.parse(request.responseText);
            btn.innerText = received_data.like;
        }
    }
    request.open("GET",api_url);
    request.send();
}
