let generatedBlogMarkdown = "";
let generatedProblemTitle = "";
let generatedBlog = "";

let progressInterval;

function startProgress() {
    const container = document.getElementById('progressContainer');
    const bar = document.getElementById('progressBar');
    const timeEl = document.getElementById('timeLeft');
    const statusEl = document.getElementById('status');
    const textEl = document.getElementById('progressText');
    
    container.style.display = 'block';
    statusEl.style.display = 'none';
    
    let progress = 0;
    let secondsLeft = 15;
    
    bar.style.width = '0%';
    timeEl.innerText = '~15s';
    textEl.innerText = 'Generating & Publishing...';
    
    clearInterval(progressInterval);
    progressInterval = setInterval(() => {
        progress += (100 / 15) * 0.1; // 0.1s tick
        if (progress > 95) progress = 95; // cap at 95% until done
        
        bar.style.width = progress + '%';
        
        // Update timer every second
        if (Math.floor(progress * 15 / 100) > Math.floor((progress - (100/15)*0.1) * 15 / 100)) {
            secondsLeft -= 1;
            if (secondsLeft < 1) secondsLeft = 1;
            timeEl.innerText = '~' + secondsLeft + 's';
        }
    }, 100);
}

function finishProgress(success) {
    clearInterval(progressInterval);
    const bar = document.getElementById('progressBar');
    const timeEl = document.getElementById('timeLeft');
    if (success) {
        bar.style.width = '100%';
        timeEl.innerText = 'Done!';
    }
    setTimeout(() => {
        const container = document.getElementById('progressContainer');
        const statusEl = document.getElementById('status');
        if (container) container.style.display = 'none';
        if (statusEl) statusEl.style.display = 'block';
    }, success ? 1000 : 0);
}

function convertMarkdownToHTML(markdown) {
    return markdown
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        .replace(/\*\*(.*)\*\*/gim, '<b>$1</b>')
        .replace(/\*(.*)\*/gim, '<i>$1</i>')
        .replace(/\n/gim, '<br>');
}

document.addEventListener('DOMContentLoaded', async () => {

    const statusEl = document.getElementById('status');
    const platformInputs =
        Array.from(
            document.querySelectorAll(
                'input[name="platform"]'
            )
        );

    const draftInput =
        document.getElementById('draftMode');

    chrome.storage.local.get({
        publishingPlatforms: ['devto'],
        publishAsDraft: false
    }, ({ publishingPlatforms, publishAsDraft }) => {

        platformInputs.forEach(input => {
            input.checked =
                publishingPlatforms.includes(
                    input.value
                );
        });

        draftInput.checked =
            publishAsDraft;
    });

    const savePublishingSettings = () => {

        const selectedPlatforms =
            platformInputs
                .filter(input => input.checked)
                .map(input => input.value);

        if (selectedPlatforms.length === 0) {

            const devtoInput =
                platformInputs.find(
                    input => input.value === 'devto'
                );

            if (devtoInput) {
                devtoInput.checked = true;
                selectedPlatforms.push('devto');
            }
        }

        chrome.storage.local.set({
            publishingPlatforms:
                selectedPlatforms,
            publishAsDraft:
                draftInput.checked
        });
    };

    platformInputs.forEach(input =>
        input.addEventListener(
            'change',
            savePublishingSettings
        )
    );

    draftInput.addEventListener(
        'change',
        savePublishingSettings
    );

    // Load generated blog from storage
    chrome.storage.local.get(
        [
            "generatedBlog",
            "generatedProblemTitle"
        ],
        (res) => {

            if (res.generatedBlog) {

                generatedBlog =
                    res.generatedBlog;

                generatedBlogMarkdown =
                    res.generatedBlog;

                generatedProblemTitle =
                    res.generatedProblemTitle
                    || "leetcode-blog";

                document
                    .getElementById("exportSection")
                    .style.display = "block";

                document
                    .getElementById("previewSection")
                    .style.display = "block";

                document
                    .getElementById("blogEditor")
                    .value = generatedBlog;
            }
    });

    statusEl.innerText =
        "Publishing automation active";
});

// Generate button
document.getElementById('generateBtn')
.addEventListener('click', async () => {

    const statusEl =
        document.getElementById('status');

    const btn =
        document.getElementById('generateBtn');

    btn.disabled = true;

    btn.disabled = true;

    startProgress();

    try {

        const tabs =
            await chrome.tabs.query({
                active: true,
                currentWindow: true
            });

        const tab = tabs[0];

        const customPrompt =
            document
                .getElementById('customPrompt')
                .value
                .trim();

        if (
            !tab ||
            !tab.url ||
            !tab.url.includes(
                "leetcode.com/problems/"
            )
        ) {

            statusEl.innerText =
                "Please open a LeetCode problem page!";

            statusEl.className =
                "error-status";

            finishProgress(false);
            btn.disabled = false;

            return;
        }

        try {

            await chrome.tabs.sendMessage(
                tab.id,
                {
                    type: 'MANUAL_TRIGGER',
                    custom_prompt: customPrompt
                }
            );

        } catch (msgErr) {

            console.log(
                "Re-injecting content script..."
            );

            await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                files: ['content.js']
            });

            setTimeout(async () => {

                try {

                    await chrome.tabs.sendMessage(
                        tab.id,
                        {
                            type: 'MANUAL_TRIGGER'
                        }
                    );

                } catch (e2) {

                    statusEl.innerText =
                        "Error: Please refresh LeetCode page!";

                    statusEl.className =
                        "error-status";

                    finishProgress(false);
                    btn.disabled = false;
                }

            }, 500);
        }

    } catch (e) {

        console.error("Popup Error:", e);

        statusEl.innerText =
            "Error: " + e.message;

        statusEl.className =
            "error-status";

        finishProgress(false);
        btn.disabled = false;
    }
});

