chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === 'GENERATE_BLOG') {
        const { title, description, code, author, client_time, geminiKey } = request.payload;

        // 🚀 API URL - Make sure this matches your deployed Render URL!
        const API_URL = "https://leetcodeai-backend.onrender.com/generate-blog";

        console.log("LeetLog AI: Sending request to", API_URL);

        fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ title, description, code, author, client_time, geminiKey })
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', message: 'Posted ✅', status: 'success' });
                    
                    // NEW: Silently notify backend that we are DONE for today 
                    // This allows your backend to stop sending reminders!
                    fetch("https://leetcodeai-backend.onrender.com/mark-done", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ phone: "+917819834452" })
                    }).catch(e => console.log("Silent mark-done failed, ignoring."));

                } else {
                    chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', message: 'API Error: ' + JSON.stringify(data), status: 'error' });
                }
            })
            .catch(error => {
                chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', message: 'Network Error: ' + error.message, status: 'error' });
            });
    }
});
