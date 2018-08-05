'use strict';

var DEFAULT_ANCHOR = 'about';

var header = document.getElementsByTagName('header')[0];
var navigationElements = header.children[0].children;
var rootAnchors = document.querySelectorAll('.content[id]');

function currentAnchor() {
  return (location.href.indexOf("#") !== -1 ? location.href.substring(
    location.href.indexOf("#") + 1, location.href.length) : '');
}

// Reset anchor to default
function resetAnchor() {
  setAnchor(DEFAULT_ANCHOR);
}

// Called on page visit to ensure that the default anchor is set
function initialiseAnchor() {
  if (location.href.substring(location.href.indexOf('#') + 1) == location.href) {
    resetAnchor();
  } else {
    processAnchor(currentAnchor());
  }
}

function setAnchor(anchor) {
  var rawAnchor = '#' + anchor;
  headerSelect(document.querySelector('a[href="' + rawAnchor + '"]'));
  if (anchor !== currentAnchor()) {
    var currentLocation = location.href.split('#');
    location.href = currentLocation[0] + rawAnchor;
  }
}

function processAnchor(anchor) {
  // Anchor is set
  if ((anchor.split('#').length - 1) == 0 || anchor !== '') {
    var pathAnchor = anchor.split('/');
    switch (pathAnchor.length) {
      // Regular anchor
      case 1:
      // Anchor cascade
      case 2:
        for (var anchorIndex = 0; anchorIndex < rootAnchors.length; anchorIndex++) {
          if (rootAnchors[anchorIndex].id === pathAnchor[0]) {
            setAnchor(pathAnchor[0]);
            if (pathAnchor.length == 2) {
              var pathElement = document.getElementById(pathAnchor[1]);
              if (pathElement !== null && rootAnchors[anchorIndex].contains(pathElement)) {
                pathElement.scrollIntoView();
              } else {
                resetAnchor();
              }
            }
            // Navigated to root anchor and scrolled path element into view or
            // only navigated to root or
            // non-existent path element and navigated to default anchor
            return;
          }
        }
      default:
        // Invalid path
        resetAnchor();
    }
  } else {
    // Return to default anchor if extraneous '#' characters are present or
    // anchor is empty
    resetAnchor();
  }
}

function headerSelect(navigationElement) {
  for (var navId = 0; navId < header.children[0].childElementCount; navId++) {
    if (navigationElements[navId].children[0] === navigationElement) {
      navigationElements[navId].children[0].classList = ['header-selected'];
    } else {
      navigationElements[navId].children[0].classList = [];
    }
  }
}

initialiseAnchor();

window.addEventListener('hashchange', function(event) {
  processAnchor(currentAnchor());
}, false);