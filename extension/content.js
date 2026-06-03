(function () {
    if (window.hasLeetLogInitialized) return;
    window.hasLeetLogInitialized = true;

    console.log("LeetLog AI: Tracking successful submissions...");

    let isProcessing = false;
    let hasGeneratedForAccepted = false;
    let lastProblemTitle = ""; 
    let lastUrl = location.href;
    // Auto-trigger debounce and dedupe helpers
    let autoTriggerTimer = null;
    const AUTO_TRIGGER_DEBOUNCE_MS = 800; // wait for DOM to settle
    const AUTO_TRIGGER_MIN_INTERVAL_MS = 60 * 1000; // 1 minute between auto-triggers for same submission

    // Function to handle data extraction and blog generation
    const triggerBlogGeneration = async (custom_prompt = "") => {
        if (isProcessing) return;
        isProcessing = true;

        try {
            console.log("LeetLog AI: Triggering generation...");
            chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', message: 'Generating blog...', status: 'loading' });

            // Data Extraction
            const titleElement = document.querySelector('div[data-cy="question-title"]') ||
                document.querySelector('.text-title-large') ||
                document.querySelector('div.h-full.flex-col > div > div > span');
            const title = titleElement ? titleElement.innerText : "Unknown Problem";

            const descriptionElement = document.querySelector('.elfjS') ||
                document.querySelector('[data-track-load="description_content"]') ||
                document.querySelector('div[class*="question-content"]');
            const description = descriptionElement ? descriptionElement.innerText : "No description found.";
            // Extract difficulty badge 
            const difficultyElement = document.querySelector('.difficulty') ||
                document.querySelector('.text-difficuly-easy') ||
                document.querySelector('.text-difficuly-medium') ||
                document.querySelector('.text-difficuly-hard');
            const difficulty = difficultyElement ? difficultyElement.innerText.trim() : "Unknown Difficulty";

            let code = "";
            const viewLines = document.querySelector('.view-lines');
            if (viewLines) {
                code = Array.from(viewLines.children).map(line => line.innerText).join('\n');
            } else {
                // Try to get from monaco editor or a regular textarea
                const monaco = document.querySelector('.monaco-editor');
                if (monaco) {
                    // This is a bit of a hack but often works for extracting text from the editor view
                    code = Array.from(monaco.querySelectorAll('.view-line')).map(l => l.innerText).join('\n');
                }
                if (!code || code.trim().length < 5) {
                    const textarea = document.querySelector('textarea.monaco-mouse-cursor-text') || document.querySelector('textarea');
                    code = textarea ? textarea.value : "No code found.";
                }
            }

            // Extract difficulty badge
            const difficultyElement = document.querySelector('[class*="difficulty"]') ||
                document.querySelector('[class*="Difficulty"]');
            const difficulty = difficultyElement ? difficultyElement.innerText.trim() : "Unknown";

            // Extract the user's LeetCode Username
            let author = "Anonymous LeetCoder";
            const allLinks = document.querySelectorAll('a[href^="/u/"]');
            for (let link of allLinks) {
                let u = link.getAttribute('href').split('/u/')[1] || "";
                if (u) { author = u.replace('/', ''); break; }
            }

            if (!title || title === "Unknown Problem" || !code || code === "No code found.") {
                throw new Error("Could not extract problem details. Please ensure the problem is fully loaded.");
            }

            // Get current local time for formatting (YYYY-MM-DD HH:MM:SS)
            const now = new Date();
            const offset = now.getTimezoneOffset() * 60000;
            const client_time = new Date(now - offset).toISOString().slice(0, 19).replace('T', ' ');

            // Save the date of success for reminders
            const today = new Date().toDateString();
            chrome.storage.local.set({ lastAcceptedDate: today });

            // Send to background script
            chrome.runtime.sendMessage({
                type: 'GENERATE_BLOG',
                payload: { title, description, code, author, client_time, custom_prompt, difficulty } // add custom_prompt and difficulty
            });


        } catch (error) {
            console.error("LeetLog AI Error:", error);
            chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', message: 'Auto-Post Error: ' + error.message, status: 'error' });
            isProcessing = false;
        }
    };

    // Compute a lightweight key for the current problem to avoid duplicate auto-posts
    const _computeProblemKey = () => {
        try {
            const titleElement = document.querySelector('div[data-cy="question-title"]') ||
                document.querySelector('.text-title-large') ||
                document.querySelector('div.h-full.flex-col > div > div > span');
            const title = titleElement ? titleElement.innerText.trim() : "";

            const allLinks = document.querySelectorAll('a[href^="/u/"]');
            let author = "";
            for (let link of allLinks) {
                let u = link.getAttribute('href').split('/u/')[1] || "";
                if (u) { author = u.replace('/', ''); break; }
            }

            let code = "";
            const viewLines = document.querySelector('.view-lines');
            if (viewLines) {
                code = Array.from(viewLines.children).map(line => line.innerText).join('\n');
            } else {
                const monaco = document.querySelector('.monaco-editor');
                if (monaco) code = Array.from(monaco.querySelectorAll('.view-line')).map(l => l.innerText).join('\n');
                if (!code || code.trim().length < 5) {
                    const textarea = document.querySelector('textarea.monaco-mouse-cursor-text') || document.querySelector('textarea');
                    code = textarea ? textarea.value : "";
                }
            }

            // Keep key reasonably small - use first 200 chars of code
            const shortCode = (code || "").slice(0, 200);
            return `${title}||${author}||${shortCode}`;
        } catch (e) {
            return null;
        }
    };

    // Start of Listener for manual triggers from popup and status updates
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        if (request.type === 'MANUAL_TRIGGER') {
            triggerBlogGeneration(request.custom_prompt || ""); //usage of custom prompt
        } else if (request.type === 'STATUS_UPDATE') {
            if (request.status === 'success' || request.status === 'error') {
                isProcessing = false;
            }

        }
    });

    // Observer for automagic trigger on successful submission
    const observer = new MutationObserver(async (mutations) => {
        // Reset the flag if the URL or problem title has changed (for SPA navigation)
        const titleElement = document.querySelector('div[data-cy="question-title"]') ||
            document.querySelector('.text-title-large') ||
            document.querySelector('div.h-full.flex-col > div > div > span');
        const currentTitle = titleElement ? titleElement.innerText.trim() : "";

        if (window.location.href !== lastUrl || (currentTitle && currentTitle !== lastProblemTitle)) {
            lastUrl = window.location.href;
            if (currentTitle) lastProblemTitle = currentTitle;
            hasGeneratedForAccepted = false;
        }

        const resultElement = document.querySelector('[data-e2e-locator="submission-result"]');
        if (resultElement && resultElement.innerText.trim() === 'Accepted') {

            if (!hasGeneratedForAccepted) {
                hasGeneratedForAccepted = true;
                triggerBlogGeneration();
            }

        } 
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true,
        characterData: true
    });
})();
