document.addEventListener('DOMContentLoaded', () => {
    const statusEl = document.getElementById('status');
    statusEl.innerText = "Automation Active 🚀";
});

document.getElementById('generateBtn').addEventListener('click', async () => {
    const statusEl = document.getElementById('status');
    const btn = document.getElementById('generateBtn');

    btn.disabled = true;
    statusEl.innerText = "Triggering manual generation...";

    try {
        let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        if (!tab.url.includes("leetcode.com/problems/")) {
            statusEl.innerText = "Please open a LeetCode problem!";
            btn.disabled = false;
            return;
        }

        // Send message to the already-running content script
        chrome.tabs.sendMessage(tab.id, { type: 'MANUAL_TRIGGER' });

    } catch (e) {
        statusEl.innerText = "Error: Use 'Generate' only on problem pages!";
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
            // Revert to automation active message after a few seconds on success
            if (request.status === 'success') {
                setTimeout(() => { statusEl.innerText = "Automation Active 🚀"; }, 5000);
            }
        }
    }
});
