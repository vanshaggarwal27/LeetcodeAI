// ── Email setup ──────────────────────────────────────────────
const API_BASE_URL = "https://leetcodeai-backend.onrender.com";

const MAIN_IDS = ['generate-blog-btn', 'copyBtn', 'customPrompt',
    '.input-group', '.platform-panel', '#exportSection',
    '#previewSection', '#progressContainer', '#status', '#dashboardBtn', '#historySection',
    '.footer', 'h2', 'p'];
let authMode = 'login';

function setAuthStatus(message, type = 'error') {
    const loginStatus = document.getElementById('loginStatus');
    loginStatus.textContent = message;
    loginStatus.className = type === 'info' ? 'info-status' : '';
}

function setAuthMode(mode) {
    authMode = mode;
    const isSignup = authMode === 'signup';
    document.getElementById('authTitle').textContent = isSignup ? 'Create your LeetLog AI account' : 'Log in to LeetLog AI';
    document.getElementById('authDescription').textContent = isSignup
        ? 'Create an account to keep your generated blogs tied to your profile.'
        : 'Connect your account so generated blogs publish to the right user profile.';
    document.getElementById('saveEmailBtn').textContent = isSignup ? 'Sign Up' : 'Log In';
    document.getElementById('authSwitchText').textContent = isSignup ? 'Already have an account?' : 'New here?';
    document.getElementById('toggleAuthMode').textContent = isSignup ? 'Log in' : 'Create an account';
    setAuthStatus('', 'error');
}

function showEmailSetup() {
    document.body.classList.add('auth-only');
    setAuthMode(authMode);
    document.getElementById('emailSetup').style.display = 'flex';
    document.getElementById('userBadge').style.display = 'none';
    document.getElementById('passwordInput').value = '';
    setAuthStatus('', 'error');
    // hide main content while setup is shown
    ['generate-blog-btn', 'copyBtn', 'dashboardBtn'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });
    document.querySelectorAll('.input-group, .platform-panel, .button-group, .footer, #status, #exportSection, #previewSection, #progressContainer, h2, body > p')
        .forEach(el => el.style.display = 'none');
    const historySection = document.getElementById('historySection');
    if (historySection) historySection.style.display = 'none';
}

function showMainUI(email) {
    document.body.classList.remove('auth-only');
    document.getElementById('emailSetup').style.display = 'none';
    const badge = document.getElementById('userBadge');
    badge.style.display = 'flex';
    document.getElementById('userEmailDisplay').textContent = email;
    // restore main content
    ['generate-blog-btn', 'copyBtn', 'dashboardBtn'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = '';
    });
    document.querySelectorAll('.input-group, .platform-panel, .button-group, .footer, #status, h2, body > p')
        .forEach(el => el.style.display = '');
    const historySection = document.getElementById('historySection');
    if (historySection) historySection.style.display = '';
}

