function openPopup(link) {
    var iframe = document.getElementById("originnews");
    iframe.src = link;
    document.getElementById("popup").style.display = "block";
}

function closePopup() {
    document.getElementById("popup").style.display = "none";
}