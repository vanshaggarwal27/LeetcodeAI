chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === 'GENERATE_BLOG') {
        const { title, description, code, author, client_time, custom_prompt } = request.payload;

        // 🚀 API URL - Make sure this matches your deployed Render URL!
        const API_URL = "http://localhost:10000/generate-blog";

        console.log("LeetLog AI: Sending request to", API_URL);

        chrome.storage.local.get({
            publishingPlatforms: ['devto'],
            publishAsDraft: false
        }, ({ publishingPlatforms, publishAsDraft }) => {
            fetch(API_URL, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    title,
                    description,
                    code,
                    author,
                    client_time,
                    custom_prompt,
                    platforms: publishingPlatforms,
                    publish_as_draft: publishAsDraft
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success' || data.status === 'partial_success') {
                    const platforms = data.data?.platforms || [];
                    const postedPlatforms = platforms
                        .filter(result => result.status === 'success')
                        .map(result => result.platform)
                        .join(', ');
                        chrome.storage.local.get({ publishHistory: [] }, (res) => {
  const entry = {
    title: title,
    date: client_time || new Date().toISOString(),
    platforms: postedPlatforms ? postedPlatforms.split(', ').filter(p => p) : [],
    status: data.status
  };
  const history = res.publishHistory;
  history.unshift(entry);
  chrome.storage.local.set({ publishHistory: history.slice(0, 100) });
});
                    const failedPlatforms = platforms
                        .filter(result => result.status === 'error')
                        .map(result => result.platform)
                        .join(', ');
                    chrome.runtime.sendMessage({
                        type: 'STATUS_UPDATE',
                        message: failedPlatforms
                            ? `Posted to ${postedPlatforms}; failed: ${failedPlatforms}`
                            : (postedPlatforms ? `Posted to ${postedPlatforms}` : 'Posted'),
                        status: data.status === 'partial_success' ? 'warning' : 'success',
                        platforms
                    });
                } else {
                    const platformErrors = data.data?.platforms
                        ?.filter(result => result.status === 'error')
                        ?.map(result => `${result.platform}: ${result.message}`)
                        ?.join('; ');
                    const errMsg = platformErrors || data.message || JSON.stringify(data);
                    chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', message: 'Error: ' + errMsg, status: 'error' });
                }
            })
            .catch(error => {
                chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', message: 'Network Error: ' + error.message, status: 'error' });
            });
        });
    }
});
