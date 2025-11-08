# Trackify — Simple Expense Tracker

Trackify is a minimal personal finance app to track income and expenses, categorize them, and visualize spending habits.
It is designed to be simple, visually clean, and easy to run locally for learning personal budgeting.

## Features
- Add income and expense transactions with date, category and optional note
- Create a new category inline when adding a transaction
- View a dashboard with totals, recent transactions, expenses by category (pie), and monthly net (line)
- List and delete transactions
- Small, single-file Flask backend with SQLite for quick local use

## Tech stack
- Python 3.10+ (virtualenv recommended)
- Flask (backend web framework)
- Flask-SQLAlchemy (ORM)
- SQLite (local development DB)
- Bootstrap 5 and Chart.js (UI and charts)

## Quick start (Windows PowerShell)
1. Open PowerShell and change into the project directory:

```powershell
cd 'C:\Users\Admin\Desktop\py nam\trackify'
```

2. Create and activate a virtual environment (recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Run the app locally:

```powershell
python app.py
```

5. Open your browser to: http://127.0.0.1:5000

## Configuration / Environment variables
- `TRACKIFY_SECRET` (optional) — set a strong secret key for Flask sessions in production. If not set, a default development secret is used.

Example (PowerShell):

```powershell
$Env:TRACKIFY_SECRET = 'replace-with-strong-secret'
python app.py
```

## Database
- The app uses a local SQLite file `trackify.db` created automatically on first run. Do not commit this file to version control (see `.gitignore`).

If you want to reset the database during development, stop the server and delete `trackify.db`, then restart the app.

## Running in production
This project is a small demo and not production hardened. For a basic production deployment consider:
- Use a WSGI server such as Gunicorn or uWSGI behind a reverse proxy (NGINX)
- Use a production-ready database instead of SQLite (Postgres, MySQL)
- Set `TRACKIFY_SECRET` to a secure value and run with `FLASK_ENV=production` (or better, set Flask's config explicitly)

Example with Gunicorn (on Linux):

```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Development notes
- The main app file is `app.py` and templates live in `templates/` while static CSS is in `static/css/style.css`.
- Charts are rendered client-side using Chart.js and populated by an API endpoint (`/api/category_breakdown`).
- If you change models, delete `trackify.db` and re-run the app to recreate and reseed categories.

## Contributing
- Pull requests are welcome. For small fixes or features, open a PR against `main` with a short description.
- Please add tests for new functionality where appropriate and keep changes focused.

## .gitignore (recommended)
Don't commit environment files, venvs or the local DB. Example entries:

```
.venv/
trackify.db
_pycache_/
.vscode/
```

