const API_BASE_URL = "https://leetcodeai-backend.onrender.com";

async function parseApiResponse(response) {
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(data.detail || data.message || `Request failed with status ${response.status}`);
    }
    return data;
}

function authHeaders(userEmail, sessionToken) {
    return {
        "Content-Type": "application/json",
        "X-User-Email": userEmail,
        "Authorization": `Bearer ${sessionToken}`
    };
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === 'GENERATE_BLOG') {
        const { title, description, code, author, client_time, custom_prompt, difficulty, language, topics } = request.payload;
        chrome.storage.local.get({
            publishingPlatforms: ['devto'],
            publishAsDraft: false,
            userEmail: null,
            sessionToken: null,
        }, async ({ publishingPlatforms, publishAsDraft, userEmail, sessionToken }) => {
            if (!userEmail || !sessionToken) {
                chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', message: 'Please log in before publishing.', status: 'error' });
                return;
            }
            fetch(`${API_BASE_URL}/generate-blog`, {
                method: "POST",
                headers: authHeaders(userEmail, sessionToken),
                body: JSON.stringify({
                    title, description, code, author, client_time, custom_prompt, difficulty, language,
                    tags: (topics && topics.length > 0) ? topics : null,
                    platforms: publishingPlatforms,
                    publish_as_draft: publishAsDraft
                })
            })
                .then(parseApiResponse)
                .then(data => {
                    if (data.status === 'success' || data.status === 'partial_success') {
                        const generatedBlog =
                            data.data?.blog_content || "";

                        chrome.storage.local.set({
                            generatedBlog,
                            generatedProblemTitle: title
                        }, () => {

                            chrome.runtime.sendMessage({
                                type: "BLOG_READY"
                            });

                        });
                    }

                    if (data.status === 'success' || data.status === 'partial_success') {
                        const platforms = data.data?.platforms || [];
                        const postedPlatforms = platforms
                            .filter(result => result.status === 'success')
                            .map(result => result.platform);
                        const devtoResult = platforms.find(r => r.platform === 'devto' && r.status === 'success');
                        chrome.storage.local.get({ publishHistory: [] }, (res) => {
                            const entry = {
                                title: title,
                                url: devtoResult?.url || null,
                                publishedAt: client_time || new Date().toISOString(),
                                platforms: postedPlatforms
                            };
                            const history = res.publishHistory;
                            history.unshift(entry);
                            chrome.storage.local.set({ publishHistory: history.slice(0, 10) });
                        });
                        const failedPlatforms = platforms
                            .filter(r => r.status === 'error').map(r => r.platform);

                        const entry = {
                            title,
                            date: client_time || new Date().toISOString(),
                            platforms: postedPlatforms,
                            status: data.status,
                            author,
                            user_email: userEmail,
                        };

                        const historyKey = `publishHistory_${userEmail}`;
                        chrome.storage.local.get({ [historyKey]: [] }, (res) => {
                            const history = (res[historyKey] || []).filter(h => h.title !== entry.title);
                            history.unshift(entry);
                            chrome.storage.local.set({ [historyKey]: history.slice(0, 100) });
                        });

                        fetch(`${API_BASE_URL}/dashboard/record`, {
                            method: "POST",
                            headers: authHeaders(userEmail, sessionToken),
                            body: JSON.stringify(entry)
                        }).catch(() => { });
                        chrome.runtime.sendMessage({
                            type: 'STATUS_UPDATE',
                            message:
                                failedPlatforms.length > 0
                                    ? `Posted to ${postedPlatforms.join(', ')}; failed: ${failedPlatforms.join(', ')}`
                                    : postedPlatforms.length > 0
                                        ? `Posted to ${postedPlatforms.join(', ')}`
                                        : 'Posted',
                            status: data.status === 'partial_success' ? 'warning' : 'success',
                            platforms
                        });
                    } else {
                        const platformErrors = data.data?.platforms
                            ?.filter(result => result.status === 'error')
                            ?.map(result => `${result.platform}: ${result.message}`)
                            ?.join('; ');
                        const errMsg = platformErrors || data.message || JSON.stringify(data);
                        chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', message: 'Error: ' + errMsg, status: 'error' });
                    }
                })
                .catch(error => {
                    chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', message: 'Network Error: ' + error.message, status: 'error' });
                });
        });
    }
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === 'PUBLISH_EDITED_BLOG') {
        const { blog } = request;
        chrome.storage.local.get({
            publishingPlatforms: ['devto'],
            publishAsDraft: false,
            userEmail: null,
            sessionToken: null,
            generatedProblemTitle: 'leetcode-blog'
        }, async ({ publishingPlatforms, publishAsDraft, userEmail, sessionToken, generatedProblemTitle }) => {
            if (!userEmail || !sessionToken) {
                const errMsg = 'Please log in before publishing.';
                chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', message: errMsg, status: 'error' });
                sendResponse({ success: false, error: errMsg });
                return;
            }
            fetch(`${API_BASE_URL}/publish-blog`, {
                method: "POST",
                headers: authHeaders(userEmail, sessionToken),
                body: JSON.stringify({
                    title: generatedProblemTitle,
                    content: blog,
                    platforms: publishingPlatforms,
                    publish_as_draft: publishAsDraft,
                    author: "Anonymous Developer"
                })
            })
                .then(parseApiResponse)
                .then(data => {
                    if (data.status === 'success' || data.status === 'partial_success') {
                        const platforms = data.data?.platforms || [];
                        const postedPlatforms = platforms
                            .filter(r => r.status === 'success').map(r => r.platform);
                        const failedPlatforms = platforms
                            .filter(r => r.status === 'error').map(r => r.platform);

                        const entry = {
                            title: generatedProblemTitle,
                            date: new Date().toISOString(),
                            platforms: postedPlatforms,
                            status: data.status,
                            author: "Anonymous Developer",
                            user_email: userEmail,
                        };

                        const historyKey = `publishHistory_${userEmail}`;
                        chrome.storage.local.get({ [historyKey]: [] }, (res) => {
                            const history = (res[historyKey] || []).filter(h => h.title !== entry.title);
                            history.unshift(entry);
                            chrome.storage.local.set({ [historyKey]: history.slice(0, 100) });
                        });

                        fetch(`${API_BASE_URL}/dashboard/record`, {
                            method: "POST",
                            headers: authHeaders(userEmail, sessionToken),
                            body: JSON.stringify(entry)
                        }).catch(() => { });

                        const successMsg = failedPlatforms.length > 0
                            ? `Posted to ${postedPlatforms.join(', ')}; failed: ${failedPlatforms.join(', ')}`
                            : postedPlatforms.length > 0
                                ? `Posted to ${postedPlatforms.join(', ')}`
                                : 'Posted';

                        chrome.runtime.sendMessage({
                            type: 'STATUS_UPDATE',
                            message: successMsg,
                            status: data.status === 'partial_success' ? 'warning' : 'success',
                            platforms
                        });
                        sendResponse({ success: true, message: successMsg, data });
                    } else {
                        const platformErrors = data.data?.platforms
                            ?.filter(result => result.status === 'error')
                            ?.map(result => `${result.platform}: ${result.message}`)
                            ?.join('; ');
                        const errMsg = platformErrors || data.message || JSON.stringify(data);
                        chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', message: 'Error: ' + errMsg, status: 'error' });
                        sendResponse({ success: false, error: errMsg });
                    }
                })
                .catch(error => {
                    const errMsg = 'Network Error: ' + error.message;
                    chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', message: errMsg, status: 'error' });
                    sendResponse({ success: false, error: errMsg });
                });
        });
        return true;
    }
});
