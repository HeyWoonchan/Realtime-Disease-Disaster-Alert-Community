var locations = {};
var map;
function initMap() {
    // Google Maps 지도 인스턴스 생성 (기본 위치는 임의로 설정합니다. 이후에 수정될 것입니다.)
    map = new google.maps.Map(document.getElementById('map'), {
        center: {lat: 37.27538, lng: 127.05488},
        zoom: 10
    });

    // 서버에서 마커 데이터 가져오기
    fetch('/update_marker_internal')
    .then(response => response.json())
    .then(data => {
        // 처음 가져온 위치를 맵의 중앙으로 설정합니다.
        if (data.length > 0) {
            map.setCenter({lat: data[0].latitude, lng: data[0].longitude});
        }

        // 마커 데이터를 반복하여 마커를 추가합니다.
        data.forEach((marker, index) => {
            var position = {lat: marker.latitude, lng: marker.longitude};
            var title = marker.what;
        
            // 위치 정보를 locations 객체에 저장합니다.
            locations[index] = position;
        
            // 마커를 생성합니다.
            var newMarker = new google.maps.Marker({
                position: position,
                map: map,
                title: title
            });
        
            // 마커를 클릭하면 팝업창으로 'what' 정보를 표시합니다.
            var infowindow = new google.maps.InfoWindow({
                content: title
            });
        
            newMarker.addListener('click', function() {
                infowindow.open(map, newMarker);
            });
        
            // 첫 번째 마커의 경우, 정보 창을 바로 엽니다.
            if (index === 0) {
                infowindow.open(map, newMarker);
            }
        });
    });
}

function moveToLocation(id) {
    var location = locations[id];
    if (location) {
        map.panTo(location);
    }
}

document.getElementById("toggle-button").addEventListener("click", function() {
    var sidebar = document.getElementById("sidebar-popup");
    var button = document.getElementById("toggle-button");
    var rect = button.getBoundingClientRect();
    sidebar.style.top = rect.bottom + "px";
    sidebar.style.left = rect.left + "px";
    
    if (sidebar.classList.contains("hidden")) {
        sidebar.classList.remove("hidden");
    } else {
        sidebar.classList.add("hidden");
    }
});

let isExpanded = false;

function displayComments(comments, limit) {
    let commentList = document.getElementById('commentList');
    commentList.innerHTML = '';

    for (let i = 0; i < Math.min(limit, comments.length); i++) {
        let comment = comments[i];
        commentList.innerHTML += `<li>${comment[1]}: ${comment[2]}</li>`;
    }
}

function toggleCard() {
    if (!isExpanded) {
        displayComments(comments, 10);
        commentList.innerHTML += '<form method="POST" action="/" onclick="event.stopPropagation();"><input type="text" name="name" placeholder="이름"><br><textarea name="comment" placeholder="댓글"></textarea><br><input type="submit" value="등록"></form>';
        isExpanded = true;
    } else {
        displayComments(comments, 4);
        isExpanded = false;
    }
}

// 처음에는 4개의 댓글만 표시
displayComments(comments, 4);
