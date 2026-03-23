document.getElementById('generateBtn').addEventListener('click', async () => {
    const statusEl = document.getElementById('status');
    const btn = document.getElementById('generateBtn');
    
    statusEl.innerText = "Extracting data...";
    btn.disabled = true;

    try {
        let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        if (!tab.url.includes("leetcode.com/problems/")) {
            statusEl.innerText = "Please open a LeetCode problem!";
            btn.disabled = false;
            return;
        }

        chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ['content.js']
        }, () => {
             // The content script will handle extracting and sending
             // But we need content script to return or message the popup 
             // to show status
        });
        
    } catch (e) {
        statusEl.innerText = "Error: " + e.message;
        btn.disabled = false;
    }
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    const statusEl = document.getElementById('status');
    const btn = document.getElementById('generateBtn');
    
    if (request.type === 'STATUS_UPDATE') {
        statusEl.innerText = request.message;
        if (request.status === 'success' || request.status === 'error') {
            btn.disabled = false;
        }
    }
});
