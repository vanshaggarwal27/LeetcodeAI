document.addEventListener('DOMContentLoaded', async () => {
    const statusEl = document.getElementById('status');
    const keyInput = document.getElementById('geminiKey');
    const reminderCheck = document.getElementById('reminderEnabled');
    const reminderFields = document.getElementById('reminderFields');
    const phoneInput = document.getElementById('phone');
    const keyInputCallMeBot = document.getElementById('callmebotKey');
    
    // Load existing settings
    const data = await chrome.storage.local.get(['geminiKey', 'reminderEnabled', 'phone']);
    if (data.geminiKey) keyInput.value = data.geminiKey;
    if (data.phone) phoneInput.value = data.phone;
    if (data.reminderEnabled) {
        reminderCheck.checked = true;
        reminderFields.style.display = 'block';
    }

    // Save key on change
    keyInput.addEventListener('input', () => {
        chrome.storage.local.set({ geminiKey: keyInput.value });
    });

    // Save reminder settings
    reminderCheck.addEventListener('change', () => {
        const enabled = reminderCheck.checked;
        reminderFields.style.display = enabled ? 'block' : 'none';
        chrome.storage.local.set({ reminderEnabled: enabled });
        if (enabled) chrome.runtime.sendMessage({ type: 'SCHEDULE_REMINDER' });
    });

    phoneInput.addEventListener('input', () => {
        chrome.storage.local.set({ phone: phoneInput.value });
    });

    statusEl.innerText = "Dev.to Automation Active 🚀";
});

document.getElementById('generateBtn').addEventListener('click', async () => {
    const statusEl = document.getElementById('status');
    const btn = document.getElementById('generateBtn');
    
    btn.disabled = true;
    statusEl.innerText = "Triggering generation...";

    try {
        let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        if (!tab.url.includes("leetcode.com/problems/")) {
            statusEl.innerText = "Please open a LeetCode problem!";
            btn.disabled = false;
            return;
        }

        const geminiKey = document.getElementById('geminiKey').value;
        
        // Try simple message first (for already running scripts)
        try {
            await chrome.tabs.sendMessage(tab.id, { 
                type: 'MANUAL_TRIGGER', 
                geminiKey: geminiKey 
            });
        } catch (msgErr) {
            // Fallback: Re-inject the script if it's not currently running (e.g. after extension update)
            console.log("Re-injecting content script...");
            await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                files: ['content.js']
            });
            // Now try sending the message again
            setTimeout(() => {
                chrome.tabs.sendMessage(tab.id, { 
                    type: 'MANUAL_TRIGGER',
                    geminiKey: geminiKey
                });
            }, 500);
        }
        
    } catch (e) {
        statusEl.innerText = "Error: Refresh the page!";
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
            if (request.status === 'success') {
                setTimeout(() => { statusEl.innerText = "Dev.to Automation Active 🚀"; }, 5000);
            }
        }
    }
});
