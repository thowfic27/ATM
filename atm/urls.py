"""
URL routes for the ATM app.

Each page matches a CLI option from ATM.py:

    /               -> welcome screen (main menu)
    /register/      -> "2. New User (Create Account)"
    /login/         -> "1. Login"
    /dashboard/     -> "1. Check Balance" (also the ATM menu home)
    /deposit/       -> "2. Deposit"
    /withdraw/      -> "3. Withdraw"
    /statement/     -> "4. Mini Statement"
    /logout/        -> "5. Logout"
"""

from django.urls import path

from . import views

app_name = "atm"

urlpatterns = [
    path("", views.index, name="index"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("deposit/", views.deposit, name="deposit"),
    path("withdraw/", views.withdraw, name="withdraw"),
    path("statement/", views.statement, name="statement"),
]
