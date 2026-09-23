/**
 * CampusConnect - Bookings & Sessions Controller
 */

let currentBookingData = null;

document.addEventListener("DOMContentLoaded", async () => {
  const isAuth = await Auth.requireAuth();
  if (!isAuth) return;
  await Auth.initGlobalNav();

  const isDetailPage = window.location.pathname.includes("booking-detail.html");

  if (isDetailPage) {
    initBookingDetailPage();
  } else {
    initBookingsListPage();
  }
});

/**
 * =========================================================================
 * BOOKINGS LIST PAGE (bookings.html)
 * =========================================================================
 */
async function initBookingsListPage() {
  const container = document.getElementById("bookings-list-container");
  if (!container) return;

  container.innerHTML = UI.createSkeleton("list", 4);

  try {
    // Current backend doesn't have a dedicated GET /api/bookings/ filter endpoint,
    // so we fetch notifications to extract recent session IDs or check the state.
    const notifs = await api.notifications.list(false, 30);
    const bookingNotifs = (notifs.notifications || []).filter(n => n.notification_type === "booking" || n.notification_type === "session");

    if (bookingNotifs.length === 0) {
      UI.renderEmptyState(container, {
        icon: "bi-calendar2-x",
        title: "No bookings found",
        description: "You have not booked any mentorship sessions yet. Start by finding a mentor.",
        actionText: "Explore Mentors",
        actionHref: "mentors.html"
      });
      return;
    }

    let html = "";
    bookingNotifs.forEach(item => {
      const sessionId = item.related_id;
      html += `
        <div class="session-card d-flex flex-column flex-md-row align-items-md-center justify-content-between gap-3">
          <div class="d-flex align-items-start gap-3">
            <div class="session-date-badge">
              <div class="session-date-month">${new Date(item.created_at).toLocaleString('en-US', { month: 'short' })}</div>
              <div class="session-date-day">${new Date(item.created_at).getDate()}</div>
            </div>
            <div>
              <div class="d-flex align-items-center gap-2 mb-1">
                <h5 class="fw-bold text-dark mb-0">${Utils.escapeHtml(item.title)}</h5>
                <span class="badge badge-status badge-pending">Active</span>
              </div>
              <p class="text-secondary small mb-2">${Utils.escapeHtml(item.message)}</p>
              <div class="text-muted small">
                <i class="bi bi-clock me-1"></i>${Utils.formatTime(item.created_at)}
              </div>
            </div>
          </div>
          <div class="d-flex gap-2 align-self-end align-self-md-center">
            ${sessionId ? `<a href="booking-detail.html?id=${sessionId}" class="btn btn-outline-primary btn-sm">Session Details</a>` : ''}
            <a href="mentors.html" class="btn btn-primary btn-sm">Book Another</a>
          </div>
        </div>
      `;
    });

    container.innerHTML = html;
  } catch (err) {
    console.error("Error loading bookings", err);
    UI.renderEmptyState(container, {
      icon: "bi-calendar2-check",
      title: "Your mentorship schedule",
      description: "Book guidance sessions with seniors, professors, and industry leaders.",
      actionText: "Find a Mentor",
      actionHref: "mentors.html"
    });
  }
}

/**
 * =========================================================================
 * BOOKING DETAIL PAGE (booking-detail.html)
 * =========================================================================
 */
async function initBookingDetailPage() {
  const sessionId = Utils.getParam("id");
  if (!sessionId) {
    UI.toast({ type: "error", title: "Error", message: "No session ID specified." });
    setTimeout(() => window.location.href = "bookings.html", 1500);
    return;
  }

  const container = document.getElementById("booking-detail-container");
  if (container) {
    container.innerHTML = `
      <div class="cc-card p-5 text-center">
        <div class="spinner-border text-primary mb-3" role="status"></div>
        <p class="text-muted">Loading session details...</p>
      </div>
    `;
  }

  try {
    const session = await api.bookings.get(sessionId);
    currentBookingData = session;
    renderBookingDetail(session);
  } catch (err) {
    console.error("Error fetching session detail", err);
    if (container) {
      UI.renderError(container, err.message || "Failed to load booking details.", () => initBookingDetailPage());
    }
  }
}

