(function () {
    if (window.hasLeetLogInitialized) return;
    window.hasLeetLogInitialized = true;

    console.log("LeetLog AI: Tracking successful submissions...");

    let isProcessing = false;

    // Function to handle data extraction and blog generation
    const triggerBlogGeneration = async (geminiKey = null) => {
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

            // Send to background script
            chrome.runtime.sendMessage({
                type: 'GENERATE_BLOG',
                payload: { title, description, code, author, client_time, geminiKey }
            });

            setTimeout(() => { isProcessing = false; }, 5000);
        } catch (error) {
            console.error("LeetLog AI Error:", error);
            chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', message: 'Auto-Post Error: ' + error.message, status: 'error' });
            isProcessing = false;
        }
    };

    // Start of Listener for manual triggers from popup
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        if (request.type === 'MANUAL_TRIGGER') {
            triggerBlogGeneration(request.geminiKey);
        }
    });

    // Observer for automagic trigger on successful submission
    const observer = new MutationObserver(async (mutations) => {
        const resultElement = document.querySelector('[data-e2e-locator="submission-result"]');
        if (resultElement && resultElement.innerText.trim() === 'Accepted') {
            // Check storage for key before auto-triggering
            const data = await chrome.storage.local.get(['geminiKey']);
            triggerBlogGeneration(data.geminiKey || null);
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true,
        characterData: true
    });
})();
