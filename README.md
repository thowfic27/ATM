# PyBank ATM — Web Frontend

A web frontend (Django + HTML/CSS/JS + Bootstrap 5) for the existing
**ATM Transaction Simulation** (`ATM.py`). It talks to the **same MySQL
database** (`atm_db`) through the **same `config.py`**, so accounts created
in the CLI work on the website and vice-versa.

## Project structure

```
dharshini task/
├── ATM.py                     # original CLI app (unchanged)
├── config.py                  # MySQL credentials (shared by CLI + web)
├── db_setup.sql               # MySQL database setup (unchanged)
├── manage.py                  # Django management script
├── requirements.txt           # Python dependencies for the web app
├── atm_project/               # Django project (settings / urls)
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py / asgi.py
└── atm/                       # The ATM web app
    ├── db.py                  # MySQL layer (mirrors the functions in ATM.py)
    ├── forms.py               # login / register / deposit / withdraw forms
    ├── views.py               # one view per CLI menu option
    ├── urls.py                # routes
    ├── templates/atm/         # HTML pages (Bootstrap 5)
    │   ├── base.html          # navbar, footer, flash messages, modal
    │   ├── index.html         # welcome page (hero + features)
    │   ├── login.html         # CLI: Login
    │   ├── register.html      # CLI: New User (Create Account)
    │   ├── dashboard.html     # CLI: Check Balance + account card
    │   ├── deposit.html       # CLI: menu option 2
    │   ├── withdraw.html      # CLI: menu option 3
    │   └── statement.html     # CLI: menu option 4 (last 5 txns)
    └── static/atm/
        ├── css/style.css      # custom styling on top of Bootstrap
        └── js/main.js          # quick amounts, show-password, confirm modal,
                                # balance animation, auto-dismiss alerts
```

## Page ↔ CLI mapping

| CLI (ATM.py)                    | Web page       | URL           |
|----------------------------------|----------------|---------------|
| Welcome banner                   | Home           | `/`           |
| 1. Login                         | Login          | `/login/`     |
| 2. New User (Create Account)     | Create Account | `/register/`  |
| ATM menu → Check Balance         | Dashboard      | `/dashboard/` |
| ATM menu → 2. Deposit            | Deposit        | `/deposit/`   |
| ATM menu → 3. Withdraw           | Withdraw       | `/withdraw/`  |
| ATM menu → 4. Mini Statement     | Mini Statement | `/statement/` |
| ATM menu → 5. Logout             | Logout         | `/logout/`    |

## Setup

1. **Install the Python packages**

   ```
   pip install -r requirements.txt
   ```

2. **Set up MySQL** (if not already done for the CLI)

   ```
   mysql -u root -p < db_setup.sql
   ```

3. **Edit `config.py`** with your MySQL username / password (same file the CLI uses).

4. **Run the Django checks and start the server**

   ```
   python manage.py migrate     # creates Django's internal sqlite DB (sessions etc.)
   python manage.py runserver
   ```

5. Open **http://127.0.0.1:8000/** in your browser.

> Note: Django's own sqlite database (`db.sqlite3`) is only used for internal
> things like sessions. All ATM data (users, transactions) stays in MySQL via
> `config.py` — exactly like the CLI.

## Technologies used

- **Python / Django** — backend (views, forms, sessions)
- **MySQL** — existing `atm_db` database (users + transactions tables)
- **HTML5** — templates (Django template language)
- **CSS** — custom stylesheet (`atm/static/atm/css/style.css`)
- **JavaScript** — vanilla JS (`atm/static/atm/js/main.js`)
- **Bootstrap 5** — UI framework (CSS + JS, via CDN)
- No other languages or frontend libraries.
