# Glossary

A reference for key terms, acronyms, and project-specific concepts used throughout LeetLog AI. If you encounter an unfamiliar term in the codebase or documentation, look it up here first.

> Terms are grouped by category and listed alphabetically within each group. Cross-links to relevant documentation are provided where applicable.

---

## Table of Contents

- [Project Terms](#-project-terms)
- [Chrome Extension Terms](#-chrome-extension-terms)
- [Backend Terms](#-backend-terms)
- [Security Terms](#-security-terms)
- [AI Terms](#-ai-terms)
- [Publishing Platform Terms](#-publishing-platform-terms)
- [Workflow & Contribution Terms](#-workflow--contribution-terms)
- [Architecture Terms](#-architecture-terms)
- [Troubleshooting Terms](#-troubleshooting-terms)

---

## 🗂 Project Terms

**GSSoC (GirlScript Summer of Code)**
An open-source program that mentors contributors through real-world projects. LeetLog AI participates as a GSSoC 2026 project. Contributors accepted into GSSoC work on assigned issues under maintainer guidance.

**LeetCode**
A competitive programming platform where users solve algorithmic and data structure problems. LeetLog AI watches your LeetCode session to detect when you solve a problem and automatically generates a blog post from your solution.

**LeetLog AI**
The official project name. The repository URL uses the historical name `LeetcodeAI`, but all current documentation and branding refer to the project as LeetLog AI. It is a Chrome Extension and Python backend system that automatically generates and publishes blog posts from solved LeetCode problems.

**`main` branch**
The primary, production-ready branch of this repository. All contributions are merged into `main` via pull requests. This is also the only branch that receives security fixes. See [SECURITY.md](./SECURITY.md).

**Maintainer**
The repository owner (`@vanshaggarwal27`) or a designated reviewer who has write access to the repo, reviews pull requests, and assigns issues to contributors.

---

## 🧩 Chrome Extension Terms

**Background Script / Service Worker (`background.js`)**
A script that runs in the background of Chrome, separate from any webpage. In LeetLog AI, `background.js` acts as the service worker — it receives messages from `content.js` and `popup.js`, and makes the `POST` request to the FastAPI backend. Because it is a service worker (MV3), it does not run continuously; it wakes up on demand and goes idle when not needed.

**Content Script (`content.js`)**
A JavaScript file that is injected into and runs in the context of a specific web page — in this case, `https://leetcode.com/*`. It can read and interact with the DOM of the LeetCode page. In LeetLog AI, `content.js` is responsible for scraping the problem title, description, your solution code, and your LeetCode username directly from the page.

**Developer Mode**
A Chrome setting (`chrome://extensions/` → toggle "Developer mode") that allows you to load unpacked extensions directly from your local filesystem, bypassing the Chrome Web Store. Required during development and local testing.

**Load Unpacked**
The Chrome extension loading mechanism used during development. Instead of installing from the Web Store, you point Chrome directly at the `extension/` folder on your disk. Any code changes take effect after clicking the reload button on the extensions page.

**Manifest V3 (MV3)**
The current version of the Chrome Extension platform specification. It introduces service workers (replacing persistent background pages), stricter content security policies, and declarative network request rules. LeetLog AI's `manifest.json` uses MV3. Contributors working on the extension should be familiar with MV3 constraints.

**`manifest.json`**
The configuration file at the root of the `extension/` folder that defines the extension's name, version, permissions, content scripts, service worker, and popup. Chrome reads this file when loading the extension.

**Popup (`popup.html` / `popup.js`)**
The small UI window that appears when you click the LeetLog AI icon in the Chrome toolbar. `popup.html` defines the layout and `popup.js` handles button clicks, platform selection, and displaying per-platform publish status back to the user.

**`chrome.storage`**
A Chrome Extension API for persisting data across sessions. It is similar to `localStorage` but accessible from both content scripts and background scripts. In LeetLog AI, API keys must **never** be stored here — they must remain server-side only.

---

## ⚙️ Backend Terms

**`.env` file**
A plain-text file located at `backend/.env` that stores environment-specific configuration values, primarily API keys and secrets. It is listed in `.gitignore` and must never be committed to version control. The backend reads it at startup using the `python-dotenv` library. See [SECURITY.md](./SECURITY.md) for a full list of variables.

**`conftest.py`**
A special pytest file located at `backend/tests/conftest.py` that defines shared test fixtures available to all test files. In LeetLog AI, it contains mock fixtures for external API calls (Gemini, Dev.to, MongoDB) so that tests never make real network requests.

**`devto.py`**
The publishing module in `backend/devto.py`. Despite its name it is the general publisher registry — it contains client logic for Dev.to, Hashnode, Medium, and the custom webhook. When adding a new platform, this is the file to extend.

**Endpoint (`/generate-blog`)**
The single HTTP `POST` route exposed by the FastAPI backend. The Chrome extension calls this endpoint with problem data (title, code, username, selected platforms). The backend responds with a JSON object indicating publish success or failure per platform.

**FastAPI**
The Python web framework used for the LeetLog AI backend. It provides automatic API documentation at `/docs`, async request handling, and type validation via Pydantic. See [fastapi.tiangolo.com](https://fastapi.tiangolo.com/).

**`main.py`**
The entry point for the backend. It defines the FastAPI app instance, registers the `/generate-blog` route, and starts the uvicorn server when run directly (`python main.py`).

**Mock Fixture**
A pytest fixture that replaces a real external dependency (like a Gemini API call or a MongoDB query) with a fake implementation during testing. This ensures tests are fast, deterministic, and do not consume API quota. All mock fixtures are defined in `conftest.py`.

**MongoDB / `MONGODB_URI`**
The database used by the backend for persistence (e.g. logging generated posts). You can run it locally via Docker (`docker run -d -p 27017:27017 --name mongodb mongo`) or use MongoDB Atlas (cloud-hosted). The connection string is stored in `.env` as `MONGODB_URI`.

**PEP 8**
The official Python style guide. All backend Python code in LeetLog AI should follow PEP 8 conventions — `snake_case` naming, 4-space indentation, maximum line length of 79 characters, etc.

**pytest**
The testing framework used for the backend. Run the full test suite with `make test` or `cd backend && pytest -v`. New integrations should include corresponding tests.

**Unit Test**
A test that verifies the behavior of a small, isolated piece of functionality such as a function or module.

**Integration Test**
A test that verifies multiple components work together correctly, such as the interaction between the FastAPI endpoint and publishing modules.

**Render**
The cloud platform used to deploy the LeetLog AI backend for production. Environment variables (`GEMINI_API_KEY`, etc.) are configured in the Render dashboard and are never stored in code. The deployed URL is set as `API_BASE_URL` in `background.js`.

**uvicorn**
The ASGI server that runs the FastAPI application. It is started automatically when you run `python main.py`. The start command on Render is `uvicorn main:app --host 0.0.0.0 --port 10000`.

**Virtual Environment (`venv`)**
An isolated Python environment created with `python -m venv venv`. It keeps the project's dependencies separate from your system Python installation. Always activate it before running or testing the backend.

---

## 🔒 Security Terms

**API Key**
A secret credential used to authenticate requests to third-party services. API keys must never be committed to the repository or exposed in client-side code.

**Secret**
Any sensitive value that grants access to services or resources, including API keys, access tokens, database credentials, and webhook URLs.

**`.gitignore`**
A Git configuration file that specifies which files and folders should not be tracked by version control. Sensitive files such as `.env` should always be listed here.

**Least Privilege Principle**
A security practice where users, services, and applications are granted only the permissions necessary to perform their tasks.

## 🤖 AI Terms

**`ai.py`**
The module in `backend/ai.py` responsible for blog generation. It constructs the prompt, calls the Gemini API, and returns the generated blog post as a structured string. It is called by `main.py` after receiving a request at `/generate-blog`.

**Blog Generation**
The process by which LeetLog AI takes a LeetCode problem title, description, solution code, and username, and uses the Gemini API to produce a fully formatted blog post including: explanation, intuition behind the approach, step-by-step walkthrough, solution code block, time/space complexity analysis, and a conclusion.

**Gemini API (`GEMINI_API_KEY`)**
Google's generative AI API, used to produce the blog post content. The API key is stored in `.env` as `GEMINI_API_KEY`. Calls are made from `ai.py` using the `google-generativeai` Python SDK. Leaking this key allows an attacker to make AI requests billed to the repository owner.

**Prompt**
The instruction text sent to the Gemini API that tells it what kind of output to generate. In LeetLog AI, the prompt is constructed dynamically in `ai.py` from the scraped problem data and includes formatting instructions for the blog post structure.

**Prompt Engineering**
The practice of carefully crafting the prompt text sent to an AI model to get the most useful and consistently formatted output. Contributors modifying `ai.py` should test prompt changes across several LeetCode problems of varying difficulty to ensure quality output.

---

## 📤 Publishing Platform Terms

**Custom Webhook / `BLOG_WEBHOOK_URL`**
An HTTP endpoint on a personal blog or CMS that LeetLog AI can `POST` a generated blog to. The payload includes `title`, `body_markdown`, `tags`, `published`, and `source` fields. The URL is stored in `.env`. If it contains an authentication token as a query parameter, treat it as a secret.

**Dev.to API Key (`DEVTO_API_KEY`)**
A personal API key from [dev.to/settings/extensions](https://dev.to/settings/extensions) that authenticates publishing requests to Dev.to. Stored in `.env`. Leaking this key allows an attacker to publish, edit, or delete articles on your Dev.to account.

**Hashnode Publication ID (`HASHNODE_PUBLICATION_ID`)**
A unique identifier for your Hashnode blog (not your account). Required alongside `HASHNODE_TOKEN` to publish to the correct blog. Find it in your Hashnode blog settings.

**Hashnode Token (`HASHNODE_TOKEN`)**
A developer API token from Hashnode that authenticates publishing requests. Stored in `.env`. Leaking this token allows an attacker to publish or modify posts on your Hashnode blog.

**Medium Integration Token (`MEDIUM_TOKEN`)**
A personal access token from Medium that authenticates publishing requests. Stored in `.env`. Leaking this token allows an attacker to publish content under your Medium account.

**Medium User ID (`MEDIUM_USER_ID`)**
Your Medium account's unique identifier. Required alongside `MEDIUM_TOKEN` to route posts to the correct account. Retrieved from the Medium API once authenticated.

**Per-platform Status**
The JSON response field returned by `/generate-blog` that reports success or failure for each selected publishing platform independently. For example, a post might succeed on Dev.to but fail on Hashnode if the token is invalid. The popup displays this status to the user.

---

## 🔄 Workflow & Contribution Terms

**Conventional Commits**
A commit message standard used in this project. Format: `type: short description`. Common types: `feat` (new feature), `fix` (bug fix), `docs` (documentation), `refactor` (code cleanup), `chore` (config/dependency), `test` (tests). Example: `feat: add Hashnode publishing support`. See [CONTRIBUTING.md](./CONTRIBUTING.md).

**Fork**
A personal copy of the LeetLog AI repository under your own GitHub account. You make all changes in your fork and then open a pull request back to the original repo. Create one by clicking "Fork" on the GitHub repo page.

**Issue Assignment**
Before starting work on an issue, comment on it to request assignment. A maintainer will assign it to you. Working on unassigned issues risks your PR being closed if someone else is already working on the same thing.

**`good first issue`**
A GitHub label applied to issues that are well-scoped and suitable for contributors new to the codebase. A great starting point if this is your first contribution to LeetLog AI.

**Pull Request (PR)**
A request to merge your changes from your fork's branch into the `main` branch of the original repository. PRs should reference the issue they close (`Closes #<number>`), describe what changed, and explain how to test the change. See [CONTRIBUTING.md](./CONTRIBUTING.md) for the full PR checklist.

**`upstream`**
The original `vanshaggarwal27/LeetcodeAI` repository, as opposed to your personal fork. You add it as a remote with `git remote add upstream https://github.com/vanshaggarwal27/LeetcodeAI.git` and sync with `git fetch upstream` before opening a PR to avoid merge conflicts.

---

## 🏗 Architecture Terms

**Chrome Extension ↔ Backend Communication**
The data flow in LeetLog AI works as follows:

1. `content.js` scrapes problem data from the LeetCode page and sends it to `background.js` via Chrome's message passing API.
2. `background.js` (service worker) receives the data and makes a `POST` request to the FastAPI backend at `/generate-blog`.
3. The backend generates the blog via Gemini (`ai.py`) and publishes to selected platforms (`devto.py`).
4. The backend returns a per-platform status JSON to `background.js`.
5. `background.js` forwards the result to `popup.js`, which displays it in the popup UI.

**`API_BASE_URL`**
A constant in `background.js` that points to the FastAPI backend. Set to the Render deployment URL in production. For local testing, temporarily change it to `http://localhost:10000`.

**`backend/`**
The directory containing the entire Python FastAPI server: `main.py` (routes), `ai.py` (Gemini integration), `devto.py` (publishing clients), `requirements.txt` (dependencies), `tests/` (test suite), and `.env` (secrets, not committed).

**`extension/`**
The directory containing the entire Chrome Extension: `manifest.json` (config), `content.js` (page scraper), `background.js` (service worker), `popup.html` (UI), `popup.js` (UI logic).

---

## 🛠 Troubleshooting Terms

**HTTP 401 Unauthorized**
An error indicating that authentication credentials are missing, invalid, or expired.

**HTTP 404 Not Found**
An error indicating that the requested route or resource does not exist.

**HTTP 500 Internal Server Error**
A generic server-side error indicating that an unexpected exception occurred while processing a request.

---

_Something missing? If you encounter a term not listed here, please [open an issue](https://github.com/vanshaggarwal27/LeetcodeAI/issues/new) or submit a PR adding it._
