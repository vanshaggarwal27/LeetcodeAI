(async () => {
    try {
        console.log("LeetLog AI content script running...");
        chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', message: 'Extracting data...', status: 'loading' });
        
        // Data Extraction
        const titleElement = document.querySelector('div[data-cy="question-title"]') || document.querySelector('.text-title-large');
        const title = titleElement ? titleElement.innerText : "Unknown Problem";
        
        const descriptionElement = document.querySelector('.elfjS') || document.querySelector('[data-track-load="description_content"]');
        const description = descriptionElement ? descriptionElement.innerText : "No description found.";
        
        let code = "";
        const viewLines = document.querySelector('.view-lines');
        if (viewLines) {
            code = viewLines.innerText;
        } else {
            const codeElement = document.querySelector('textarea');
            code = codeElement ? codeElement.value : "No code found.";
        }
        
        // Extract the user's LeetCode Username
        let author = "Anonymous LeetCoder";
        const allLinks = document.querySelectorAll('a[href^="/u/"]');
        for (let link of allLinks) {
            let u = link.getAttribute('href').split('/u/')[1] || "";
            if (u) {
                author = u.replace('/', '');
                break;
            }
        }
        
        if (!title || !description || !code) {
             throw new Error("Could not extract problem details.");
        }

        chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', message: 'Generating and Posting...', status: 'loading' });

        // Send to background script
        chrome.runtime.sendMessage({
            type: 'GENERATE_BLOG',
            payload: { title, description, code, author }
        });

    } catch (error) {
        chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', message: 'Error: ' + error.message, status: 'error' });
    }
})();
