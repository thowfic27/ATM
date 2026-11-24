"""
Views for the ATM web app.

Each view mirrors a part of the original CLI (ATM.py):

    CLI main menu                  ->  Web page
    ---------------------------------------------------
    Login                          ->  atm:login
    New User (Create Account)      ->  atm:register
    1. Check Balance               ->  atm:dashboard
    2. Deposit                     ->  atm:deposit
    3. Withdraw                    ->  atm:withdraw
    4. Mini Statement              ->  atm:statement
    5. Logout                      ->  atm:logout

Logged-in ATM users are kept in request.session
(user_id, user_name, account_number).
"""

from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect, render

from . import db
from .forms import DepositForm, LoginForm, RegisterForm, WithdrawForm


# ============================================================
# DECORATOR
# ============================================================
def atm_login_required(view_func):
    """Send the visitor to the login page unless an ATM user is in the session."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("account_number"):
            messages.info(request, "Please log in to access your account.")
            return redirect("atm:login")
        return view_func(request, *args, **kwargs)

    return wrapper


def _current_balance(request, acc_no):
    """Best-effort balance read; DB errors become flash messages instead of crashes."""
    try:
        return db.get_balance(acc_no)
    except db.AtmError as exc:
        messages.error(request, str(exc))
        return None


# ============================================================
# PUBLIC PAGES
# ============================================================
def index(request):
    """Landing page - like the CLI's welcome screen."""
    if request.session.get("account_number"):
        return redirect("atm:dashboard")
    return render(request, "atm/index.html")


def register(request):
    """New user account creation - mirrors create_account() in ATM.py."""
    if request.session.get("account_number"):
        return redirect("atm:dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = db.create_account(
                    form.cleaned_data["name"],
                    form.cleaned_data["password"],
                )
            except db.AtmError as exc:
                form.add_error(None, str(exc))
            else:
                messages.success(
                    request,
                    "Account created successfully! Your account number is "
                    f"{user['account_number']}. Please log in.",
                )
                return redirect("atm:login")
    else:
        form = RegisterForm()

    return render(request, "atm/register.html", {"form": form})


def login_view(request):
    """Login - mirrors login() in ATM.py."""
    if request.session.get("account_number"):
        return redirect("atm:dashboard")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            try:
                user = db.login_user(
                    form.cleaned_data["name"],
                    form.cleaned_data["password"],
                )
            except db.AtmError as exc:
                form.add_error(None, str(exc))
            else:
                if user is None:
                    form.add_error(None, "Invalid username or password.")
                else:
                    # keep the ATM user in the session
                    request.session["user_id"] = user["id"]
                    request.session["user_name"] = user["name"]
                    request.session["account_number"] = user["account_number"]
                    messages.success(request, f"Welcome back, {user['name']}!")
                    return redirect("atm:dashboard")
    else:
        form = LoginForm()

    return render(request, "atm/login.html", {"form": form})


def logout_view(request):
    """Logout - clears the session (CLI menu option 5)."""
    request.session.flush()
    messages.info(request, "You have been logged out. Thank you for using PyBank ATM!")
    return redirect("atm:index")


# ============================================================
# LOGGED-IN PAGES
# ============================================================
@atm_login_required
def dashboard(request):
    """ATM menu home - shows the account card and current balance (option 1)."""
    balance = _current_balance(request, request.session["account_number"])
    return render(request, "atm/dashboard.html", {"balance": balance})


@atm_login_required
def deposit(request):
    """Deposit money - menu option 2."""
    acc_no = request.session["account_number"]
    balance = _current_balance(request, acc_no)

    if request.method == "POST":
        form = DepositForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data["amount"]
            try:
                new_balance = db.deposit(acc_no, amount)
            except db.AtmError as exc:
                messages.error(request, str(exc))
            else:
                messages.success(
                    request,
                    f"Deposited Rs. {amount:.2f}. New balance: Rs. {new_balance:.2f}.",
                )
                return redirect("atm:dashboard")
    else:
        form = DepositForm()

    return render(request, "atm/deposit.html", {"form": form, "balance": balance})


@atm_login_required
def withdraw(request):
    """Withdraw money - menu option 3."""
    acc_no = request.session["account_number"]
    balance = _current_balance(request, acc_no)

    if request.method == "POST":
        form = WithdrawForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data["amount"]
            try:
                new_balance = db.withdraw(acc_no, amount)
            except db.AtmError as exc:
                messages.error(request, str(exc))
            else:
                messages.success(
                    request,
                    f"Withdrew Rs. {amount:.2f}. New balance: Rs. {new_balance:.2f}.",
                )
                return redirect("atm:dashboard")
    else:
        form = WithdrawForm()

    return render(request, "atm/withdraw.html", {"form": form, "balance": balance})


@atm_login_required
def statement(request):
    """Mini statement - the last 5 transactions, menu option 4."""
    acc_no = request.session["account_number"]
    try:
        transactions = db.mini_statement(acc_no, limit=5)
    except db.AtmError as exc:
        messages.error(request, str(exc))
        transactions = []
    return render(request, "atm/statement.html", {"transactions": transactions})
