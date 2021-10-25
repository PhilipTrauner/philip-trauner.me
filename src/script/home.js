'use strict';

var DEFAULT_PATH = 'about';
var LINK_NODE_NAME = 'A';
var LINK_REGEX = '^\/[^\/]+\/?$';

var contentDivisions = document.querySelectorAll('.fragment[id]');
var paths = {};
var suppressPopStateEventHandler = false;
var initialLoad = true;

for (var contentId = 0; contentId < contentDivisions.length; contentId++) {
  var navElement = document.querySelectorAll(
    'li > a[href="/' + contentDivisions[contentId].id + '"]')[0];

  paths[contentDivisions[contentId].id] = [
    contentDivisions[contentId],
    navElement,
    navElement.innerHTML
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

function processPath(path, hash, causedByPop) {
  var correctPath = pathExists(path);
  var validHash = hash !== undefined && hash !== "";

  // Path is invalid, continue with default path
  if (!correctPath) {
    path = DEFAULT_PATH;
  }

  // Path now always valid, remove hidden class from corresponding div
  paths[path][0].classList = ['fragment'];

  // Set title to be able to distinguish paths in history
  document.title = 'Philip Trauner - ' + paths[path][2];

  for (var pathId = 0; pathId < pathsKeys.length; pathId++) {
    if (pathsKeys[pathId] !== path) {
      paths[pathsKeys[pathId]][0].classList = ['hidden fragment'];
    }
  }

  // Select the header that corresponds to the path
  headerSelect(path);

  // History should not be modified on initial load, or if called by pop 
  // event handler (history entry already exists)
  if (!initialLoad && !causedByPop) {
    history.pushState(null, null, path);
  }

  // Replace state if invalid path
  if (!correctPath || validHash) {
    history.replaceState(null, null, path);
  }

  // Path in next pop state will not differ from current path
  if (validHash) {
    suppressPopStateEventHandler = true;
    location.hash = hash;
  }

  // Initial load has passed
  initialLoad = false;
}

processPath(currentPath(), location.hash, false);

window.addEventListener('click', function (e) {
  var target = e.target;
  // Only hijack click events for links with same origin
  if (target.nodeName == LINK_NODE_NAME &&
    target.pathname !== undefined &&
    target.host == location.host &&
    target.pathname.match(LINK_REGEX)) {
    processPath(target.pathname.substring(1), target.hash, false);
    e.preventDefault();
    e.stopPropagation();
  }
}, false);

window.addEventListener('popstate', function (e) {
  if (!suppressPopStateEventHandler) {
    processPath(e.target.location.pathname.substring(1), location.hash, true);
  } else {
    suppressPopStateEventHandler = false;
  }
});
