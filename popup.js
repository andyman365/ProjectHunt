document.getElementById('list-videos').addEventListener('click', async () => {
  const tabs = await browser.tabs.query({ active: true, currentWindow: true });
  const currentTab = tabs[0];

  browser.runtime.sendMessage({ action: "list_videos", tabId: currentTab.id })
      .then(response => {
          document.getElementById('output').textContent = response.links ? response.links.join(", ") : "No videos found.";
          console.log("Video links:", response.links);
      })
      .catch(error => {
          console.error("Error listing videos: ", error);
          document.getElementById('output').textContent = "Error retrieving video links.";
      });
});

document.getElementById('download-video').addEventListener('click', async () => {
  const tabs = await browser.tabs.query({ active: true, currentWindow: true });
  const currentTab = tabs[0];

  console.log("this is the current tab info"  , currentTab)
  console.log("Sending download request for tab ID:", currentTab.id, "with URL:", currentTab.url);
  
  browser.runtime.sendMessage({ action: "download_video", tabId: currentTab.id, url: currentTab.url })
      .then(response => {
          document.getElementById('output').textContent = response.message || "Download started!";
      })
      .catch(error => {
          console.error("Error downloading video: ", error);
          document.getElementById('output').textContent = "Failed to start download.";
      });
});

document.getElementById('add-profile').addEventListener('click', async () => {
  // Get the current tab URL
  const [tab] = await browser.tabs.query({ active: true, currentWindow: true });
  const currentUrl = tab.url; // Current tab URL
  console.log("Current tab URL: ", currentUrl); // Debug: log current URL

  // Prompt the user for additional profile data (optional)
  const username = "andy";
  const category = "hot";

  // Create the profile data object
  const profileData = {
      url: currentUrl, // Current tab URL
      platform: "YouTube", // Assuming platform is YouTube; you can modify this
      category: category || "Uncategorized", // Use provided category or default
      username: username || "Unknown", // Use provided username or default
  };
  console.log("Profile data to be sent: ", profileData); // Debug: log profile data

  // Send the profile data to the server
  try {
      let response = await fetch("http://127.0.0.1:5000/post_profile", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(profileData),
      });
      let data = await response.json();
      document.getElementById('output').innerText = data.message; // Display success message
  } catch (error) {
      console.error("Error posting profile: ", error);
      document.getElementById('output').innerText = `Failed to post profile: ${error}`; // Display error message
  }
});
