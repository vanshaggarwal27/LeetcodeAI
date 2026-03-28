chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === 'GENERATE_BLOG') {
        const { title, description, code, author, client_time, geminiKey } = request.payload;

        // 🚀 API URL - Make sure this matches your deployed Render URL!
        // If testing locally, use "http://localhost:10000/generate-blog"
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
                    // Clear any pending retry reminders for tonight
                    chrome.alarms.clear('leetcodes_retry');
                } else {
                    chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', message: 'API Error: ' + JSON.stringify(data), status: 'error' });
                }
            })
            .catch(error => {
                chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', message: 'Network Error: ' + error.message, status: 'error' });
            });
    }

    if (request.type === 'SCHEDULE_REMINDER') {
        setupDailyReminder();
    }
});

// Alarm Listener for 11 PM Reminder and Retries
chrome.alarms.onAlarm.addListener(async (alarm) => {
    if (alarm.name === 'leetcodes_reminder' || alarm.name === 'leetcodes_retry') {
        const data = await chrome.storage.local.get(['reminderEnabled', 'lastAcceptedDate', 'phone']);
        
        if (!data.reminderEnabled || !data.phone) return;

        const today = new Date().toDateString();
        if (data.lastAcceptedDate !== today) {
            console.log(`LeetLog AI: [${alarm.name}] Reminder condition met! Pulsing backend...`);
            
            // Call backend to send WhatsApp reminder
            const BACKEND_URL = "https://leetcodeai-backend.onrender.com/send-reminder";
            
            fetch(BACKEND_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ phone: data.phone })
            })
            .then(res => res.json())
            .then(resData => {
                console.log("Reminder success:", resData);
                // Schedule a retry in 30 minutes if not already scheduled
                if (alarm.name === 'leetcodes_reminder') {
                     chrome.alarms.create('leetcodes_retry', { delayInMinutes: 30, periodInMinutes: 30 });
                }
            })
            .catch(err => console.error("Reminder failure:", err));
        } else {
            // Condition met today, stop retrying
            chrome.alarms.clear('leetcodes_retry');
        }
    }
});

function setupDailyReminder() {
    // Schedule for 11:00 PM (23:00)
    const now = new Date();
    const scheduledTime = new Date();
    scheduledTime.setHours(23, 0, 0, 0);

    // If it's already past 11 PM today, schedule for tomorrow
    if (now > scheduledTime) {
        scheduledTime.setDate(scheduledTime.getDate() + 1);
    }

    const delay = scheduledTime.getTime() - now.getTime();
    
    // Create alarm: 24h interval = 1440 minutes
    chrome.alarms.create('leetcodes_reminder', {
        when: Date.now() + delay,
        periodInMinutes: 1440 
    });
    
    console.log("LeetLog AI: Scheduled daily reminder for 11:00 PM. First alarm in (ms):", delay);
}

// Ensure reminder is scheduled on startup
chrome.runtime.onStartup.addListener(setupDailyReminder);
chrome.runtime.onInstalled.addListener(setupDailyReminder);
