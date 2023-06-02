var map = new google.maps.Map(document.getElementById('map'), {
    center: {lat: 37.27538, lng: 127.05488},
    zoom: 7
});

function update_marker(latitude, longitude, what){
    const marker = new google.maps.Marker({
    position: {lat: latitude, lng: longitude},
    map: map,
    });

    const infowindow = new google.maps.InfoWindow({
    content: what
    });

    marker.addListener("click", () => {
    infowindow.open({
    anchor: marker,
    map,
    });
    });
}

function update_marker_position() {
  $.getJSON('/update_marker_internal', function(data) { // DB 데이터 값 불러오기
      update_marker(data.latitude, data.longitude, data.what);
  });
}

update_marker_position()