const API_BASE_URL = "https://leetcodeai-backend.onrender.com";
//const API_BASE_URL = "http://localhost:10000";
function getUserEmail() {
    return new Promise(resolve => {
        chrome.storage.local.get({ userEmail: null }, ({ userEmail }) => resolve(userEmail));
    });
}

function getUserEmail() {
    return new Promise(resolve => {
        chrome.storage.local.get({ userEmail: null }, ({ userEmail }) => resolve(userEmail));
    });
}
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === 'GENERATE_BLOG') {
        const { title, description, code, author, client_time, custom_prompt, difficulty } = request.payload;
        chrome.storage.local.get({
            publishingPlatforms: ['devto'],
            publishAsDraft: false,
            userEmail: null,
        }, async ({ publishingPlatforms, publishAsDraft, userEmail }) => {
            if (!userEmail) {
                chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', message: 'Please set your email in the extension settings before publishing.', status: 'error' });
                return;
            }
            fetch(`${API_BASE_URL}/generate-blog`, {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-User-Email": userEmail },
                body: JSON.stringify({
                    title, description, code, author, client_time, custom_prompt, difficulty,
                    platforms: publishingPlatforms,
                    publish_as_draft: publishAsDraft
                })
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success' || data.status === 'partial_success'){
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
                        .map(result => result.platform)
                        .join(', ');
                        const devtoResult = platforms.find(r => r.platform === 'devto' && r.status === 'success');
                        chrome.storage.local.get({ publishHistory: [] }, (res) => {
                            const entry = {
                                title: title,
                                url: devtoResult?.url || null,
                                publishedAt: client_time || new Date().toISOString(),
                                platforms: postedPlatforms ? postedPlatforms.split(', ').filter(p => p) : []
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
                        headers: { "Content-Type": "application/json", "X-User-Email": userEmail },
                        body: JSON.stringify(entry)
                    }).catch(() => {});
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