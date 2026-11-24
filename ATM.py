"""
ATM Transaction Simulation
- New user account creation  -> stored in MySQL (users table)
- Login with name + password -> validated against users table
- ATM features: balance, deposit, withdraw, mini-statement, logout
"""

import random
import string
import getpass

import mysql.connector
from mysql.connector import Error

from config import DB_CONFIG

# ============================================================
# DATABASE HELPERS
# ============================================================
def get_connection():
    """Return a new MySQL connection."""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"[DB ERROR] Could not connect to MySQL: {e}")
        print("Check config.py (username/password/database name).")
        return None


# ============================================================
# UTILITIES
# ============================================================
def generate_account_number():
    """12-digit unique account number."""
    return "".join(random.choices(string.digits, k=12))


def input_password(prompt="Password: "):
    """Hide password while typing (falls back to visible on some IDEs)."""
    try:
        return getpass.getpass(prompt)
    except Exception:
        return input(prompt)


def validate_password(pw):
    """
    Simple rule set (easy to explain):
    - at least 6 chars
    - at least 1 digit
    """
    if len(pw) < 6:
        return False, "Password must be at least 6 characters."
    if not any(ch.isdigit() for ch in pw):
        return False, "Password must contain at least one digit."
    return True, ""


# ============================================================
# ACCOUNT CREATION (NEW USER)
# ============================================================
def create_account():
    print("\n--- NEW ACCOUNT CREATION ---")
    name = input("Choose a username (name): ").strip()
    if not name:
        print("❌ Username cannot be empty.")
        return

    password = input_password("Choose a password: ")
    ok, msg = validate_password(password)
    if not ok:
        print(f"❌ {msg}")
        return

    confirm = input_password("Confirm password: ")
    if password != confirm:
        print("❌ Passwords do not match.")
        return

    conn = get_connection()
    if not conn:
        return

    try:
        cur = conn.cursor()

        # unique username check
        cur.execute("SELECT id FROM users WHERE name = %s", (name,))
        if cur.fetchone():
            print("❌ That username already exists. Try another.")
            return

        # generate unique account number
        while True:
            acc_no = generate_account_number()
            cur.execute("SELECT id FROM users WHERE account_number = %s", (acc_no,))
            if not cur.fetchone():
                break

        # NOTE: for teaching purposes we store plain password.
        # For real systems use bcrypt / hashlib with salt.
        cur.execute(
            "INSERT INTO users (name, password_hash, account_number, balance) "
            "VALUES (%s, %s, %s, %s)",
            (name, password, acc_no, 0.00),
        )
        conn.commit()

        print("\n✅ Account created successfully!")
        print(f"   Username       : {name}")
        print(f"   Account Number : {acc_no}")
        print("   (Please note this account number — you'll see it on every login.)\n")

    except Error as e:
        conn.rollback()
        print(f"[DB ERROR] {e}")
    finally:
        cur.close()
        conn.close()


# ============================================================
# LOGIN
# ============================================================
def login():
    print("\n--- LOGIN ---")
    name = input("Username: ").strip()
    password = input_password("Password: ")

    conn = get_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM users WHERE name = %s AND password_hash = %s",
            (name, password),
        )
        user = cur.fetchone()

        if user:
            print(f"\n✅ Login Successful. Welcome, {user['name']}!")
            return user
        else:
            print("\n❌ Login Failed. Invalid username or password.")
            return None

    except Error as e:
        print(f"[DB ERROR] {e}")
        return None
    finally:
        cur.close()
        conn.close()


# ============================================================
# TRANSACTION HELPERS
# ============================================================
def log_transaction(cur, acc_no, txn_type, amount, balance_after):
    cur.execute(
        "INSERT INTO transactions "
        "(account_number, txn_type, amount, balance_after) "
        "VALUES (%s, %s, %s, %s)",
        (acc_no, txn_type, amount, balance_after),
    )


def get_balance(acc_no):
    conn = get_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT balance FROM users WHERE account_number = %s", (acc_no,))
        row = cur.fetchone()
        return float(row[0]) if row else None
    finally:
        cur.close()
        conn.close()


def deposit(acc_no, amount):
    conn = get_connection()
    if not conn:
        return False, "DB connection failed."
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET balance = balance + %s WHERE account_number = %s",
            (amount, acc_no),
        )
        cur.execute("SELECT balance FROM users WHERE account_number = %s", (acc_no,))
        new_balance = float(cur.fetchone()[0])
        log_transaction(cur, acc_no, "DEPOSIT", amount, new_balance)
        conn.commit()
        return True, new_balance
    except Error as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()


