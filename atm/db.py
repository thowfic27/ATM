"""
MySQL data layer for the ATM web app.

These functions mirror the ones in ATM.py (the CLI version), so the web
frontend and the CLI share the exact same database and rules:

    - users table        -> login + account info
    - transactions table -> mini statement

Connection settings come from the project's existing config.py,
the same file ATM.py uses.

Every function raises AtmError with a friendly, user-displayable
message when something goes wrong.
"""

import random
import string

import mysql.connector
from mysql.connector import Error

from config import DB_CONFIG


class AtmError(Exception):
    """Friendly error raised for ATM / database problems."""


# ============================================================
# CONNECTION
# ============================================================
def get_connection():
    """Return a new MySQL connection (same as ATM.py)."""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as exc:
        raise AtmError(
            "Could not connect to MySQL. Please make sure the server is "
            "running and that config.py contains the correct username / "
            "password / database name."
        ) from exc


def _close(cur, conn):
    """Safely close a cursor and its connection."""
    if cur:
        try:
            cur.close()
        except Error:
            pass
    if conn:
        try:
            conn.close()
        except Error:
            pass


# ============================================================
# UTILITIES (same rules as the CLI)
# ============================================================
def generate_account_number():
    """12-digit unique account number (same as ATM.py)."""
    return "".join(random.choices(string.digits, k=12))


def validate_password(pw):
    """
    Simple rule set (identical to ATM.py):
    - at least 6 characters
    - at least 1 digit
    """
    if len(pw) < 6:
        return False, "Password must be at least 6 characters."
    if not any(ch.isdigit() for ch in pw):
        return False, "Password must contain at least one digit."
    return True, ""


def _log_transaction(cur, acc_no, txn_type, amount, balance_after):
    """Insert a row into the transactions table (same as ATM.py)."""
    cur.execute(
        "INSERT INTO transactions "
        "(account_number, txn_type, amount, balance_after) "
        "VALUES (%s, %s, %s, %s)",
        (acc_no, txn_type, amount, balance_after),
    )


# ============================================================
# ACCOUNT CREATION (NEW USER)
# ============================================================
def create_account(name, password):
    """
    Create a new user row. Mirrors create_account() in ATM.py.
    Returns {"name": ..., "account_number": ...} on success.
    """
    ok, msg = validate_password(password)
    if not ok:
        raise AtmError(msg)

    conn = get_connection()
    cur = None
    try:
        cur = conn.cursor()

        # unique username check
        cur.execute("SELECT id FROM users WHERE name = %s", (name,))
        if cur.fetchone():
            raise AtmError("That username already exists. Please choose another one.")

        # generate a unique account number
        while True:
            acc_no = generate_account_number()
            cur.execute("SELECT id FROM users WHERE account_number = %s", (acc_no,))
            if not cur.fetchone():
                break

        # NOTE: for teaching purposes we store the plain password,
        # exactly like ATM.py does. Real systems would hash it.
        cur.execute(
            "INSERT INTO users (name, password_hash, account_number, balance) "
            "VALUES (%s, %s, %s, %s)",
            (name, password, acc_no, 0.00),
        )
        conn.commit()
        return {"name": name, "account_number": acc_no}

    except AtmError:
        conn.rollback()
        raise
    except Error as exc:
        conn.rollback()
        raise AtmError(f"Database error while creating the account: {exc}") from exc
    finally:
        _close(cur, conn)


# ============================================================
# LOGIN
# ============================================================
def login_user(name, password):
    """
    Return the user row (dict) when credentials match, otherwise None.
    Mirrors login() in ATM.py.
    """
    conn = get_connection()
    cur = None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id, name, account_number, balance "
            "FROM users WHERE name = %s AND password_hash = %s",
            (name, password),
        )
        return cur.fetchone()
    except Error as exc:
        raise AtmError(f"Database error during login: {exc}") from exc
    finally:
        _close(cur, conn)


# ============================================================
# TRANSACTIONS
# ============================================================
def get_balance(acc_no):
    """Current balance for an account (menu option 1)."""
    conn = get_connection()
    cur = None
    try:
        cur = conn.cursor()
        cur.execute("SELECT balance FROM users WHERE account_number = %s", (acc_no,))
        row = cur.fetchone()
        if row is None:
            raise AtmError("Account not found.")
        return float(row[0])
    except Error as exc:
        raise AtmError(f"Could not read the balance: {exc}") from exc
    finally:
        _close(cur, conn)


def deposit(acc_no, amount):
    """
    Add money to an account (menu option 2).
    Returns the new balance on success.
    """
    if amount <= 0:
        raise AtmError("Amount must be positive.")

    conn = get_connection()
    cur = None
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET balance = balance + %s WHERE account_number = %s",
            (amount, acc_no),
        )
        if cur.rowcount == 0:
            raise AtmError("Account not found.")
        cur.execute("SELECT balance FROM users WHERE account_number = %s", (acc_no,))
        new_balance = float(cur.fetchone()[0])
        _log_transaction(cur, acc_no, "DEPOSIT", amount, new_balance)
        conn.commit()
        return new_balance
    except AtmError:
        conn.rollback()
        raise
    except Error as exc:
        conn.rollback()
        raise AtmError(f"Deposit failed: {exc}") from exc
    finally:
        _close(cur, conn)


def withdraw(acc_no, amount):
    """
    Take money out of an account (menu option 3).
    Uses SELECT ... FOR UPDATE for an atomic check, exactly like ATM.py.
    Returns the new balance on success.
    """
    if amount <= 0:
        raise AtmError("Amount must be positive.")

    conn = get_connection()
    cur = None
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT balance FROM users WHERE account_number = %s FOR UPDATE",
            (acc_no,),
        )
        row = cur.fetchone()
        if row is None:
            raise AtmError("Account not found.")

        current_balance = float(row[0])
        if amount > current_balance:
            raise AtmError(
                f"Insufficient balance. Available: Rs. {current_balance:.2f}"
            )

        cur.execute(
            "UPDATE users SET balance = balance - %s WHERE account_number = %s",
            (amount, acc_no),
        )
        new_balance = current_balance - amount
        _log_transaction(cur, acc_no, "WITHDRAW", amount, new_balance)
        conn.commit()
        return new_balance
    except AtmError:
        conn.rollback()
        raise
    except Error as exc:
        conn.rollback()
        raise AtmError(f"Withdrawal failed: {exc}") from exc
    finally:
        _close(cur, conn)


def mini_statement(acc_no, limit=5):
    """
    Last few transactions for an account (menu option 4).
    Returns a list of dicts, newest first.
    """
    conn = get_connection()
    cur = None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT txn_type, amount, balance_after, txn_time "
            "FROM transactions WHERE account_number = %s "
            "ORDER BY txn_id DESC LIMIT %s",
            (acc_no, limit),
        )
        return list(cur.fetchall())
    except Error as exc:
        raise AtmError(f"Could not load the mini statement: {exc}") from exc
    finally:
        _close(cur, conn)
