var locationSet = false;
if (location.href.substring(location.href.indexOf("#")+1) == location.href) {
	location.href += "#about";
	locationSet = true;
}
if (!locationSet) {
	currentLocation = location.href.split("#");
	location.href = currentLocation[0] + "#" + currentLocation[1];
}
window.addEventListener("hashchange", function(event) {
	window.scrollTo(0, 0);
}, false);