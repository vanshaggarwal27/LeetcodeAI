# 🤝 Contributing to LeetLog AI

First off — **thank you!** Whether it's your first open-source contribution or your hundredth, we're glad you're here. LeetLog AI is part of **GSSoC 2025** and welcomes developers of all skill levels.

---

## 📋 Table of Contents

- [Code of Conduct](#-code-of-conduct)
- [How Can I Contribute?](#-how-can-i-contribute)
- [Contribution Workflow (Step-by-Step)](#-contribution-workflow-step-by-step)
  - [Step 1 — Find or Create an Issue](#step-1--find-or-create-an-issue)
  - [Step 2 — Fork & Clone](#step-2--fork--clone)
  - [Step 3 — Create a Branch](#step-3--create-a-branch)
  - [Step 4 — Set Up the Backend](#step-4--set-up-the-backend)
  - [Step 5 — Set Up Environment Variables](#step-5--set-up-environment-variables)
  - [Step 6 — Run the Server Locally](#step-6--run-the-server-locally)
  - [Step 7 — Load the Chrome Extension](#step-7--load-the-chrome-extension)
  - [Step 8 — Make Your Changes](#step-8--make-your-changes)
  - [Step 9 — Commit with a Good Message](#step-9--commit-with-a-good-message)
  - [Step 10 — Push & Open a Pull Request](#step-10--push--open-a-pull-request)
- [Coding Standards](#-coding-standards)
- [Reporting Bugs](#-reporting-bugs)

---

## 🙌 Code of Conduct

By participating in this project, you agree to be kind and constructive. Harassment, discrimination, or disrespectful behavior of any kind will not be tolerated. Let's keep this a welcoming space for everyone.

---

## 💡 How Can I Contribute?

Not sure where to start? Here are some great entry points:

| Type | What to do |
|---|---|
| 🐛 **Fix a bug** | Check [Issues](https://github.com/vanshaggarwal27/LeetcodeAI/issues) for open bugs |
| ✨ **Add a feature** | Look for issues labeled `enhancement` or `good first issue` |
| 📖 **Improve docs** | Fix typos, add examples, clarify the README or CONTRIBUTING guide |
| 🧪 **Write tests** | Help build a test suite for the backend API endpoints |
| 🎨 **Improve the UI** | Polish the Chrome extension popup design |
| 🌐 **Add platform support** | Extend `devto.py` to support Hashnode, Medium, etc. |

> 💬 **Always comment on an issue before starting work**, so maintainers can assign it to you and avoid duplicate effort.

---

## 🔄 Contribution Workflow (Step-by-Step)

### Step 1 — Find or Create an Issue

- Browse [open issues](https://github.com/vanshaggarwal27/LeetcodeAI/issues)
- If your idea doesn't have an issue yet, [create one](https://github.com/vanshaggarwal27/LeetcodeAI/issues/new) describing the problem or feature
- **Wait for a maintainer to assign the issue to you** before starting work

---

### Step 2 — Fork & Clone

Click **Fork** on the top-right of the GitHub repo page, then clone your fork:

```bash
git clone https://github.com/<your-username>/LeetcodeAI.git
cd LeetcodeAI
```

Add the original repo as `upstream` so you can stay in sync:

```bash
git remote add upstream https://github.com/vanshaggarwal27/LeetcodeAI.git
```

---

### Step 3 — Create a Branch

**Never work directly on `main`.** Create a dedicated branch for your change:

```bash
# For a new feature:
git checkout -b feat/add-hashnode-support

# For a bug fix:
git checkout -b fix/devto-retry-logic

# For documentation:
git checkout -b docs/improve-contributing-guide
```

> Branch names should be lowercase, hyphen-separated, and descriptive.

---

### Step 4 — Set Up the Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### Step 5 — Set Up Environment Variables

Create a `.env` file inside the `backend/` directory:

```bash
# backend/.env
GEMINI_API_KEY=your_google_gemini_key_here
DEVTO_API_KEY=your_devto_api_key_here
```

Where to get your keys:
- **Gemini API Key** → [Google AI Studio](https://aistudio.google.com/app/apikey)
- **Dev.to API Key** → [Dev.to Settings → Extensions](https://dev.to/settings/extensions)

> ⚠️ **Never commit your `.env` file.** It is already in `.gitignore`.

---

### Step 6 — Run the Server Locally

```bash
# From inside the backend/ directory (with venv activated)
python main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:10000 (Press CTRL+C to quit)
```

You can verify it's live by visiting: [http://localhost:10000](http://localhost:10000)

---

### Step 7 — Load the Chrome Extension

To test the extension against your local server:

1. Open Chrome and go to `chrome://extensions/`
2. Enable **Developer mode** (toggle in the top-right corner)
3. Click **"Load unpacked"**
4. Select the `extension/` folder from the cloned repo

> The extension in `background.js` points to the deployed Render URL by default.
> For local testing, temporarily change `API_URL` in `background.js`:
> ```js
> const API_URL = "http://localhost:10000/generate-blog";
> ```

---

### Step 8 — Make Your Changes

Write your code, fix the bug, or update the docs. Keep these things in mind:

- Follow the [Coding Standards](#-coding-standards) below
- Make sure the backend still starts without errors after your changes
- Test your changes end-to-end if possible (open a LeetCode problem, click the extension)

---

### Step 9 — Commit with a Good Message

Use the **Conventional Commits** format:

```bash
git add .
git commit -m "feat: add Hashnode publishing support"
```

| Prefix | When to use |
|---|---|
| `feat:` | A new feature |
| `fix:` | A bug fix |
| `docs:` | Documentation only changes |
| `refactor:` | Code cleanup without feature/fix |
| `chore:` | Dependency updates, config changes |
| `test:` | Adding or updating tests |

---

### Step 10 — Push & Open a Pull Request

First, sync with the latest `main` to avoid merge conflicts:

```bash
git fetch upstream
git rebase upstream/main
```

Then push your branch and open a PR:

```bash
git push origin feat/your-branch-name
```

Go to your fork on GitHub — you'll see a **"Compare & pull request"** button. Click it and fill in the PR template:

- **Title**: Short and descriptive (e.g., `feat: add Hashnode publishing`)
- **Description**:
  - What does this PR do?
  - Which issue does it close? (use `Closes #<issue-number>`)
  - How can reviewers test it?
- **Screenshots**: Include before/after screenshots for any UI changes

> A maintainer will review your PR within a few days. Be ready to address feedback — it's a normal part of the process! 🙂

---

## 🎨 Coding Standards

### Python (Backend)
- Follow [PEP 8](https://peps.python.org/pep-0008/) style guidelines
- Use `snake_case` for all variables and functions
- Add a docstring to every new function explaining what it does
- Keep each function focused on a single responsibility
- Handle exceptions explicitly — avoid bare `except:` clauses

### JavaScript (Extension)
- Use `camelCase` for variables and function names
- Prefer `async/await` over `.then()` chains for readability
- Remove `console.log` debug statements before submitting a PR
- Keep logic in `background.js` (networking) separate from `popup.js` (UI)

### General Rules
- ✅ One feature or fix per PR
- ✅ No `.env` files or API keys in any commit — ever
- ✅ Update the `README.md` if your change affects setup or usage
- ✅ Keep diffs small and focused — easier to review, faster to merge

---

## 🐛 Reporting Bugs

Found something broken? Please [open an issue](https://github.com/vanshaggarwal27/LeetcodeAI/issues/new) and include:

- **Description** — What is the bug?
- **Steps to Reproduce** — Exact steps to trigger it
- **Expected Behavior** — What should happen?
- **Actual Behavior** — What actually happens?
- **Environment** — OS, Chrome version, Python version
- **Logs / Screenshots** — Any error messages from the console or terminal

---

Thank you for being part of LeetLog AI! Every contribution — big or small — matters. 🚀
