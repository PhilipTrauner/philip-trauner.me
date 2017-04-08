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

(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
})(window,document,'script','https://www.google-analytics.com/analytics.js','ga');
ga('create', 'UA-38226657-2', 'auto');
ga('send', 'pageview');