function renderBookingDetail(session) {
  const container = document.getElementById("booking-detail-container");
  if (!container) return;

  const statusClassMap = {
    pending: "badge-pending",
    confirmed: "badge-confirmed",
    completed: "badge-completed",
    cancelled: "badge-cancelled"
  };
  const statusBadgeClass = statusClassMap[session.status.toLowerCase()] || "badge-pending";

  const isPending = session.status.toLowerCase() === "pending";
  const isConfirmed = session.status.toLowerCase() === "confirmed";
  const isCompleted = session.status.toLowerCase() === "completed";
  const isCancelled = session.status.toLowerCase() === "cancelled";

  container.innerHTML = `
    <div class="row">
      <div class="col-lg-8 mb-4">
        <div class="cc-card mb-4">
          <div class="d-flex justify-content-between align-items-start pb-3 mb-3 border-bottom">
            <div>
              <span class="text-muted small">Session Reference: <code>${session.id}</code></span>
              <h3 class="font-heading fw-bold text-dark mt-1 mb-0">${Utils.escapeHtml(session.title)}</h3>
            </div>
            <span class="badge badge-status ${statusBadgeClass} text-uppercase px-3 py-2 fs-6">
              ${Utils.escapeHtml(session.status)}
            </span>
          </div>

          <div class="row g-3 mb-4">
            <div class="col-sm-6">
              <div class="p-3 bg-light rounded-3">
                <span class="text-muted small d-block mb-1"><i class="bi bi-calendar3 me-1"></i>Date & Time</span>
                <span class="fw-bold text-dark">${Utils.formatDate(session.scheduled_at)} at ${Utils.formatTime(session.scheduled_at)}</span>
              </div>
            </div>
            <div class="col-sm-6">
              <div class="p-3 bg-light rounded-3">
                <span class="text-muted small d-block mb-1"><i class="bi bi-hourglass-split me-1"></i>Duration</span>
                <span class="fw-bold text-dark">${Utils.formatDuration(session.duration_minutes || 60)}</span>
              </div>
            </div>
          </div>

          <h5 class="fw-bold mb-2">Session Description & Agenda</h5>
          <p class="text-secondary mb-4">${Utils.escapeHtml(session.description || "No specific agenda provided.")}</p>

          <!-- Meeting Link if Confirmed -->
          ${isConfirmed ? `
            <div class="alert alert-success border d-flex align-items-center justify-content-between p-3 rounded-3 mb-4">
              <div>
                <h6 class="fw-bold text-success mb-1"><i class="bi bi-camera-video-fill me-2"></i>Virtual Meeting Room</h6>
                <span class="small">Join the live session at the scheduled time.</span>
              </div>
              <a href="#" class="btn btn-success btn-sm disabled" title="Link active 10 mins prior to session">Join Meeting</a>
            </div>
          ` : ''}

          <!-- Feedback Section if Completed -->
          ${isCompleted ? `
            <div class="border rounded-3 p-4 bg-light mb-4" id="session-feedback-box">
              <h5 class="fw-bold mb-2"><i class="bi bi-star-fill text-warning me-2"></i>Rate & Review this Session</h5>
              <p class="text-secondary small mb-3">Your feedback helps mentors improve and helps fellow students choose the best guide.</p>
              <button type="button" class="btn btn-outline-primary btn-sm" id="open-feedback-modal-btn">
                <i class="bi bi-pencil-square me-1"></i> Submit Session Feedback
              </button>
            </div>
          ` : ''}

          <!-- Action Buttons -->
          <div class="d-flex flex-wrap gap-2 pt-3 border-top">
            ${(!isCancelled && !isCompleted) ? `
              <button type="button" class="btn btn-outline-danger btn-sm" id="cancel-booking-btn">
                <i class="bi bi-x-circle me-1"></i> Cancel Session
              </button>
            ` : ''}
            <a href="messages.html" class="btn btn-outline-secondary btn-sm">
              <i class="bi bi-chat-dots me-1"></i> Message Mentor
            </a>
            <a href="bookings.html" class="btn btn-link btn-sm text-secondary ms-auto">
              <i class="bi bi-arrow-left me-1"></i> Back to Sessions
            </a>
          </div>
        </div>
      </div>

      <!-- Right Summary & Payment Card -->
      <div class="col-lg-4 mb-4">
        <div class="cc-card">
          <h5 class="font-heading fw-bold mb-3 pb-2 border-bottom">Payment Summary</h5>

          <div class="d-flex justify-content-between py-2 text-secondary">
            <span>Session Fee:</span>
            <span class="fw-bold text-dark">${Utils.formatCurrency(session.student_pays)}</span>
          </div>

          <div class="d-flex justify-content-between py-2 text-secondary">
            <span>Mentor Payout:</span>
            <span>${Utils.formatCurrency(session.mentor_receives)}</span>
          </div>

          <div class="d-flex justify-content-between py-2 border-top mt-2 pt-2">
            <span class="fw-bold text-dark">Total Amount:</span>
            <span class="fw-extrabold text-primary fs-5">${Utils.formatCurrency(session.student_pays)}</span>
          </div>

          ${isPending && session.student_pays > 0 ? `
            <div class="mt-4">
              <a href="payments.html?session_id=${session.id}&amount=${session.student_pays}" class="btn btn-primary btn-lg w-100">
                <i class="bi bi-credit-card me-1"></i> Pay Now
              </a>
              <div class="text-center text-muted small mt-2">
                <i class="bi bi-lock-fill text-success me-1"></i> Secure 256-bit payment checkout
              </div>
            </div>
          ` : ''}

          ${session.student_pays === 0 ? `
            <div class="alert alert-success text-center small mt-3 mb-0 p-2 rounded-2">
              <i class="bi bi-gift-fill me-1"></i> Free Session (Same College Policy)
            </div>
          ` : ''}
        </div>
      </div>
    </div>
  `;

  // Attach Cancel Session Handler
  document.getElementById("cancel-booking-btn")?.addEventListener("click", () => {
    UI.showConfirmModal({
      title: "Cancel Mentorship Session",
      message: "Are you sure you want to cancel this booking? This action cannot be undone.",
      confirmText: "Yes, Cancel Booking",
      confirmClass: "btn-danger",
      onConfirm: async () => {
        try {
          await api.bookings.cancel(session.id);
          UI.toast({
            type: "success",
            title: "Booking Cancelled",
            message: "The session has been cancelled."
          });
          initBookingDetailPage();
        } catch (err) {
          UI.toast({
            type: "error",
            title: "Cancellation Failed",
            message: err.message || "Unable to cancel session."
          });
        }
      }
    });
  });

  // Attach Feedback Modal Handler
  document.getElementById("open-feedback-modal-btn")?.addEventListener("click", () => {
    openFeedbackModal(session.id);
  });
}

