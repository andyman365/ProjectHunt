// Listen for tab updates (i.e., when the user navigates to a new URL)
browser.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    // Only proceed if the tab has finished loading and the URL has changed
    if (changeInfo.status === 'complete') {
        browser.tabs.sendMessage(tabId, { url: tab.url });
        console.log("Tab updated with URL:", tab.url);

        const currentUrl = tab.url; // Get the updated tab URL

        // Function to check if the URL is a profile URL
        function isProfileUrl(url) {
            // Check for Instagram profiles
            if (url.includes('instagram.com') && !isVideoUrl(url)) {
                return true;
            }
            
            // Check for YouTube profiles (i.e., "/@username" pattern or "/user/username")
            const youtubeProfileRegex = /^(https?:\/\/)?(www\.)?(youtube\.com)\/(@|user\/)[a-zA-Z0-9_-]+/;
            return youtubeProfileRegex.test(url);
        }

        // Function to check if the URL is a video URL
        function isVideoUrl(url) {
            const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com)\/(watch\?v=|embed\/|v\/|shorts\/)/;
            const youtubeShortsRegex = /^(https?:\/\/)?(www\.)?(youtube\.com)\/shorts\/([a-zA-Z0-9_-]+)/;
            const instagramRegex = /^(https?:\/\/)?(www\.)?(instagram\.com)\/(p|reel)\/([a-zA-Z0-9_-]+)/;

            return youtubeRegex.test(url) || youtubeShortsRegex.test(url) || instagramRegex.test(url);
        }

        // Check if the current URL is a profile URL and not a video URL
        if (isProfileUrl(currentUrl) && !isVideoUrl(currentUrl)) {
            const platform = currentUrl.includes("youtube.com") ? "YouTube" : "Instagram";

            // Prepare the data to check or add profile
            const profileData = {
                url: currentUrl,
                platform: platform,
                category: "Uncategorized", // Customize this if needed
                username: "Unknown" // Add logic to extract username if needed
            };

            // Send a request to the backend to check or add the profile
            try {
                let response = await fetch("http://127.0.0.1:5000/check_or_add_profile", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(profileData)
                });
                let data = await response.json();

                if (data.status === 'success') {
                    const profileId = data.profile_id; // Get the profile ID from the response

                    // Now, send the visit URL along with the profile ID to record the visit
                    let visitResponse = await fetch("http://127.0.0.1:5000/add_visit", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            profile_id: profileId,
                            visited_url: currentUrl
                        })
                    });
                    let visitData = await visitResponse.json();
                    console.log("Visit recorded successfully:", visitData);
                } else {
                    console.log("Error checking/adding profile:", data.message);
                }
            } catch (error) {
                console.error("Error in profile or visit request:", error);
            }
        } else {
            console.log("This URL is either a video or not a recognized profile. No action taken.");
        }
    }
});

// Message listener for actions like listing videos or downloading
browser.runtime.onMessage.addListener(async (message, sender) => {
    const currentUrl = message.url; // Get the current tab's URL from the sender
    console.log("this is the current url" )
    if (message.action === "list_videos") {
        try {
            let response = await fetch("http://127.0.0.1:5000/get_videos", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({url: currentUrl})
            });
            let data = await response.json();

            console.log("Videos fetched:", data.links);
            return {message: "Videos listed successfully!", links: data.links};
        } catch (error) {
            console.error("Error fetching video links: ", error);
            return {message: "Failed to list videos."};
        }
    }

    if (message.action === "download_video") {
        try {
            let response = await fetch("http://127.0.0.1:5000/download_video", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({url: currentUrl})
            });
            let data = await response.json();
            return {message: "Download started successfully!"};
        } catch (error) {
            console.error("Error downloading video: ", error);
            return {message: "Failed to download video."}; 
        }
    }

    if (message.action === "post_profile") {
        const profileData = {
            url: currentUrl, // Current tab URL
            platform: "YouTube", // Assuming platform is YouTube; you can modify this
            category: message.category || "Uncategorized", // Use provided category or default
            username: message.username || "Unknown" // Use provided username or default
        };

        try {
            let response = await fetch("http://127.0.0.1:5000/post_profile", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(profileData)
            });
            let data = await response.json();
            return {message: "Profile posted successfully!", response: data};
        } catch (error) {
            console.error("Error posting profile: ", error);
            return {message: "Failed to post profile."};
        }
    }
});
