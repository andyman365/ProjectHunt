// thin_bar.js

window.addEventListener('message', (event) => {
    const url = event.data.url;
    console.log('yoyoyo' , event.data.url )

    const downloadOptions = document.getElementById('download-options');
    const subscribeBtn = document.getElementById('subscribe-btn');

    // Check if it's a video page or profile page
    if (url.includes('youtube.com/watch') || url.includes('youtube.com/shorts') || url.includes('instagram.com/reel')) {
        downloadOptions.style.display = 'block';
        subscribeBtn.style.display = 'none';
    } else if (url.includes('instagram.com') || url.includes('youtube.com/channel') || url.includes('youtube.com/user')) {
        downloadOptions.style.display = 'none';
        subscribeBtn.style.display = 'block';
    }
});
