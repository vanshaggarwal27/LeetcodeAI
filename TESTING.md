# Testing Guide

This document explains how contributors can test LeetcodeAI locally before submitting a pull request.

## Prerequisites

Before running tests, make sure you have:

* Python 3.12.3 installed
* Git installed
* A virtual environment created and activated
* Required dependencies installed
* Test API keys configured in `backend/.env` when testing AI generation or publishing flows

The required Python version is defined in the `.python-version` file.

## Setup

Clone the repository:

```bash
git clone https://github.com/vanshaggarwal27/LeetcodeAI.git
cd LeetcodeAI
```

Create and activate a virtual environment:

```bash
python -m venv venv
```

On Windows:

```bash
venv\Scripts\activate
```

On macOS/Linux:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables

Before testing backend, AI generation, or publishing features, create a `.env` file inside the `backend/` directory.

Example:

```env
GEMINI_API_KEY=your_test_gemini_api_key
DEVTO_API_KEY=your_test_devto_api_key
HASHNODE_TOKEN=your_test_hashnode_token
MEDIUM_TOKEN=your_test_medium_token
CUSTOM_WEBHOOK_URL=your_test_webhook_url
```

Use test keys or sandbox accounts whenever possible.

## Running Automated Tests

If the project Makefile is available, run:

```bash
make test
```

You can also run tests directly with pytest:

```bash
pytest
```

Run a specific test file:

```bash
pytest path/to/test_file.py
```

## Running Lint Checks

If the Makefile includes a lint command, run:

```bash
make lint
```

If running Ruff directly:

```bash
ruff check .
```

To automatically fix supported lint issues:

```bash
ruff check . --fix
```

## Manual Testing Checklist

### Backend Testing

Start the backend server:

```bash
cd backend
python main.py
```

Verify that the server starts successfully at:

```text
http://localhost:10000
```

Check that no import errors, missing environment variables, or startup crashes occur.

### AI Generation Testing

Send a test request to the `/generate-blog` endpoint using sample LeetCode problem data.

Example using curl:

```bash
curl -X POST http://localhost:10000/generate-blog \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Two Sum",
    "difficulty": "Easy",
    "language": "Python",
    "code": "def twoSum(nums, target): return []",
    "description": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target."
  }'
```

Verify that:

* The request completes successfully
* A blog-style response is generated
* No server error occurs
* Invalid or missing input is handled properly

### Publishing Platform Testing

Use test API keys before testing publishing features.

#### Dev.to

Verify that the Dev.to publishing flow works with a test API key.

Check:

* API key is read correctly
* Generated content is sent successfully
* Errors are shown clearly for invalid credentials

#### Hashnode

Verify Hashnode publishing using a test token.

Check:

* Token is configured correctly
* Blog content is prepared properly
* API errors are handled gracefully

#### Medium

Verify Medium publishing using a test token.

Check:

* Token is loaded from environment variables
* Content is sent to the correct endpoint
* Invalid token errors are handled properly

#### Custom Webhook

Verify custom webhook publishing using a test webhook URL.

Check:

* Webhook URL is read from `backend/.env`
* Payload is sent correctly
* Failed webhook requests are handled properly

### Chrome Extension Testing

To test the Chrome extension:

1. Open Chrome.
2. Go to:

```text
chrome://extensions/
```

3. Enable Developer Mode.
4. Click **Load unpacked**.
5. Select the `extension/` folder.
6. Open LeetCode.
7. Solve or open a problem.
8. Verify that the extension popup loads correctly.
9. Check that per-platform publishing status is displayed properly.

Also check the browser console for errors.

### Safari Extension Testing

To test the Safari port:

1. Open the `LeetLog AI/` Xcode project.
2. Build and run the project.
3. Enable the extension in Safari settings.
4. Open LeetCode in Safari.
5. Verify that the extension loads and behaves as expected.
6. Confirm that platform status and generated content are shown correctly.

## Pre-PR Checklist

Before submitting a pull request, confirm:

* [ ] I am using Python 3.12.3
* [ ] I created and activated a virtual environment
* [ ] I installed all required dependencies
* [ ] I configured `backend/.env` with test API keys where required
* [ ] I ran automated tests using `make test` or `pytest`
* [ ] I ran lint checks using `make lint` or `ruff check .`
* [ ] I manually tested backend startup
* [ ] I manually tested AI blog generation
* [ ] I checked publishing flows with test credentials where applicable
* [ ] I tested the Chrome extension if extension files were affected
* [ ] I tested the Safari extension if Safari files were affected
* [ ] I reviewed my changes before opening a PR

## Notes

Do not commit real API keys, tokens, or secrets.

Use test credentials whenever possible.

If a test cannot be performed locally, mention the reason clearly in the pull request description.