/**
 * =========================================================================
 * 5-STAR FEEDBACK MODAL (Calling POST /api/bookings/{id}/feedback)
 * =========================================================================
 */
function openFeedbackModal(sessionId) {
  let modalEl = document.getElementById("cc-feedback-modal");
  if (!modalEl) {
    modalEl = document.createElement("div");
    modalEl.id = "cc-feedback-modal";
    modalEl.className = "modal fade";
    modalEl.tabIndex = -1;
    document.body.appendChild(modalEl);
  }

  modalEl.innerHTML = `
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content border-0 shadow-lg" style="border-radius: var(--radius-lg);">
        <div class="modal-header border-bottom">
          <h5 class="modal-title font-heading fw-bold">
            <i class="bi bi-star-fill text-warning me-2"></i>Session Feedback
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <form id="session-feedback-form">
          <div class="modal-body p-4">
            <div class="mb-3 text-center">
              <label class="form-label d-block mb-2">How would you rate this session?</label>
              <div class="d-flex justify-content-center gap-2 fs-2" id="star-rating-selector">
                <i class="bi bi-star-fill text-warning cursor-pointer" data-val="1"></i>
                <i class="bi bi-star-fill text-warning cursor-pointer" data-val="2"></i>
                <i class="bi bi-star-fill text-warning cursor-pointer" data-val="3"></i>
                <i class="bi bi-star-fill text-warning cursor-pointer" data-val="4"></i>
                <i class="bi bi-star-fill text-warning cursor-pointer" data-val="5"></i>
              </div>
              <input type="hidden" id="feedback-rating-val" value="5">
            </div>

            <div class="mb-3">
              <label class="form-label" for="feedback-review-text">Your Review & Comments <span class="text-danger">*</span></label>
              <textarea class="form-control" id="feedback-review-text" rows="4" placeholder="Share how helpful the mentor was, what you learned, and suggestions..." required></textarea>
            </div>
          </div>
          <div class="modal-footer border-top bg-light">
            <button type="button" class="btn btn-outline-secondary btn-sm" data-bs-dismiss="modal">Cancel</button>
            <button type="submit" class="btn btn-primary btn-sm" id="submit-feedback-btn">
              Submit Review
            </button>
          </div>
        </form>
      </div>
    </div>
  `;

  const bsModal = new bootstrap.Modal(modalEl);
  bsModal.show();

  // Interactive star click handler
  const starsContainer = modalEl.querySelector("#star-rating-selector");
  const ratingInput = modalEl.querySelector("#feedback-rating-val");

  starsContainer.querySelectorAll("i").forEach(star => {
    star.style.cursor = "pointer";
    star.addEventListener("click", () => {
      const val = parseInt(star.dataset.val, 10);
      ratingInput.value = val;
      starsContainer.querySelectorAll("i").forEach((s, idx) => {
        if (idx < val) {
          s.className = "bi bi-star-fill text-warning";
        } else {
          s.className = "bi bi-star text-muted";
        }
      });
    });
  });

  // Submit Feedback Handler
  const form = modalEl.querySelector("#session-feedback-form");
  const submitBtn = modalEl.querySelector("#submit-feedback-btn");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const rating = parseFloat(ratingInput.value);
    const review = modalEl.querySelector("#feedback-review-text").value.trim();

    if (!review) {
      UI.toast({ type: "warning", title: "Review Required", message: "Please write a few words about your session." });
      return;
    }

    UI.setLoading(submitBtn, true, "Submitting...");

    try {
      await api.bookings.feedback(sessionId, rating, review);
      UI.setLoading(submitBtn, false);
      bsModal.hide();

      UI.toast({
        type: "success",
        title: "Feedback Submitted",
        message: "Thank you! Your feedback has been recorded."
      });
    } catch (err) {
      UI.setLoading(submitBtn, false);
      UI.toast({
        type: "error",
        title: "Submission Failed",
        message: err.message || "Could not submit feedback."
      });
    }
  });
}