// Listen for blog ready event
chrome.runtime.onMessage.addListener((request) => {

    if (request.type === "BLOG_READY") {

        chrome.storage.local.get(
            [
                "generatedBlog",
                "generatedProblemTitle"
            ],
            (res) => {

                if (res.generatedBlog) {

                    generatedBlog =
                        res.generatedBlog;

                    generatedBlogMarkdown =
                        res.generatedBlog;

                    generatedProblemTitle =
                        res.generatedProblemTitle
                        || "leetcode-blog";

                    document
                        .getElementById("exportSection")
                        .style.display = "block";

                    document
                        .getElementById("previewSection")
                        .style.display = "block";

                    document
                        .getElementById("blogEditor")
                        .value = generatedBlog;

                    document
                        .getElementById("status")
                        .innerText =
                        "Blog generated successfully!";

                    finishProgress(true);
                    document
                        .getElementById("generateBtn")
                        .disabled = false;
                }
        });
    }
});

// Status updates
chrome.runtime.onMessage.addListener(
    (request) => {

    const statusEl =
        document.getElementById('status');

    const btn =
        document.getElementById('generateBtn');

    if (request.type === 'STATUS_UPDATE') {

        statusEl.innerText =
            request.message;

        statusEl.className = "";

        if (request.status === 'success') {
            finishProgress(true);

            statusEl.innerText =
                request.message ||
                "Successfully posted";

            statusEl.className =
                "success-status";

            btn.disabled = false;

        } else if (
            request.status === 'error'
        ) {
            finishProgress(false);

            statusEl.className =
                "error-status";

            btn.disabled = false;

        } else if (
            request.status === 'warning'
        ) {
            finishProgress(true);

            statusEl.className =
                "warning-status";

            btn.disabled = false;
        }
    }
});

// Dashboard button
document.getElementById('dashboardBtn')
.addEventListener('click', () => {

    chrome.tabs.create({
        url: chrome.runtime.getURL(
            'dashboard.html'
        )
    });
});

// Export Markdown
document
.getElementById("exportMarkdownBtn")
?.addEventListener("click", () => {

    const blob = new Blob(
        [generatedBlogMarkdown],
        { type: "text/markdown" }
    );

    const url =
        URL.createObjectURL(blob);

    const a =
        document.createElement("a");

    a.href = url;

    a.download =
        `${generatedProblemTitle}.md`;

    a.click();

    URL.revokeObjectURL(url);
});

// Export HTML
document
.getElementById("exportHTMLBtn")
?.addEventListener("click", () => {

    const html =
        convertMarkdownToHTML(
            generatedBlogMarkdown
        );

    const blob = new Blob(
        [html],
        { type: "text/html" }
    );

    const url =
        URL.createObjectURL(blob);

    const a =
        document.createElement("a");

    a.href = url;

    a.download =
        `${generatedProblemTitle}.html`;

    a.click();

    URL.revokeObjectURL(url);
});

// Export PDF
document
.getElementById("exportPDFBtn")
?.addEventListener("click", () => {

    const container =
        document.createElement("div");

    container.style.padding =
        "20px";

    container.innerHTML =
        convertMarkdownToHTML(
            generatedBlogMarkdown
        );

    html2pdf()
        .set({
            margin: 0.5,
            filename:
                `${generatedProblemTitle}.pdf`,
            image: {
                type: "jpeg",
                quality: 1
            },
            html2canvas: {
                scale: 2
            },
            jsPDF: {
                unit: "in",
                format: "a4",
                orientation: "portrait"
            }
        })
        .from(container)
        .save();
});

// Publish button
document
.getElementById("publishBtn")
?.addEventListener("click", async () => {

    const editedBlog =
        document
            .getElementById("blogEditor")
            .value;

    chrome.runtime.sendMessage({
        type: "PUBLISH_EDITED_BLOG",
        blog: editedBlog
    });

    document
        .getElementById("status")
        .innerText =
        "Publishing edited blog...";
});

// Cancel button
document
.getElementById("cancelPreviewBtn")
?.addEventListener("click", () => {

    document
        .getElementById("previewSection")
        .style.display = "none";
});