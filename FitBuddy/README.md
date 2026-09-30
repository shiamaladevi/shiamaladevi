# FitBuddy – AI Fitness Plan Generator using Gemini

Complete FastAPI + Gemini + SQLite project based on the supplied FitBuddy specification.

## Stack
Python, FastAPI, Jinja2, HTML/CSS, Google Gemini API, SQLAlchemy, SQLite, Uvicorn.

## Mac / VS Code setup
Use `python3` if `python` is not recognized:

```bash
cd FitBuddy
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Put your Gemini API key in `.env` as `GOOGLE_API_KEY=...`. The app can also run without a key using a basic starter plan; Gemini-generated personalization and feedback revisions need a valid key. The app uses Google's maintained `google-genai` SDK, tries `gemini-3.8-flash` by default, and falls back to `gemini-3.5-flash` on server errors. Set `GEMINI_MODEL` and `GEMINI_FALLBACK_MODEL` in `.env` to models available to your API key.

Run:
```bash
uvicorn app.main:app --reload
```

Open:
- http://127.0.0.1:8000
- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/view-all-users

## Demo data
Name: Rasu Demo
User ID: FB001
Age: 26
Weight: 70
Goal: weight loss
Intensity: medium

Feedback example:
`Add more cardio and one extra rest day.`

Never upload `.env` or your API key to GitHub.
