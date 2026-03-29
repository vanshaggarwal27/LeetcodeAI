document.addEventListener('DOMContentLoaded', async () => {
    const statusEl = document.getElementById('status');
    statusEl.innerText = "Dev.to Automation Active 🚀";
});

document.getElementById('generateBtn').addEventListener('click', async () => {
    const statusEl = document.getElementById('status');
    const btn = document.getElementById('generateBtn');
    
    btn.disabled = true;
    statusEl.innerText = "Triggering generation...";
    statusEl.className = ""; // Reset classes

    try {
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        const tab = tabs[0];
        
        if (!tab || !tab.url || !tab.url.includes("leetcode.com/problems/")) {
            statusEl.innerText = "Please open a LeetCode problem page!";
            statusEl.className = "error-status";
            btn.disabled = false;
            return;
        }
        // Try simple message first
        try {
            await chrome.tabs.sendMessage(tab.id, { 
                type: 'MANUAL_TRIGGER'
            });
        } catch (msgErr) {
            console.log("Re-injecting content script...");
            await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                files: ['content.js']
            });
            
            // Wait slightly for injection
            setTimeout(async () => {
                try {
                    await chrome.tabs.sendMessage(tab.id, { 
                        type: 'MANUAL_TRIGGER'
                    });
                } catch (e2) {
                    statusEl.innerText = "Error: Please refresh LeetCode page!";
                    statusEl.className = "error-status";
                    btn.disabled = false;
                }
            }, 500);
        }
    } catch (e) {
        console.error("Popup Error:", e);
        statusEl.innerText = "Error: " + e.message;
        statusEl.className = "error-status";
        btn.disabled = false;
    }
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    const statusEl = document.getElementById('status');
    const btn = document.getElementById('generateBtn');
    
    if (request.type === 'STATUS_UPDATE') {
        statusEl.innerText = request.message;
        statusEl.className = ""; // Reset

        if (request.status === 'success') {
            statusEl.innerText = "Successfully posted to Dev.to! ✅";
            statusEl.className = "success-status";
            btn.disabled = false;
            setTimeout(() => { 
                statusEl.innerText = "Dev.to Automation Active 🚀"; 
                statusEl.className = "";
            }, 5000);
        } else if (request.status === 'error') {
            statusEl.className = "error-status";
            btn.disabled = false;
        } else if (request.status === 'loading') {
            statusEl.innerText = request.message || "Generating blog...";
        }
    }
});
