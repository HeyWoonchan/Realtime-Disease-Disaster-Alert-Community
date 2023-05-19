var map = new naver.maps.Map('map', {               //어디를 중심으로 화면에 표시할지
    center: new naver.maps.LatLng(35.95, 128.25), 
    zoom: 0
});

function update_marker(latitude, longitude, what){
    var marker = new naver.maps.Marker({                //마커 표시하는 위치
    position: new naver.maps.LatLng(latitude, longitude),
    map: map,
    // icon: {
    //     url: '../static/marker.png',
    //     size: new naver.maps.Size(50, 52),
    //     origin: new naver.maps.Point(0, 0),
    //     anchor: new naver.maps.Point(25, 26)
    // }
    })

    var infowindow = new naver.maps.InfoWindow({
        content: '<div style="width:100px;text-align:center;padding:10x;font-size:10px"><b>' + what
    });

    naver.maps.Event.addListener(marker, "click", function() {
    if (infowindow.getMap()) {
        infowindow.close();
    } else {
        infowindow.open(map, marker);
    }
});
}

function update_marker_position() {
    $.getJSON('/update_marker', function(data) { // DB 데이터 값 불러오기
        update_marker(data.latitude, data.longitude, data.what);
    });
}

update_marker_position()