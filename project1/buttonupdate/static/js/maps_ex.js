//해외 지도 스크립트
var map = new google.maps.Map(document.getElementById('map'), {
    center: {lat: 0, lng: 0},
    zoom: 2
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
  $.getJSON('/update_external', function(data) { // DB 데이터 값 불러오기
      update_marker(data.latitude, data.longitude, data.what);
      document.getElementById("notice").src = data.link
      iframe_update(data.link, "Ifrm_notice")
  });
  
}

function update_WHOnews() {
    $.getJSON('/update_WHOnews', function(data) { // DB 데이터 값 불러오기
        link_WHO = data.link
        iframe_update(data.link, "Ifrm_WHOnews")
    });

  }

// iframe script
function iframe_update(link, Ifrm) {
    console.log(link);
    document.getElementById(Ifrm).src = link
}

//스크롤 script
function scrollToElement(elementId) {
    var offset = $("#" + elementId).offset();
    $('html, body').animate({ scrollTop: (offset.top - 20) }, 350);
}

//버튼 script
function toggleIframe_notice() {
    var iframeContainer = $("#iframeContainer_notice");
    if (iframeContainer.is(":hidden")) {
        iframeContainer.show();
        scrollToElement("iframeContainer_notice");
    } else {
        iframeContainer.hide();
    }
}

function toggleIframe_WHO() {
    var iframeContainer = $("#iframeContainer_WHO");
    if (iframeContainer.is(":hidden")) {
        window.open(link_WHO)
        iframeContainer.show();
        scrollToElement("iframeContainer_WHO");
    } else {
        iframeContainer.hide();
    }
}
function openPopup() {
    document.getElementById('popup').style.display = 'block';
}

function closePopup() {
    document.getElementById('popup').style.display = 'none';
}
update_marker_position()
update_WHOnews()