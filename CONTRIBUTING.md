# 🤝 Contributing to LeetLog AI

Thank you for your interest in contributing! LeetLog AI is an open-source project under **GSSoC 2025**, and we welcome contributions from developers of all experience levels.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Setting Up Your Environment](#setting-up-your-environment)
- [Making a Pull Request](#making-a-pull-request)
- [Coding Standards](#coding-standards)
- [Reporting Bugs](#reporting-bugs)

---

## 🙌 Code of Conduct

By participating in this project, you agree to be respectful and inclusive. Harassment, discrimination, or disrespectful behavior of any kind will not be tolerated.

---

## 💡 How Can I Contribute?

Here are some great ways to get started:

- 🐛 **Fix bugs** — Check the [Issues](../../issues) tab for bug reports
- ✨ **Add features** — Look for issues tagged `good first issue` or `enhancement`
- 📖 **Improve docs** — Fix typos, improve clarity, or add examples to the README
- 🧪 **Write tests** — Help us build a test suite for the backend
- 🎨 **Improve the UI** — Make the Chrome extension popup look even better

---

## ⚙️ Setting Up Your Environment

### 1. Fork and clone the repository

```bash
# Fork via GitHub, then:
git clone https://github.com/<your-username>/LeetcodeAI.git
cd LeetcodeAI
```

### 2. Create a feature branch

```bash
git checkout -b feat/your-feature-name
# or for a bugfix:
git checkout -b fix/short-description-of-bug
```

### 3. Set up the backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

### 4. Create your `.env` file

```bash
# backend/.env
GEMINI_API_KEY=your_key_here
DEVTO_API_KEY=your_key_here
```

### 5. Run the server locally

```bash
python main.py
# Runs at http://localhost:10000
```

### 6. Load the extension

1. Open `chrome://extensions/`
2. Enable **Developer mode**
3. Click **Load unpacked** → select the `extension/` folder

---

## 📬 Making a Pull Request

1. Ensure your branch is up to date with `main`:
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. Push your branch and open a PR on GitHub:
   ```bash
   git push origin feat/your-feature-name
   ```

3. In your PR description, please include:
   - **What** the PR does
   - **Why** it's needed (link to the relevant issue if any)
   - **How to test** your changes

4. A maintainer will review your PR and may request changes. Please respond promptly.

---

## 🎨 Coding Standards

### Python (Backend)
- Follow [PEP 8](https://peps.python.org/pep-0008/) style guidelines
- Use `snake_case` for variables and functions
- Add docstrings to all new functions
- Keep functions small and focused

### JavaScript (Extension)
- Use `camelCase` for variables and functions
- Prefer `async/await` over raw promise chains
- Avoid `console.log` in production code (use it only for debugging)

### General
- Keep PRs focused — one feature or fix per PR
- Write meaningful commit messages: `feat: add X`, `fix: resolve Y`, `docs: update Z`
- Never commit `.env` files or API keys

---

## 🐛 Reporting Bugs

Please open an issue with the following details:

- **Description** — What is the bug?
- **Steps to Reproduce** — How can we trigger the bug?
- **Expected Behavior** — What should happen?
- **Actual Behavior** — What actually happens?
- **Screenshots/Logs** — If applicable

---

Thank you for contributing to LeetLog AI! 🚀
