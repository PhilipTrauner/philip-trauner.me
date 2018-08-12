'use strict';

var DEFAULT_PATH= 'about';
var LINK_NODE_NAME = 'A';
var LINK_REGEX = '^\/[^\/]+\/?$';

var contentDivisions = document.querySelectorAll('.content[id]');
var paths = {};
var suppressPopStateEventHandler = false; 

for (var contentId = 0; contentId < contentDivisions.length; contentId++) {
  paths[contentDivisions[contentId].id] = [
    contentDivisions[contentId], 
    document.querySelectorAll(
      'li > a[href="/' + contentDivisions[contentId].id + '"]')[0]
  ];
}

var pathsKeys = Object.keys(paths);

function currentPath() {
  return location.pathname.substring(1);
}

function pathExists(path) {
  return (pathsKeys.indexOf(path) !== -1);
}

function headerSelect(path) {
  paths[path][1].classList = ['header-selected'];

  for (var pathId = 0; pathId < pathsKeys.length; pathId++) {
    if (pathsKeys[pathId] !== path) {
      paths[pathsKeys[pathId]][1].classList = [];
    }
  }
}

function processPath(path, hash) {
  if (!pathExists(path)) {
    path = DEFAULT_PATH; 
  }

  paths[path][0].classList = ['content'];

  for (var pathId = 0; pathId < pathsKeys.length; pathId++) {
    if (pathsKeys[pathId] !== path) {
      paths[pathsKeys[pathId]][0].classList = ['hidden content'];
    }
  }

  headerSelect(path);
  history.pushState(null, null, path);
  if (hash !== undefined) {
    suppressPopStateEventHandler = true; 
    location.hash = hash;
  }
}

processPath(currentPath(), location.hash);

window.addEventListener('click', function(e) {
  var target = e.target;
  if (target.nodeName == LINK_NODE_NAME && 
      target.pathname !== undefined && 
      target.host == location.host &&
      target.pathname.match(LINK_REGEX)) {
    processPath(target.pathname.substring(1), target.hash);
    e.preventDefault();
    e.stopPropagation();
  }
}, false);

window.addEventListener('popstate', function(e) {
  if (!suppressPopStateEventHandler) {
    processPath(currentPath(), location.hash);
  } else {
    suppressPopStateEventHandler = false;
  }
});