document.getElementById('saveEmailBtn').addEventListener('click', async () => {
    const input = document.getElementById('emailInput');
    const passwordInput = document.getElementById('passwordInput');
    const loginBtn = document.getElementById('saveEmailBtn');
    const email = input.value.trim();
    const password = passwordInput.value;
    setAuthStatus('', 'error');

    if (!email || !email.includes('@')) {
        input.classList.add('invalid');
        return;
    }
    input.classList.remove('invalid');

    if (!password) {
        passwordInput.classList.add('invalid');
        return;
    }
    passwordInput.classList.remove('invalid');

    loginBtn.disabled = true;
    loginBtn.textContent = authMode === 'signup' ? 'Signing up...' : 'Logging in...';

    try {
        const endpoint = authMode === 'signup' ? 'register' : 'login';
        const response = await fetch(`${API_BASE_URL}/auth/${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await response.json().catch(() => ({}));

        if (!response.ok || !data.token || !data.user) {
            const rawMessage = data.detail || data.message || '';
            if (response.status === 401 && authMode === 'login') {
                setAuthMode('signup');
                setAuthStatus('No account found with these details. Create an account below.', 'info');
                return;
            }
            if (response.status === 409 && authMode === 'signup') {
                setAuthMode('login');
                setAuthStatus('Account already exists. Log in instead.', 'info');
                return;
            }
            if (/database|mongodb/i.test(rawMessage)) {
                throw new Error('Login service is temporarily unavailable. Please try again later.');
            }
            if (response.status === 400 && /password/i.test(rawMessage)) {
                throw new Error(rawMessage);
            }
            throw new Error(rawMessage || `${authMode === 'signup' ? 'Sign up' : 'Login'} failed. Please try again.`);
        }

        chrome.storage.local.set({
            userEmail: data.user.email,
            userId: data.user.id,
            sessionToken: data.token
        }, () => showMainUI(data.user.email));
    } catch (error) {
        setAuthStatus(error.message);
    } finally {
        loginBtn.disabled = false;
        loginBtn.textContent = authMode === 'signup' ? 'Sign Up' : 'Log In';
    }
});

document.getElementById('toggleAuthMode').addEventListener('click', () => {
    setAuthMode(authMode === 'login' ? 'signup' : 'login');
});

document.getElementById('emailInput').addEventListener('input', function () {
    this.classList.remove('invalid');
});

document.getElementById('passwordInput').addEventListener('input', function () {
    this.classList.remove('invalid');
});

document.getElementById('changeEmailBtn').addEventListener('click', () => {
    chrome.storage.local.remove(['userEmail', 'userId', 'sessionToken'], showEmailSetup);
});
// ─────────────────────────────────────────────────────────────

let generatedBlogMarkdown = "";
let generatedProblemTitle = "";
let generatedBlog = "";

let progressInterval;
let generationTimeout;

function resetGenerationUI() {
    const btn = document.getElementById("generate-blog-btn");
    const progressContainer = document.getElementById("progressContainer");
    const copyBtn = document.getElementById('copyBtn');

    clearInterval(progressInterval);

    if (btn) {
        btn.disabled = false;
    }

    if (copyBtn) {
        copyBtn.disabled = false;
    }

    if (progressContainer) {
        progressContainer.style.display = "none";
    }
}

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
    clearTimeout(generationTimeout);

    generationTimeout = setTimeout(() => {
        finishProgress(false);

        const statusEl = document.getElementById("status");

        if (statusEl) {
            statusEl.innerText = "Generation timed out. Please try again.";
            statusEl.className = "error-status";
        }
    }, 30000);

    // RESOLVED: kept fix/popup-status-reset comments for clarity; logic is identical
    progressInterval = setInterval(() => {
        progress += (100 / 15) * 0.1; // 0.1s tick
        if (progress > 95) progress = 95; // cap at 95% until done

        bar.style.width = progress + '%';

        // Update timer every second
        if (Math.floor(progress * 15 / 100) > Math.floor((progress - (100 / 15) * 0.1) * 15 / 100)) {
            secondsLeft -= 1;
            if (secondsLeft < 1) secondsLeft = 1;
            timeEl.innerText = '~' + secondsLeft + 's';
        }
    }, 100);
}

function finishProgress(success) {
    clearInterval(progressInterval);
    clearTimeout(generationTimeout);
    const bar = document.getElementById('progressBar');
    const timeEl = document.getElementById('timeLeft');
    if (success) {
        bar.style.width = '100%';
        timeEl.innerText = 'Done!';
    } else {
        timeEl.innerText = 'Failed';
    }
    setTimeout(() => {
        resetGenerationUI();

        const statusEl = document.getElementById("status");

        if (statusEl) {
            statusEl.style.display = "block";
        }
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

// ========== COPY TO CLIPBOARD FUNCTION ==========
async function copyBlogToClipboard() {
    if (!generatedBlogMarkdown) {
        const statusEl = document.getElementById('status');
        statusEl.innerText = "❌ No blog generated yet. Please generate a blog first.";
        statusEl.className = "error-status";
        return;
    }

    try {
        await navigator.clipboard.writeText(generatedBlogMarkdown);
        const statusEl = document.getElementById('status');
        statusEl.innerText = "✅ Blog copied to clipboard! You can paste it anywhere.";
        statusEl.className = "success-status";
    } catch (err) {
        console.error("Copy failed:", err);
        // Fallback for older browsers
        const textarea = document.createElement("textarea");
        textarea.value = generatedBlogMarkdown;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
        const statusEl = document.getElementById('status');
        statusEl.innerText = "✅ Blog copied to clipboard (fallback method).";
        statusEl.className = "success-status";
    }
}
// ================================================

document.addEventListener('DOMContentLoaded', async () => {
    // Check email on every open
    chrome.storage.local.get({ userEmail: null, sessionToken: null }, ({ userEmail, sessionToken }) => {
        if (userEmail && sessionToken) showMainUI(userEmail);
        else showEmailSetup();
    });

    const statusEl = document.getElementById('status');
    const platformInputs = Array.from(document.querySelectorAll('input[name="platform"]'));
    const draftInput = document.getElementById('draftMode');

    chrome.storage.local.get({
        publishingPlatforms: ['devto'],
        publishAsDraft: false
    }, ({ publishingPlatforms, publishAsDraft }) => {

        platformInputs.forEach(input => {
            input.checked = publishingPlatforms.includes(input.value);
        });

        draftInput.checked = publishAsDraft;
    });

    const savePublishingSettings = () => {

        const selectedPlatforms = platformInputs
            .filter(input => input.checked)
            .map(input => input.value);

        if (selectedPlatforms.length === 0) {

            const devtoInput = platformInputs.find(input => input.value === 'devto');

            if (devtoInput) {
                devtoInput.checked = true;
                selectedPlatforms.push('devto');
            }
        }

        chrome.storage.local.set({
            publishingPlatforms: selectedPlatforms,
            publishAsDraft: draftInput.checked
        });
    };

    platformInputs.forEach(input => input.addEventListener('change', savePublishingSettings));
    draftInput.addEventListener('change', savePublishingSettings);

    // Load generated blog from storage
    chrome.storage.local.get(
        ["generatedBlog", "generatedProblemTitle"],
        (res) => {

            if (res.generatedBlog) {

                generatedBlog = res.generatedBlog;
                generatedBlogMarkdown = res.generatedBlog;
                generatedProblemTitle = res.generatedProblemTitle || "leetcode-blog";

                document.getElementById("exportSection").style.display = "block";
                document.getElementById("previewSection").style.display = "block";
                document.getElementById("blogEditor").value = generatedBlog;
                statusEl.innerText = "Publishing automation active";
            } else {
                statusEl.innerText = "Ready to generate blog";
                statusEl.className = "";
            }
        }
    );

    // Load and render recent posts history
    chrome.storage.local.get({ publishHistory: [] }, ({ publishHistory }) => {
        const listEl = document.getElementById('historyList');
        if (listEl) {
            if (!publishHistory.length) {
                listEl.innerHTML = '<div class="history-empty">No posts yet. Generate your first blog! ✍️</div>';
                return;
            }
            listEl.innerHTML = publishHistory.map(entry => {
                const date = new Date(entry.publishedAt).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
                const platforms = (entry.platforms || []).join(', ') || 'unknown';
                return `<div class="history-item" data-url="${entry.url || ''}">
                    <div class="history-item-title">${entry.title}</div>
                    <div class="history-item-meta">${date} &middot; ${platforms}</div>
                </div>`;
            }).join('');

            listEl.querySelectorAll('.history-item').forEach(item => {
                item.addEventListener('click', () => {
                    const url = item.dataset.url;
                    if (url) chrome.tabs.create({ url });
                });
            });
        }
    });

    // Select elements using your kebab-case naming standard to match popup.html
    const generateBtn = document.getElementById('generate-blog-btn');
    const btnText = document.getElementById('btn-text');
    const btnSpinner = document.getElementById('btn-spinner');
    const copyBtn = document.getElementById('copyBtn');

    generateBtn.addEventListener('click', async () => {
        const statusEl = document.getElementById('status');

        // 1. Enter Loading State: Disable buttons to prevent multi-clicks
        generateBtn.disabled = true;
        generateBtn.style.cursor = "not-allowed";
        if (copyBtn) copyBtn.disabled = true;

        // 2. Trigger your specific text and visual loading indicators
        if (btnText) btnText.textContent = "Generating Blog...";
        if (btnSpinner) btnSpinner.style.display = "inline-block";

        btnText.textContent = "Generating Blog...";
        btnSpinner.style.display = "inline-block";

        startProgress();

        try {
            const tabs = await chrome.tabs.query({
                active: true,
                currentWindow: true
            });

            const tab = tabs[0];

            const customPrompt = document
                .getElementById('customPrompt')
                .value
                .trim();

            if (!tab || !tab.url || !tab.url.includes("leetcode.com/problems/")) {
                statusEl.innerText = "Please open a LeetCode problem page!";
                statusEl.className = "error-status";

                // Clean up UI states and stop the progress tracking animation
                finishProgress(false);

                // Re-enable components using your kebab-case naming standard
                if (generateBtn) {
                    generateBtn.disabled = false;
                    generateBtn.style.cursor = "pointer";
                }
                if (btnText) btnText.textContent = "Generate Blog";
                if (btnSpinner) btnSpinner.style.display = "none";
                if (copyBtn) copyBtn.disabled = false;

                return;
            }

            try {

                await chrome.tabs.sendMessage(tab.id, {
                    type: 'MANUAL_TRIGGER',
                    custom_prompt: customPrompt
                });

            } catch (msgErr) {

                console.log("Re-injecting content script...");

                await chrome.scripting.executeScript({
                    target: { tabId: tab.id },
                    files: ['content.js']
                });

                finishProgress(false);

                if (generateBtn) generateBtn.disabled = false;
                if (copyBtn) copyBtn.disabled = false;

                await chrome.tabs.sendMessage(tab.id, { type: 'MANUAL_TRIGGER' });
                setTimeout(async () => {

                    try {
                        await chrome.tabs.sendMessage(tab.id, { type: 'MANUAL_TRIGGER' });
                    } catch (e2) {
                        statusEl.innerText = "Error: Please refresh LeetCode page!";
                        statusEl.className = "error-status";

                        // Handle progress reset and re-enable UI buttons consistently
                        finishProgress(false);

                        if (generateBtn) {
                            generateBtn.disabled = false;
                            generateBtn.style.cursor = "pointer";
                        }
                        if (btnText) btnText.textContent = "Generate Blog";
                        if (btnSpinner) btnSpinner.style.display = "none";
                        if (copyBtn) copyBtn.disabled = false;
                    }
                }, 500);
            }
        } catch (e) {

            console.error("Popup Error:", e);

            statusEl.innerText = "Error: " + e.message;

            if (statusEl) {
                statusEl.className = "error-status";
            }

            finishProgress(false);

            if (generateBtn) generateBtn.disabled = false;
            if (copyBtn) copyBtn.disabled = false;

            generateBtn.disabled = false;
            btnText.textContent = "Generate Blog";
            btnSpinner.style.display = "none";
        }
    });

    if (statusEl) {
        statusEl.innerText = "Publishing automation active";
    }
});

chrome.runtime.onMessage.addListener((request) => {

    if (request.type === "BLOG_READY") {

        chrome.storage.local.get(
            ["generatedBlog", "generatedProblemTitle"],
            (res) => {

                if (res.generatedBlog) {

                    generatedBlog = res.generatedBlog;
                    generatedBlogMarkdown = res.generatedBlog;
                    generatedProblemTitle = res.generatedProblemTitle || "leetcode-blog";

                    document.getElementById("exportSection").style.display = "block";
                    document.getElementById("previewSection").style.display = "block";
                    document.getElementById("blogEditor").value = generatedBlog;

                    document.getElementById("status").innerText = "Blog generated successfully!";

                    finishProgress(true);
                }
            }
        );
    }
});

// Status updates
chrome.runtime.onMessage.addListener((request) => {

    const statusEl = document.getElementById('status');
    const btn = document.getElementById('generate-blog-btn');
    const copyBtn = document.getElementById('copyBtn');

    if (request.type === 'STATUS_UPDATE') {

        statusEl.innerText = request.message;
        statusEl.className = "";

        // RESOLVED: kept finishProgress() calls from fix branch; added copyBtn from main
        if (request.status === 'success') {
            finishProgress(true);
            if (copyBtn) copyBtn.disabled = false;

            statusEl.innerText = request.message || "Successfully posted";
            statusEl.className = "success-status";
            btn.disabled = false;
            btn.style.cursor = "pointer";

        } else if (request.status === 'error') {
            finishProgress(false);
            if (copyBtn) copyBtn.disabled = false;

            statusEl.className = "error-status";
            btn.disabled = false;
            btn.style.cursor = "pointer";

        } else if (request.status === 'warning') {
            finishProgress(true);
            if (copyBtn) copyBtn.disabled = false;

            statusEl.className = "warning-status";
            btn.disabled = false;
            btn.style.cursor = "pointer";
        }

        const btnTextEl = document.getElementById('btn-text');
        const btnSpinnerEl = document.getElementById('btn-spinner');

        if (btnTextEl) btnTextEl.textContent = "Generate Blog";
        if (btnSpinnerEl) btnSpinnerEl.style.display = "none";
    }
});

// Dashboard button handler from main branch
document.getElementById('dashboardBtn')?.addEventListener('click', () => {
    chrome.tabs.create({
        url: chrome.runtime.getURL('dashboard.html')
    });
});

// Export Markdown handler from main branch
document.getElementById("exportMarkdownBtn")?.addEventListener("click", () => {
    const blob = new Blob([generatedBlogMarkdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${generatedProblemTitle}.md`;
    a.click();
    URL.revokeObjectURL(url);
});

// Export HTML
document.getElementById("exportHTMLBtn")?.addEventListener("click", () => {

    const html = convertMarkdownToHTML(generatedBlogMarkdown);
    const blob = new Blob([html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${generatedProblemTitle}.html`;
    a.click();
    URL.revokeObjectURL(url);
});

// Export PDF
document.getElementById("exportPDFBtn")?.addEventListener("click", () => {

    const container = document.createElement("div");
    container.style.padding = "20px";
    container.innerHTML = convertMarkdownToHTML(generatedBlogMarkdown);

    html2pdf()
        .set({
            margin: 0.5,
            filename: `${generatedProblemTitle}.pdf`,
            image: { type: "jpeg", quality: 1 },
            html2canvas: { scale: 2 },
            jsPDF: { unit: "in", format: "a4", orientation: "portrait" }
        })
        .from(container)
        .save();
});

// Publish button
document.getElementById("publishBtn")?.addEventListener("click", async () => {

    const editedBlog = document.getElementById("blogEditor").value;

    chrome.runtime.sendMessage({
        type: "PUBLISH_EDITED_BLOG",
        blog: editedBlog
    });

    document.getElementById("status").innerText = "Publishing edited blog...";
});

// Cancel button
document.getElementById("cancelPreviewBtn")?.addEventListener("click", () => {
    document.getElementById("previewSection").style.display = "none";
});

// ========== COPY BUTTON EVENT LISTENER ==========
const copyBtn = document.getElementById('copyBtn');
if (copyBtn) {
    copyBtn.addEventListener('click', copyBlogToClipboard);
}
// =================================================
