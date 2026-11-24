/* ============================================================
   PyBank ATM — small UI enhancements
   Vanilla JS on top of Bootstrap 5 (loaded in base.html)
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {
    setupQuickAmounts();
    setupPasswordToggles();
    setupConfirmModals();
    setupBalanceAnimation();
    setupAutoDismissAlerts();
});

/* ------------------------------------------------------------
   Quick-amount buttons on the deposit / withdraw forms
   ------------------------------------------------------------ */
function setupQuickAmounts() {
    document.querySelectorAll("[data-quick-amount]").forEach((btn) => {
        btn.addEventListener("click", () => {
            const form = btn.closest("form");
            const input = form && form.querySelector("input[name='amount']");
            if (!input) return;

            input.value = btn.dataset.quickAmount;
            input.focus();
        });
    });
}

/* ------------------------------------------------------------
   "Show password" checkboxes on the login / register forms
   ------------------------------------------------------------ */
function setupPasswordToggles() {
    document.querySelectorAll("[data-password-toggle]").forEach((box) => {
        box.addEventListener("change", () => {
            const form = box.closest("form");
            if (!form) return;
            form.querySelectorAll("input[type='password']").forEach((input) => {
                input.type = box.checked ? "text" : "password";
            });
        });
    });
}

/* ------------------------------------------------------------
   Forms with data-confirm="..." ask for confirmation first.
   The shared #confirmModal lives in base.html.
   ------------------------------------------------------------ */
function setupConfirmModals() {
    const modalEl = document.getElementById("confirmModal");
    if (!modalEl) return;

    const modal = new bootstrap.Modal(modalEl);
    const body = modalEl.querySelector("#confirmModalBody");
    const okBtn = modalEl.querySelector("#confirmModalOk");
    let pendingForm = null;

    okBtn.addEventListener("click", () => {
        if (pendingForm) {
            pendingForm.submit(); // native submit() skips this handler
            pendingForm = null;
        }
        modal.hide();
    });

    modalEl.addEventListener("hidden.bs.modal", () => {
        pendingForm = null; // cancelled
    });

    document.querySelectorAll("form[data-confirm]").forEach((form) => {
        form.addEventListener("submit", (event) => {
            if (pendingForm === form) return; // already approved
            event.preventDefault();
            body.textContent = form.dataset.confirm;
            pendingForm = form;
            modal.show();
        });
    });
}

/* ------------------------------------------------------------
   Balance count-up animation (dashboard)
   ------------------------------------------------------------ */
function setupBalanceAnimation() {
    document.querySelectorAll(".balance-value[data-value]").forEach((el) => {
        const target = parseFloat(el.dataset.value);
        if (isNaN(target)) return;

        const duration = 900; // ms
        const start = performance.now();

        const format = (value) =>
            "Rs. " + value.toLocaleString("en-IN", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
            });

        const step = (now) => {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
            el.textContent = format(target * eased);
            if (progress < 1) {
                requestAnimationFrame(step);
            }
        };

        requestAnimationFrame(step);
    });
}

/* ------------------------------------------------------------
   Flash messages auto-dismiss after 5 seconds
   ------------------------------------------------------------ */
function setupAutoDismissAlerts() {
    document.querySelectorAll(".alert-dismissible").forEach((alert) => {
        setTimeout(() => {
            if (alert.isConnected) {
                bootstrap.Alert.getOrCreateInstance(alert).close();
            }
        }, 5000);
    });
}
