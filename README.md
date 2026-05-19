<div align="center">

<h1>🧠 LeetLog AI</h1>

<p><strong>Solve a LeetCode problem → Auto-publish a blog post to Dev.to, Hashnode, Medium, or your own site — in seconds.</strong></p>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![GSSoC](https://img.shields.io/badge/GSSoC-2026-orange)](https://gssoc.girlscript.tech/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)

</div>

---

## 📖 What is LeetLog AI?

**LeetLog AI** is a Chrome Extension + Python backend that watches your LeetCode session and, the moment you solve a problem, **automatically generates a professional, beginner-friendly blog post** using Google Gemini AI and **publishes it to your selected blogging platforms** on your behalf.

No copy-paste. No formatting. Just solve, and let the AI do the rest.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **AI Blog Generation** | Gemini generates a structured post: explanation, intuition, approach, code, complexity analysis |
| 📤 **Multi-platform publishing** | Posts can be published to Dev.to, Hashnode, Medium, or a custom blog webhook |
| 🧭 **Platform selection** | Choose publishing targets from the extension popup before generating a post |
| 📊 **Per-platform status** | The backend reports success or failure for each selected platform independently |
| ⚡ **One-click from Extension** | Click "Generate Blog" in the popup — that's it |
| 🔍 **Smart Code Extraction** | Scrapes your solution code and problem details directly from the LeetCode page |
| 🧑‍💻 **Author Attribution** | Automatically picks up your LeetCode username for the post footer |

---

## 🏗️ Architecture

```
┌─────────────────────────┐        ┌─────────────────────────────┐
│   Chrome Extension      │        │   FastAPI Backend (Python)  │
│                         │        │                             │
│  content.js             │──POST──▶  /generate-blog             │
│  (scrapes LeetCode page)│        │       │                     │
│                         │        │       ▼                     │
│  background.js          │        │   ai.py (Gemini API)        │
│  (sends to backend)     │        │       │                     │
│                         │        │       ▼                     │
│  popup.html / popup.js  │◀─JSON──│   devto.py (publishers)     │
│  (shows status)         │        │                             │
└─────────────────────────┘        └─────────────────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Google Chrome (for the extension)
- A [Google Gemini API Key](https://aistudio.google.com/app/apikey)
- At least one publishing API key:
  - [Dev.to API Key](https://dev.to/settings/extensions) (Account → Settings → API Keys)
  - Hashnode token + publication ID
  - Medium integration token + user ID
  - A custom webhook URL for personal blogs

---

### 1. Clone the Repository

```bash
git clone https://github.com/vanshaggarwal27/LeetcodeAI
cd LeetcodeAI
```

---

### 2. Set Up the Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

#### Create your `.env` file

```bash
# backend/.env
GEMINI_API_KEY=your_google_gemini_api_key_here
DEVTO_API_KEY=your_devto_api_key_here
HASHNODE_TOKEN=your_hashnode_token_here
HASHNODE_PUBLICATION_ID=your_hashnode_publication_id_here
MEDIUM_TOKEN=your_medium_integration_token_here
MEDIUM_USER_ID=your_medium_user_id_here
BLOG_WEBHOOK_URL=https://your-blog.example.com/api/publish
```

> ⚠️ **Never commit your `.env` file.** It is already listed in `.gitignore`.

#### Run the server

```bash
python main.py
```

The server will start at `http://localhost:10000`.

---

### 3. Load the Chrome Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (top-right toggle)
3. Click **"Load unpacked"**
4. Select the `extension/` folder from this repository

The **LeetLog AI** extension icon will appear in your toolbar.

---

### 4. Use It!

1. Go to any LeetCode problem page (e.g., `https://leetcode.com/problems/two-sum/`)
2. Write or paste your solution
3. Click the **LeetLog AI** extension icon
4. Click **"Generate Blog"**
5. Select one or more platforms in the popup
6. Wait a few seconds — the popup will show which platforms published successfully ✅

---

## 📁 Project Structure

```
LeetcodeAI/
│
├── backend/                  # Python FastAPI server
│   ├── main.py               # API routes (/generate-blog)
│   ├── ai.py                 # Gemini AI blog generation logic
│   ├── devto.py              # Publishing provider registry and clients
│   ├── requirements.txt      # Python dependencies
│   └── .env                  # ⚠️ Your secrets (NOT committed)
│
├── extension/                # Chrome Extension (MV3)
│   ├── manifest.json         # Extension config
│   ├── content.js            # Scrapes LeetCode page data
│   ├── background.js         # Service worker — calls backend
│   ├── popup.html            # Extension popup UI
│   └── popup.js              # Popup event logic
│
├── .gitignore
├── CONTRIBUTING.md
└── README.md
```

---

## 🔮 Future Scope (Ideas for Open Source Contributors)

Here is a checklist of features that would be incredibly useful for the community. We welcome contributions for these!

- [ ] **WhatsApp Reminder Service**: Send automated daily reminders to solve LeetCode problems using the **Twilio API**.
- [ ] **Automated Call Alerts**: Trigger automated phone calls using **ElevenLabs** and Twilio if a user hasn't solved their daily problem by a specific time.
- [x] **Multi-platform Publishing**: Add support for publishing to Medium, Hashnode, or an existing personal blog/website.
- [ ] **Customizable Prompts**: Allow users to configure the prompt used by Gemini so they can customize the tone and style of the generated blog post.
- [ ] **Support for Other Coding Platforms**: Extend support to platforms like HackerRank, Codeforces, or GeeksforGeeks.
- [ ] **Dashboard/Stats Page**: Create a simple dashboard to track the number of problems solved, posts published, and consistency streaks.
- [ ] **Social Sharing**: Automatically share the published Dev.to post to Twitter/X or LinkedIn.

---

## 🌐 Deploying the Backend

The backend can be deployed for free on [Render](https://render.com/).

1. Push your code to GitHub
2. Create a new **Web Service** on Render
3. Set **Build Command**: `pip install -r requirements.txt`
4. Set **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
5. Add your environment variables (`GEMINI_API_KEY` and the API keys for your selected publishing platforms) in the Render dashboard
6. Copy your public Render URL and update `API_URL` in `extension/background.js`

---

## 🤝 Contributing

We ❤️ contributions! LeetLog AI is part of **GSSoC 2026** and welcomes developers of all experience levels.

Please read our **[CONTRIBUTING.md](CONTRIBUTING.md)** for:
- How to set up your development environment
- Guidelines for submitting issues and pull requests
- Code style standards

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- [Google Gemini](https://deepmind.google/technologies/gemini/) — AI blog generation
- [Dev.to API](https://developers.forem.com/api), Hashnode, Medium, and custom webhooks — Publishing platforms
- [FastAPI](https://fastapi.tiangolo.com/) — Backend framework
- All GSSoC contributors 💪
