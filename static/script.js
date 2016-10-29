var location_set = false;
if (location.href.substring(location.href.indexOf("#")+1) == location.href) {
	location.href += "#about";
	location_set = true;
}
if (!location_set) {
	current_location = location.href.split("#");
	location.href = current_location[0] + "#" + current_location[1];
}
window.addEventListener("hashchange", function(event) {
	window.scrollTo(0, 0);
}, false);
