# Security Policy

## Supported Versions

The following versions of LeetLog AI currently receive security fixes and updates:

| Version                      | Supported                                  |
| ---------------------------- | ------------------------------------------ |
| `main` branch (latest)       | ✅ Active — security fixes applied         |
| Older forks / pinned commits | ❌ Not supported — please update to `main` |

LeetLog AI does not yet use versioned releases. All security support is on the `main` branch.

---

## Reporting a Vulnerability

**Please do not open a public GitHub Issue or Discussion for security vulnerabilities.** Doing so exposes the flaw to everyone before a fix is in place.

### Private Reporting Channel

Use GitHub's built-in **Private Security Advisory** system to report vulnerabilities confidentially:

👉 **[Report a vulnerability (private)](https://github.com/vanshaggarwal27/LeetcodeAI/security/advisories/new)**

This creates an encrypted, private thread visible only to the maintainers. No public disclosure occurs until a fix is released.

If you are unable to use GitHub's advisory system, you may contact the maintainer directly:

- **GitHub:** [@vanshaggarwal27](https://github.com/vanshaggarwal27)
- **Email:** _(open a private advisory above and request a direct email if needed)_

---

## What to Include in Your Report

To help us triage and fix the issue quickly, please provide as much of the following as possible:

1. **Description** — A clear summary of the vulnerability and its potential impact.
2. **Affected component** — Which part of the project is affected:
   - `backend/` — FastAPI server, AI generation logic, or publishing integrations
   - `extension/` — Chrome extension (content script, background worker, popup)
   - Configuration / secrets handling (`.env`, environment variables)
   - CI/CD or deployment pipeline
3. **Steps to reproduce** — A minimal, step-by-step sequence that triggers the issue.
4. **Environment details** — OS, Python version, Chrome version, Node version (if applicable).
5. **Potential impact** — Who could be affected and what an attacker could achieve (e.g. API key exfiltration, arbitrary code execution, data leakage).
6. **Suggested fix** _(optional)_ — If you have a proposed patch or mitigation, include it.

---

## Severity Classification

Not every vulnerability is equal. Use this table to self-assess severity before reporting — it helps us prioritise and respond appropriately:

| Severity        | Definition                                                            | LeetLog AI Examples                                                                                                                                  |
| --------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| 🔴 **Critical** | Direct exposure or exfiltration of secrets; RCE on the backend server | Any API key leaked in a response, log, or error; unauthenticated endpoint that executes arbitrary code                                               |
| 🟠 **High**     | Significant data breach or unauthorized action on behalf of the user  | `MEDIUM_TOKEN` / `HASHNODE_TOKEN` used to publish or delete posts without user consent; CORS misconfiguration allowing cross-origin reads of secrets |
| 🟡 **Medium**   | Limited impact requiring user interaction or specific conditions      | Extension content script injecting malicious content into LeetCode pages; SSRF via `BLOG_WEBHOOK_URL`                                                |
| 🟢 **Low**      | Minor information disclosure with no direct exploit path              | Backend error messages leaking stack traces or internal file paths                                                                                   |

Critical and High issues are treated with highest urgency.

---

## LeetLog AI Attack Surface

This section describes the specific areas of the codebase that are most security-sensitive. Researchers should focus here:

### Backend (`backend/`)

- **`/generate-blog` endpoint** — currently unauthenticated. Any caller who knows the URL can trigger Gemini API usage billed to the owner's key, and trigger publishing to all connected platforms. An authentication mechanism is a known gap.
- **Environment variables** — `GEMINI_API_KEY`, `DEVTO_API_KEY`, `HASHNODE_TOKEN`, `MEDIUM_TOKEN`, `BLOG_WEBHOOK_URL` are loaded from `backend/.env`. Any path traversal, logging misconfiguration, or error-response leak that exposes these is Critical.
- **`BLOG_WEBHOOK_URL`** — this is a user-supplied URL. If not validated, it could be abused for Server-Side Request Forgery (SSRF) to probe internal network resources, particularly on cloud deployments like Render.
- **Render deployment** — the backend is designed to run on Render. Misconfigured environment variable visibility or public log access on the hosting platform would expose all secrets.

### Chrome Extension (`extension/`)

- **`content.js`** — runs in the context of `https://leetcode.com/*` pages. A vulnerability here could allow a malicious LeetCode page to influence what data is sent to the backend.
- **`background.js`** — the service worker makes `POST` requests to the backend URL stored in the extension. If this URL can be tampered with (e.g. via a compromised extension update), requests including problem data could be redirected.
- **Extension storage** — if any API keys or tokens are ever cached in `chrome.storage`, they become accessible to other scripts with the `storage` permission. Keys must remain server-side only.
- **`popup.js` ↔ `background.js` messaging** — the internal message passing between popup and background worker should not be exploitable by injected scripts on the page.

---

## Sensitive Scope — API Keys and Secrets

LeetLog AI handles several **high-value API keys** in `backend/.env`. A vulnerability that allows any of these to be read, logged, transmitted, or otherwise exposed is considered **Critical** severity:

| Variable           | Purpose                            | Impact if Exposed                                                              |
| ------------------ | ---------------------------------- | ------------------------------------------------------------------------------ |
| `GEMINI_API_KEY`   | Google Gemini AI — blog generation | Attacker can run unlimited AI queries billed to the owner                      |
| `DEVTO_API_KEY`    | Dev.to publishing API              | Attacker can publish, edit, or delete articles on the owner's Dev.to account   |
| `HASHNODE_TOKEN`   | Hashnode publishing token          | Attacker can publish or modify posts on the owner's Hashnode blog              |
| `MEDIUM_TOKEN`     | Medium integration token           | Attacker can publish content under the owner's Medium account                  |
| `BLOG_WEBHOOK_URL` | Custom blog webhook endpoint       | May carry auth tokens in the URL; attacker can trigger arbitrary webhook calls |

**These keys must never appear in:**

- Any log output (server logs, browser console, extension storage)
- API responses returned to the Chrome extension or any client
- Committed source code or version control history
- Error messages or stack traces visible to end users

If you discover that any of these are being leaked or are at risk of exposure, please report it immediately via the private advisory link above.

---

## Expected Response Timeline

| Stage                           | Target                                             |
| ------------------------------- | -------------------------------------------------- |
| Initial acknowledgement         | Within **3 business days** of receiving the report |
| Triage and severity assessment  | Within **7 days**                                  |
| Fix or mitigation deployed      | Within **14–30 days** depending on severity        |
| Public disclosure (coordinated) | After a fix is available and deployed              |

Critical issues (e.g. live API key exposure) will be treated with highest urgency and addressed as quickly as possible.

---

## What Happens After You Report

Here is exactly what to expect after submitting a private advisory:

1. **Acknowledgement** — A maintainer will acknowledge receipt within 3 business days and confirm they can reproduce or understand the issue.
2. **Severity agreement** — We will discuss and agree on a severity rating with you. If we disagree, we will explain our reasoning.
3. **Fix development** — We develop a fix on a private branch. You may be invited to review the patch.
4. **Coordinated disclosure date** — We agree on a disclosure date together. For Critical issues this is as soon as the fix is deployed. For lower severity, we aim for within 30 days.
5. **Public advisory** — A GitHub Security Advisory is published, crediting you (unless you prefer anonymity).
6. **CVE assignment** — For significant vulnerabilities we will request a CVE identifier via GitHub.

---

## Out of Scope

The following are **not** considered security vulnerabilities for the purposes of this policy:

- Missing features or general bugs that do not have a security impact
- Issues in third-party services (Dev.to, Hashnode, Medium, Gemini) — please report those to the respective platforms
- Rate limiting or quota exhaustion on external APIs
- Issues that only affect a local development environment where no real credentials are used
- UI/UX problems in the extension popup
- Suggestions or feature requests (please use [GitHub Issues](https://github.com/vanshaggarwal27/LeetcodeAI/issues) for those)
- Vulnerabilities in dependencies that have no demonstrated exploitable path in this project

---

## What Not to Do

- ❌ **Do not open a public GitHub Issue** describing the vulnerability — this publicly discloses it before a fix exists.
- ❌ **Do not post in GitHub Discussions** or any public forum.
- ❌ **Do not exploit the vulnerability** beyond what is necessary to confirm it exists.
- ❌ **Do not share details** with third parties until a coordinated disclosure has been agreed upon with the maintainers.
- ❌ **Do not perform automated scanning** against the live Render deployment — this consumes API quota billed to the maintainer.

---

## Safe Harbour

LeetLog AI supports good-faith security research. If you:

- Report the vulnerability promptly and privately
- Do not access, modify, or delete data beyond what is necessary to demonstrate the issue
- Do not perform denial-of-service attacks or disrupt the service
- Do not violate any applicable laws in the course of your research

...then the maintainers commit to **not pursuing legal action** against you in connection with your research and to working with you in good faith toward a resolution.

---

## Disclosure Policy

LeetLog AI follows **coordinated (responsible) disclosure**. Once a fix is merged and deployed, the maintainers will:

1. Publish a GitHub Security Advisory summarising the vulnerability (without sensitive exploit details).
2. Credit the reporter (unless they prefer to remain anonymous).
3. Tag a new release if appropriate.
4. Request a CVE identifier for significant vulnerabilities.

---

## Security Hall of Fame

We are grateful to everyone who has responsibly disclosed vulnerabilities to us. Reporters who follow this policy will be listed here (with their permission):

_No vulnerabilities have been reported yet. You could be the first!_

---

Thank you for helping keep LeetLog AI and its users safe. 🙏
