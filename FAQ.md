# ❓ FAQ — LeetLog AI

Answers to the most common questions from contributors and users.
Cross-references: [README.md](README.md) | [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📖 General

**What is LeetLog AI?**
LeetLog AI is a Chrome Extension + Python FastAPI backend that automatically generates and publishes a professional blog post whenever you solve a LeetCode problem. It uses AI providers (Gemini, OpenAI, Perplexity, or xAI/Grok) to write the post and can publish to Dev.to, Hashnode, Medium, or a custom webhook.

**What is the tech stack?**
- Backend: Python 3.12.3, FastAPI, Motor (async MongoDB), Celery, Redis
- Frontend: React + Vite, runs at http://localhost:5173
- Extension: Chrome MV3 (content.js, background.js, popup.js)
- AI Providers: Gemini, OpenAI, Perplexity, xAI/Grok
- Publishing: Dev.to, Hashnode, Medium, custom webhook
- Social sharing: Twitter/X, LinkedIn
- Deployment: Render (backend), MongoDB Atlas (database)

---

## ⚙️ Setup

**What Python version is required?**
Python 3.12.3 — see `.python-version` in the project root. The README badge says 3.10+ but 3.12.3 is the tested version.

**How do I set up the virtual environment?**

Windows:
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

macOS / Linux:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> **Windows OneDrive note:** If your Desktop is inside OneDrive, use the full path:
> `cd C:\Users\YourName\OneDrive\Desktop\LeetcodeAI\backend`

**How do I create the .env file?**
Copy `backend/.env.example` to `backend/.env` and fill in your values. Never commit `.env` — it is already in `.gitignore`.

| Key | Required | Use case | Where to get it |
|---|---|---|---|
| AI_PROVIDER | Yes | Set to `gemini`, `openai`, `perplexity`, or `xai` | — |
| GEMINI_API_KEY | If using Gemini | AI blog generation | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| OPENAI_API_KEY | If using OpenAI | AI blog generation | [OpenAI platform](https://platform.openai.com/api-keys) |
| PERPLEXITY_API_KEY | If using Perplexity | AI blog generation | [Perplexity settings](https://www.perplexity.ai/settings/api) |
| XAI_API_KEY | If using xAI/Grok | AI blog generation | [xAI console](https://console.x.ai/) |
| DEVTO_API_KEY | For Dev.to publishing | Publish blog posts | [Dev.to Settings → Extensions](https://dev.to/settings/extensions) |
| MONGODB_URI | Yes | Store publish records | [MongoDB Atlas](https://cloud.mongodb.com) → Connect → Drivers |
| TWILIO_ACCOUNT_SID | For WhatsApp reminders | Send reminders | [Twilio Console](https://console.twilio.com) |
| TWILIO_AUTH_TOKEN | For WhatsApp reminders | Send reminders | [Twilio Console](https://console.twilio.com) |
| TWILIO_PHONE_NUMBER | For WhatsApp reminders | Sender number | Twilio purchased number |
| TEST_PHONE_NUMBER | For local Twilio testing | Test SMS/calls locally | Your personal phone number |
| ELEVENLABS_API_KEY | For voice call alerts | AI voice audio | [ElevenLabs settings](https://elevenlabs.io/app/settings/api-keys) |
| TWITTER_API_KEY | For Twitter/X sharing | Post tweets | [Twitter developer portal](https://developer.twitter.com) |
| TWITTER_API_SECRET | For Twitter/X sharing | Post tweets | Twitter developer portal |
| TWITTER_ACCESS_TOKEN | For Twitter/X sharing | Post tweets | Twitter developer portal |
| TWITTER_ACCESS_SECRET | For Twitter/X sharing | Post tweets | Twitter developer portal |
| LINKEDIN_ACCESS_TOKEN | For LinkedIn sharing | Post updates | LinkedIn developer portal |
| LINKEDIN_PERSON_URN | For LinkedIn sharing | Identify account | LinkedIn developer portal |
| APP_SECRET_KEY | Recommended for production | JWT token signing — defaults to `dev-only-change-me` if not set | Any random secret string |
| REDIS_URL | For Celery reminders | Redis broker URL — defaults to `redis://localhost:6379/0` | Your Redis instance URL |
| BACKEND_URL | For ElevenLabs voice calls | Public backend URL for audio file serving | Your Render deployment URL |

**How do I run the backend?**
```bash
cd backend
python main.py
```
Server starts at http://localhost:10000

**How do I run the Celery reminder worker?**
First start Redis, then run:
```bash
cd backend
celery -A celery_app.celery_app worker --loglevel=info -Q reminders
```
Set `REDIS_URL`, `CELERY_BROKER_URL`, or `CELERY_RESULT_BACKEND` if Redis is not running at `redis://localhost:6379/0`.

**How do I run the frontend dashboard?**
```bash
cd frontend
npm install
npm run dev
```
Dashboard opens at http://localhost:5173

> If your backend is not at http://localhost:10000, set the environment variable before running:
> `VITE_API_URL=https://your-backend-url npm run dev`

---

## 🔌 Chrome Extension

**How do I load the extension in Chrome?**
1. Open Chrome and go to `chrome://extensions/`
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked**
4. Select the `extension/` folder from the repo

**The extension asks for my email — why?**
Your email is stored locally in `chrome.storage.local` and sent as the `X-User-Email` header with every request. This identifies your data on the backend so your publish history and stats are kept separate from other users. It is never shared externally.

**How do I point the extension to my local backend?**
Open `extension/background.js` and update `API_BASE_URL`:
```js
const API_BASE_URL = "http://localhost:10000";
```

**How do I point the extension to my deployed Render backend?**
Update `API_BASE_URL` in `extension/background.js`:
```js
const API_BASE_URL = "https://your-app.onrender.com";
```

---

## 📤 Publishing Issues

**Why is a platform showing as failed?**
Each platform reports success or failure independently in the popup. Common causes:
- Missing or expired API key for that platform in your `.env`
- Platform API rate limit reached
- Network timeout during publishing

**Why is Dev.to not publishing?**
Verify `DEVTO_API_KEY` in your `.env`. Get it from Dev.to → Settings → Extensions → DEV Community API Keys.

**Why is the blog generating but not publishing anywhere?**
Make sure at least one platform is selected in the extension popup before clicking Generate Blog.

---

## 🚀 Deployment

**How do I deploy the backend to Render?**
1. Push your code to GitHub
2. Create a new Web Service on [Render](https://render.com)
3. Set Build Command: `pip install -r requirements.txt`
4. Set Start Command: `uvicorn main:app --host 0.0.0.0 --port 10000`
5. Add all environment variables from your `.env` file in the Render dashboard
6. Copy your public Render URL and update `API_BASE_URL` in `extension/background.js`
7. Also set `BACKEND_URL` to your Render URL so ElevenLabs audio files are served correctly

---

## 🤝 Contributing

**How do I claim an issue?**
Comment on the issue before starting work. Wait for the maintainer to assign it to you. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow.

**How do I name my branch?**
- Bug fix: `fix/short-description`
- New feature: `feat/short-description`
- Documentation: `docs/short-description`
- Refactor: `refactor/short-description`

**What commit message format should I use?**
Use [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | When to use |
|---|---|
| `feat:` | A new feature |
| `fix:` | A bug fix |
| `docs:` | Documentation only changes |
| `refactor:` | Code cleanup without feature/fix |
| `chore:` | Dependency updates, config changes |
| `test:` | Adding or updating tests |

**How do I run the tests locally?**
```bash
cd backend
pytest -v
```

**How do I run the linter?**
```bash
cd backend
ruff check .
```

**How do I auto-fix lint errors?**
```bash
cd backend
ruff check --fix .
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the complete contribution workflow.