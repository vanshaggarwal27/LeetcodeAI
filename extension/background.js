chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === 'GENERATE_BLOG') {
        const { title, description, code, author } = request.payload;

        // 🚀 Swap this to your live Render URL once deployed!
        const API_URL = "https://leetcodeai-backend.onrender.com/generate-blog";

        fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ title, description, code, author })
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', message: 'Posted ✅', status: 'success' });
                } else {
                    chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', message: 'API Error: ' + JSON.stringify(data), status: 'error' });
                }
            })
            .catch(error => {
                chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', message: 'Network Error: ' + error.message, status: 'error' });
            });
    }
});
