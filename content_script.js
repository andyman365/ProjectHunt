// content_script.js

const YOUTUBE_VIDEO_URL = 'youtube.com/watch';
const YOUTUBE_PROFILE_URL = 'youtube.com/channel';
const INSTAGRAM_VIDEO_URL = 'instagram.com/reel';
const INSTAGRAM_PROFILE_URL = 'instagram.com/';

function injectThinBar(url) {
  try {
    const iframe = document.createElement('iframe');
    iframe.src = browser.runtime.getURL('thin_bar.html');
    iframe.style.position = 'fixed';
    iframe.style.top = '0';
    iframe.style.left = '0';
    iframe.style.width = '100%';
    iframe.style.height = '50px';
    iframe.style.border = 'none';
    iframe.style.zIndex = '9999';
    iframe.onload = function() {
      updateUI(url);
    };
    document.body.insertBefore(iframe, document.body.firstChild);
    console.log("Thin bar injected");
    document.body.style.marginTop = '50px';
  } catch (error) {
    console.error("Error injecting thin bar:", error);
  }
}


function isVideoPage(url) {
  return url.includes(YOUTUBE_VIDEO_URL) || url.includes(INSTAGRAM_VIDEO_URL);
}

function isProfilePage(url) {
  return url.includes(YOUTUBE_PROFILE_URL) || url.includes(INSTAGRAM_PROFILE_URL);
}

function updateUI(url) {
  const iframe = document.querySelector('iframe[src="' + browser.runtime.getURL('thin_bar.html') + '"]');
  if (iframe) {
    iframe.contentWindow.postMessage({ url }, '*');
    console.log("Sent URL to iframe:", url);
  } else {
    console.error("Iframe not found");
  }
}

browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
  try {
    console.log("Received message in content script:", message);
    const currentUrl = message.url;
    injectThinBar(currentUrl);
  } catch (error) {
    console.error("Error handling message:", error);
  }
});

window.addEventListener('message', (event) => {
 // i don't think this ever gets called/
  try {
    console.log("Message received in iframe:", event.data);
    if (event.data && event.data.url) {
      const url = event.data.url;
      const downloadOptions = document.getElementById('download-options');
      const subscribeBtn = document.getElementById('subscribe-btn');

      if (isVideoPage(url)) {
        downloadOptions.style.display = 'block';
        subscribeBtn.style.display = 'none';
        console.log("Video page, showing download options");
      } else if (isProfilePage(url)) {
        downloadOptions.style.display = 'none';
        subscribeBtn.style.display = 'block';
        console.log("Profile page, showing subscribe button");
      }
    } else {
      console.warn("Received message does not contain a valid URL:", event.data);
    }
  } catch (error) {
    console.error("Error handling message:", error);
  }
});
