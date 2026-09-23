/**
 * CampusConnect - Payments & Checkout Controller
 */

let currentPaymentSessionId = null;
let currentAmount = 0;

document.addEventListener("DOMContentLoaded", async () => {
  const isAuth = await Auth.requireAuth();
  if (!isAuth) return;
  await Auth.initGlobalNav();

  initPaymentCheckout();
});

function initPaymentCheckout() {
  currentPaymentSessionId = Utils.getParam("session_id");
  currentAmount = parseFloat(Utils.getParam("amount")) || 500;

  const amountDisplay = document.getElementById("checkout-amount-display");
  const totalDisplay = document.getElementById("checkout-total-display");
  const sessionRefDisplay = document.getElementById("checkout-session-ref");

  if (amountDisplay) amountDisplay.textContent = Utils.formatCurrency(currentAmount);
  if (totalDisplay) totalDisplay.textContent = Utils.formatCurrency(currentAmount);
  if (sessionRefDisplay && currentPaymentSessionId) {
    sessionRefDisplay.textContent = currentPaymentSessionId;
  }

  // Payment Form Handler
  const paymentForm = document.getElementById("payment-checkout-form");
  const payBtn = document.getElementById("pay-now-btn");

  if (paymentForm) {
    paymentForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      if (!currentPaymentSessionId) {
        UI.toast({
          type: "warning",
          title: "Session Missing",
          message: "No session selected for payment."
        });
        return;
      }

      const paymentMethod = document.querySelector('input[name="payment_method"]:checked')?.value || "razorpay";
      UI.setLoading(payBtn, true, "Processing Payment...");

      try {
        // 1. Create Payment Record on Backend
        const payment = await api.payments.create(currentPaymentSessionId, paymentMethod);

        // 2. Simulate transaction confirmation with backend
        const simulatedTxnId = `txn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const confirmedPayment = await api.payments.confirm(payment.id, simulatedTxnId);

        UI.setLoading(payBtn, false);

        // Show Success Modal
        showPaymentSuccessModal(confirmedPayment);
      } catch (err) {
        UI.setLoading(payBtn, false);
        console.error("Payment failed", err);
        UI.toast({
          type: "error",
          title: "Payment Failed",
          message: err.message || "Could not complete payment transaction."
        });
      }
    });
  }
}

function showPaymentSuccessModal(payment) {
  let modalEl = document.getElementById("payment-success-modal");
  if (!modalEl) {
    modalEl = document.createElement("div");
    modalEl.id = "payment-success-modal";
    modalEl.className = "modal fade";
    modalEl.setAttribute("data-bs-backdrop", "static");
    modalEl.tabIndex = -1;
    document.body.appendChild(modalEl);
  }

  modalEl.innerHTML = `
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content border-0 shadow-lg text-center p-4" style="border-radius: var(--radius-lg);">
        <div class="mb-3">
          <div class="mx-auto bg-success-light text-success rounded-circle d-flex align-items-center justify-content-center" style="width: 72px; height: 72px; font-size: 2.5rem; background-color: var(--cc-success-bg);">
            <i class="bi bi-check-circle-fill text-success"></i>
          </div>
        </div>
        <h3 class="font-heading fw-bold text-dark mb-1">Payment Successful!</h3>
        <p class="text-secondary small mb-3">Your mentorship session is now confirmed.</p>

        <div class="bg-light p-3 rounded-3 text-start mb-4 small">
          <div class="d-flex justify-content-between py-1">
            <span class="text-muted">Transaction ID:</span>
            <span class="fw-semibold text-dark font-monospace">${Utils.escapeHtml(payment.transaction_id || 'N/A')}</span>
          </div>
          <div class="d-flex justify-content-between py-1">
            <span class="text-muted">Amount Paid:</span>
            <span class="fw-bold text-success">${Utils.formatCurrency(payment.amount)}</span>
          </div>
          <div class="d-flex justify-content-between py-1">
            <span class="text-muted">Status:</span>
            <span class="badge bg-success text-white">CONFIRMED</span>
          </div>
        </div>

        <a href="booking-detail.html?id=${payment.session_id}" class="btn btn-primary btn-lg w-100">
          View Session Details
        </a>
      </div>
    </div>
  `;

  const bsModal = new bootstrap.Modal(modalEl);
  bsModal.show();
}
