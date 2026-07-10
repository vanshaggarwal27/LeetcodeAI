# 🗺️ ROADMAP — LeetLog AI

This document tracks the planned direction, active work, and completed features of LeetLog AI.
Cross-references: [README.md](README.md) | [CONTRIBUTING.md](CONTRIBUTING.md)

---

## ✅ Completed

These features are live in the current codebase:

- **Multi-platform Publishing** — Publish generated blogs to Dev.to, Hashnode, Medium, and custom personal blog webhooks
- **Multi-AI Provider Support** — Gemini, OpenAI, Perplexity, and xAI/Grok for blog generation
- **Per-platform Status Reporting** — The backend reports success or failure for each platform independently
- **Chrome Extension (MV3)** — One-click blog generation directly from any LeetCode problem page
- **Smart Code Extraction** — Automatically scrapes problem statement, solution code, and author details
- **Custom Prompt Support** — Users can customize the tone and style of generated blog posts
- **MongoDB Dashboard** — Stores publish history and stats per user
- **Social Sharing** — Share published posts to Twitter/X and LinkedIn
- **User Authentication** — Account creation, login, and per-user integration settings via frontend dashboard
- **Frontend Dashboard** — React + Vite web dashboard for managing settings and viewing stats
- **Celery + Redis Reminder Queue** — Background job queue for scheduled reminders
- **Publish as Draft** — Option to publish to platforms as draft instead of live post

---

## 🔄 In Progress

Features currently being worked on by contributors:

- **Dashboard UI Improvements** — Making the dashboard more detailed and visually appealing
- **Extended Test Coverage** — Adding tests for routes, AI providers, social sharing, and reminders
- **UI/UX Polish** — Improving the Chrome extension popup interaction and status display

---

## 📋 Planned

Features planned for future contributors. All of these are open for contribution:

- **WhatsApp Reminder Service** — Send automated daily reminders to solve LeetCode problems using the Twilio API
- **Automated Call Alerts** — Trigger automated phone calls using ElevenLabs and Twilio if a user hasn't solved their daily problem by a specific time
- **Support for Other Coding Platforms** — Extend support to HackerRank, Codeforces, GeeksforGeeks, CodeChef, and AtCoder
- **Customizable Blog Tones** — Allow users to select from preset writing tones (casual, technical, beginner-friendly) instead of writing custom prompts from scratch
- **Copy to Clipboard** — Allow users to copy the generated blog content directly from the extension popup
- **Local History for Generated Posts** — Retain a reference to recently generated posts inside the extension popup
- **Async Dev.to Publishing** — Refactor publishing to use non-blocking async HTTP requests
- **Social Sharing Expansion** — Automatically share published posts to more platforms

---

## 💡 Ideas Under Consideration

Community-suggested features being evaluated:

- **Support for Safari Extension** — Port the Chrome extension to Safari via Xcode
- **AI Explanation Mode** — Add short educational explanations beside each blog section
- **Shareable Demo Sessions** — Allow users to share their generated blog previews
- **Custom Webhook Builder** — UI for configuring personal blog webhook endpoints
- **Streak Tracking** — Track how many consecutive days a user has solved and published

---

## 🤝 How to Contribute

Want to work on any of the Planned or Ideas features?

1. Check the [open issues](https://github.com/vanshaggarwal27/LeetcodeAI/issues)
2. Comment on the issue to get assigned
3. Follow the workflow in [CONTRIBUTING.md](CONTRIBUTING.md)

All contributions welcome — beginner to advanced! 💪