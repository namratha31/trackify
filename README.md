# Trackify — Simple Expense Tracker

Trackify is a minimal personal finance app to track income and expenses, categorize them, and visualize spending.

Quick start (Windows PowerShell):

1. Create a virtual environment and activate it (recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the app:

```powershell
python app.py
```

4. Open http://127.0.0.1:5000 in your browser.

Notes:
- The app uses SQLite database file `trackify.db` created automatically on first run.
- For production, set `TRACKIFY_SECRET` env var for the Flask secret and use a proper WSGI server.