def withdraw(acc_no, amount):
    conn = get_connection()
    if not conn:
        return False, "DB connection failed.", None
    try:
        cur = conn.cursor()
        # atomic check + update using a lock
        cur.execute(
            "SELECT balance FROM users WHERE account_number = %s FOR UPDATE",
            (acc_no,),
        )
        row = cur.fetchone()
        if not row:
            return False, "Account not found.", None

        current_balance = float(row[0])
        if amount > current_balance:
            conn.rollback()
            return False, f"Insufficient balance. Available: Rs. {current_balance:.2f}", None

        cur.execute(
            "UPDATE users SET balance = balance - %s WHERE account_number = %s",
            (amount, acc_no),
        )
        new_balance = current_balance - amount
        log_transaction(cur, acc_no, "WITHDRAW", amount, new_balance)
        conn.commit()
        return True, "Withdrawal successful.", new_balance
    except Error as e:
        conn.rollback()
        return False, str(e), None
    finally:
        cur.close()
        conn.close()


def mini_statement(acc_no, limit=5):
    conn = get_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT txn_type, amount, balance_after, txn_time "
            "FROM transactions WHERE account_number = %s "
            "ORDER BY txn_id DESC LIMIT %s",
            (acc_no, limit),
        )
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


# ============================================================
# ATM MENU (after successful login)
# ============================================================
def atm_menu(user):
    acc_no = user["account_number"]

    while True:
        print("\n" + "=" * 45)
        print(f"  ATM MENU  |  {user['name']}  |  A/C: {acc_no}")
        print("=" * 45)
        print("  1. Check Balance")
        print("  2. Deposit")
        print("  3. Withdraw")
        print("  4. Mini Statement")
        print("  5. Logout")
        print("=" * 45)

        choice = input("Choose an option (1-5): ").strip()

        if choice == "1":
            bal = get_balance(acc_no)
            print(f"\n💰 Current Balance: Rs. {bal:.2f}")

        elif choice == "2":
            try:
                amt = float(input("Enter amount to deposit: Rs. "))
                if amt <= 0:
                    print("❌ Amount must be positive.")
                    continue
                ok, result = deposit(acc_no, amt)
                if ok:
                    print(f"✅ Deposited Rs. {amt:.2f}. New balance: Rs. {result:.2f}")
                else:
                    print(f"❌ Deposit failed: {result}")
            except ValueError:
                print("❌ Invalid amount.")

        elif choice == "3":
            try:
                amt = float(input("Enter amount to withdraw: Rs. "))
                if amt <= 0:
                    print("❌ Amount must be positive.")
                    continue
                ok, msg, new_bal = withdraw(acc_no, amt)
                if ok:
                    print(f"✅ Withdrew Rs. {amt:.2f}. New balance: Rs. {new_bal:.2f}")
                else:
                    print(f"❌ {msg}")
            except ValueError:
                print("❌ Invalid amount.")

        elif choice == "4":
            print("\n--- Last 5 Transactions ---")
            rows = mini_statement(acc_no, 5)
            if not rows:
                print("No transactions yet.")
            else:
                print(f"{'Type':<15}{'Amount':>12}{'Balance':>14}   Time")
                print("-" * 65)
                for r in rows:
                    print(f"{r['txn_type']:<15}"
                          f"{r['amount']:>12.2f}"
                          f"{r['balance_after']:>14.2f}   {r['txn_time']}")

        elif choice == "5":
            print("\n👋 Logged out. Thank you!")
            return

        else:
            print("❌ Invalid choice.")


# ============================================================
# MAIN ENTRY POINT
# ============================================================
def main():
    print("=" * 55)
    print("        💳  WELCOME TO PYTHON ATM  💳")
    print("=" * 55)

    while True:
        print("\n1. Login")
        print("2. New User (Create Account)")
        print("3. Exit")
        opt = input("Choose an option (1-3): ").strip()

        if opt == "1":
            user = login()
            if user:
                atm_menu(user)

        elif opt == "2":
            create_account()

        elif opt == "3":
            print("\nThank you for using our ATM. Goodbye!")
            break

        else:
            print("❌ Invalid choice. Try again.")


if __name__ == "__main__":
    main()