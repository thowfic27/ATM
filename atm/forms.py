"""
Django forms for the ATM web app.

The validation rules (password rules, positive amounts) match the
original CLI in ATM.py, so both frontends behave the same way.
"""

from django import forms

from . import db


class LoginForm(forms.Form):
    """Login form - mirrors login() in ATM.py."""

    name = forms.CharField(
        label="Username",
        max_length=50,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your username",
                "autofocus": "autofocus",
                "autocomplete": "username",
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your password",
                "autocomplete": "current-password",
            }
        ),
    )


class RegisterForm(forms.Form):
    """New account form - mirrors create_account() in ATM.py."""

    name = forms.CharField(
        label="Username",
        max_length=50,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Choose a username",
                "autofocus": "autofocus",
                "autocomplete": "username",
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "At least 6 characters with 1 digit",
                "autocomplete": "new-password",
            }
        ),
    )
    confirm_password = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Re-enter your password",
                "autocomplete": "new-password",
            }
        ),
    )

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if not name:
            raise forms.ValidationError("Username cannot be empty.")
        return name

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        confirm = cleaned.get("confirm_password")

        # same rules as validate_password() in ATM.py / atm/db.py
        if password:
            ok, msg = db.validate_password(password)
            if not ok:
                self.add_error("password", msg)

        if password and confirm and password != confirm:
            self.add_error("confirm_password", "Passwords do not match.")

        return cleaned


class DepositForm(forms.Form):
    """Deposit form - menu option 2."""

    amount = forms.DecimalField(
        label="Amount (Rs.)",
        min_value=0.01,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "0.00",
                "step": "0.01",
                "min": "0.01",
                "inputmode": "decimal",
            }
        ),
    )


class WithdrawForm(forms.Form):
    """Withdraw form - menu option 3."""

    amount = forms.DecimalField(
        label="Amount (Rs.)",
        min_value=0.01,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "0.00",
                "step": "0.01",
                "min": "0.01",
                "inputmode": "decimal",
            }
        ),
    )
