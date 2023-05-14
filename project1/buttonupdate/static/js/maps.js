var map = new naver.maps.Map('map', {               //어디를 중심으로 화면에 표시할지
    center: new naver.maps.LatLng(35.95, 128.25), 
    zoom: 0
});

var marker = new naver.maps.Marker({                //마커 표시하는 위치
    position: new naver.maps.LatLng(37.5112, 127.0981),
    map: map})
