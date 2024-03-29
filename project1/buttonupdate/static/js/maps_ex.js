var map1;
var map2;

function initMap() {
    // Google Maps 지도 인스턴스 생성 (기본 위치는 임의로 설정합니다. 이후에 수정될 것입니다.)
    map1 = new google.maps.Map(document.getElementById('map'), {
        center: {lat: 37.27538, lng: 127.05488},
        zoom: 2
    });

    // 서버에서 마커 데이터 가져오기
    fetch('/update_external')
    .then(response => response.json())
    .then(data => {
        // 처음 가져온 위치를 맵의 중앙으로 설정합니다.
        if (data.length > 0) {
            map1.setCenter({lat: data[0].latitude, lng: data[0].longitude});
        }

        // 마커 데이터를 반복하여 마커를 추가합니다.
        data.forEach((marker, index) => {
            var position = {lat: marker.latitude, lng: marker.longitude};
            var title = marker.what;

            // 마커를 생성합니다.
            var newMarker = new google.maps.Marker({
                position: position,
                map: map1,
                title: title
            });

            // 마커를 클릭하면 팝업창으로 'what' 정보를 표시합니다.
            var infowindow = new google.maps.InfoWindow({
                content: title
            });

            newMarker.addListener('click', function() {
                infowindow.open(map1, newMarker);
            });

            
            
            infowindow.open(map1, newMarker);
            
        });
    });
}

function initMap2() {
    // Google Maps 지도 인스턴스 생성 (기본 위치는 임의로 설정합니다. 이후에 수정될 것입니다.)
    map2 = new google.maps.Map(document.getElementById('map2'), {
        center: {lat: 37.27538, lng: 127.05488},
        zoom: 2
    });

    // 서버에서 마커 데이터 가져오기
    fetch('/update_worlddisaster')
    .then(response => response.json())
    .then(data => {
        // 처음 가져온 위치를 맵의 중앙으로 설정합니다.
        if (data.length > 0) {
            map2.setCenter({lat: data[0].latitude, lng: data[0].longitude});
        }

        // 마커 데이터를 반복하여 마커를 추가합니다.
        data.forEach((marker, index) => {
            var position = {lat: marker.latitude, lng: marker.longitude};
            var title = marker.what;

            // 마커를 생성합니다.
            var newMarker = new google.maps.Marker({
                position: position,
                map: map2,
                title: title
            });

            // google.maps.event.addListener(marker, 'click', function(i) {        
            //     openPopup(link);
            // });
            
            var infowindow = new google.maps.InfoWindow({
                content: title
            });

            infowindow.open(map2, newMarker);


            // // 첫 번째 마커의 경우, 정보 창을 바로 엽니다.
            // if (index === 0) {
            //     infowindow.open(map, newMarker);
            // }
        });
    });
}


function openPopup(link) {
    var iframe = document.getElementById("exnews");
    iframe.src = link;
    document.getElementById("popup").style.display = "block";
}

function closePopup() {
    document.getElementById("popup").style.display = "none";
}

initMap()
initMap2()