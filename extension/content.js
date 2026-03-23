(function() {
    if (window.hasLeetLogInitialized) return;
    window.hasLeetLogInitialized = true;

    console.log("LeetLog AI: Tracking successful submissions...");

    let isProcessing = false;

    // Function to handle data extraction and blog generation
    const triggerBlogGeneration = async () => {
        if (isProcessing) return;
        isProcessing = true;

        try {
            console.log("LeetLog AI: Triggering generation...");
            chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', message: 'Generating blog...', status: 'loading' });

            // Data Extraction
            const titleElement = document.querySelector('div[data-cy="question-title"]') || document.querySelector('.text-title-large');
            const title = titleElement ? titleElement.innerText : "Unknown Problem";

            const descriptionElement = document.querySelector('.elfjS') || document.querySelector('[data-track-load="description_content"]');
            const description = descriptionElement ? descriptionElement.innerText : "No description found.";

            let code = "";
            const viewLines = document.querySelector('.view-lines');
            if (viewLines) {
                code = Array.from(viewLines.children).map(line => line.innerText).join('\n');
            } else {
                // Fallback for different LeetCode versions
                const codeElement = document.querySelector('textarea.monaco-mouse-cursor-text');
                code = codeElement ? codeElement.value : document.querySelector('.view-lines')?.innerText || "No code found.";
            }

            // Extract the user's LeetCode Username
            let author = "Anonymous LeetCoder";
            const allLinks = document.querySelectorAll('a[href^="/u/"]');
            for (let link of allLinks) {
                let u = link.getAttribute('href').split('/u/')[1] || "";
                if (u) { author = u.replace('/', ''); break; }
            }

            if (!title || !description || !code) {
                throw new Error("Could not extract problem details.");
            }

            // Send to background script
            chrome.runtime.sendMessage({
                type: 'GENERATE_BLOG',
                payload: { title, description, code, author }
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
            triggerBlogGeneration();
        }
    });

    // Observer for automagic trigger on successful submission
    const observer = new MutationObserver((mutations) => {
        const resultElement = document.querySelector('[data-e2e-locator="submission-result"]');
        if (resultElement && resultElement.innerText.trim() === 'Accepted') {
            triggerBlogGeneration();
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true,
        characterData: true
    });
})();
