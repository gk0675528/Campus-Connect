/**
 * CampusConnect - UI Helper and Component System
 */

const UI = {
  /**
   * Toast notification system
   * @param {Object} options - { type: 'success'|'error'|'warning'|'info', title, message, duration }
   */
  toast({ type = "info", title = "", message = "", duration = 4000 }) {
    let container = document.getElementById("toast-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "toast-container";
      container.className = "toast-container";
      document.body.appendChild(container);
    }

    const iconMap = {
      success: '<i class="bi bi-check-circle-fill text-success"></i>',
      error: '<i class="bi bi-x-circle-fill text-danger"></i>',
      warning: '<i class="bi bi-exclamation-triangle-fill text-warning"></i>',
      info: '<i class="bi bi-info-circle-fill text-primary"></i>'
    };

    const toastEl = document.createElement("div");
    toastEl.className = "custom-toast animate-fade-in";
    toastEl.innerHTML = `
      <div class="d-flex align-items-center p-3">
        <div class="fs-4 me-3 flex-shrink-0">
          ${iconMap[type] || iconMap.info}
        </div>
        <div class="flex-grow-1 min-w-0">
          ${title ? `<div class="fw-bold text-dark fs-6 mb-1">${Utils.escapeHtml(title)}</div>` : ""}
          <div class="text-secondary small">${Utils.escapeHtml(message)}</div>
        </div>
        <button type="button" class="btn-close ms-2" aria-label="Close"></button>
      </div>
    `;

    container.appendChild(toastEl);

    const closeBtn = toastEl.querySelector(".btn-close");
    const removeToast = () => {
      toastEl.style.opacity = "0";
      toastEl.style.transform = "translateY(-10px)";
      toastEl.style.transition = "all 0.2s ease";
      setTimeout(() => toastEl.remove(), 200);
    };

    closeBtn.addEventListener("click", removeToast);
    if (duration > 0) {
      setTimeout(removeToast, duration);
    }
  },

  /**
   * Loading state manager for buttons
   */
  setLoading(button, isLoading, loadingText = "Loading...") {
    if (!button) return;
    if (isLoading) {
      button.dataset.originalHtml = button.innerHTML;
      button.disabled = true;
      button.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>${Utils.escapeHtml(loadingText)}`;
    } else {
      button.disabled = false;
      if (button.dataset.originalHtml) {
        button.innerHTML = button.dataset.originalHtml;
      }
    }
  },

  /**
   * Star rating component renderer
   */
  renderStars(rating = 0) {
    const validRating = Math.max(0, Math.min(5, Number(rating) || 0));
    let starsHtml = '<div class="rating-stars" aria-label="' + validRating + ' out of 5 stars">';
    for (let i = 1; i <= 5; i++) {
      if (validRating >= i) {
        starsHtml += '<i class="bi bi-star-fill"></i>';
      } else if (validRating >= i - 0.5) {
        starsHtml += '<i class="bi bi-star-half"></i>';
      } else {
        starsHtml += '<i class="bi bi-star"></i>';
      }
    }
    starsHtml += ` <span class="fw-bold text-dark ms-1">${validRating > 0 ? validRating.toFixed(1) : "New"}</span></div>`;
    return starsHtml;
  },

  /**
   * Render empty state in container
   */
  renderEmptyState(container, {
    icon = "bi-inbox",
    title = "No Data Found",
    description = "There is nothing here yet.",
    actionText = "",
    actionHref = "",
    actionCallback = null,
    actionId = "empty-state-action"
  }) {
    if (!container) return;
    const actionButtonHtml = actionText ? `
      <a href="${actionHref || 'javascript:void(0)'}" id="${actionId}" class="btn btn-primary btn-sm mt-2">
        ${Utils.escapeHtml(actionText)}
      </a>
    ` : "";

    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">
          <i class="bi ${icon}"></i>
        </div>
        <h4 class="empty-state-title">${Utils.escapeHtml(title)}</h4>
        <p class="empty-state-text">${Utils.escapeHtml(description)}</p>
        ${actionButtonHtml}
      </div>
    `;

    if (actionCallback && actionText) {
      const btn = container.querySelector(`#${actionId}`);
      if (btn) {
        btn.addEventListener("click", (e) => {
          if (!actionHref) e.preventDefault();
          actionCallback();
        });
      }
    }
  },

  /**
   * Render error alert with retry button
   */
  renderError(container, message = "Unable to load data.", retryCallback = null) {
    if (!container) return;
    container.innerHTML = `
      <div class="alert alert-danger d-flex align-items-center justify-content-between p-3 rounded-3" role="alert">
        <div class="d-flex align-items-center">
          <i class="bi bi-exclamation-octagon-fill fs-4 me-3"></i>
          <div>
            <strong>Error:</strong> ${Utils.escapeHtml(message)}
          </div>
        </div>
        ${retryCallback ? '<button type="button" class="btn btn-sm btn-outline-danger retry-btn ms-3"><i class="bi bi-arrow-clockwise me-1"></i>Retry</button>' : ''}
      </div>
    `;

    if (retryCallback) {
      const retryBtn = container.querySelector(".retry-btn");
      if (retryBtn) {
        retryBtn.addEventListener("click", retryCallback);
      }
    }
  },

  /**
   * Skeleton loader generator
   */
  createSkeleton(type = "card", count = 3) {
    let html = "";
    for (let i = 0; i < count; i++) {
      if (type === "card") {
        html += `
          <div class="col-md-6 col-lg-4 mb-4">
            <div class="cc-card">
              <div class="d-flex gap-3 mb-3">
                <div class="skeleton skeleton-avatar"></div>
                <div class="flex-grow-1">
                  <div class="skeleton skeleton-title"></div>
                  <div class="skeleton skeleton-text" style="width: 50%;"></div>
                  <div class="skeleton skeleton-text" style="width: 70%;"></div>
                </div>
              </div>
              <div class="skeleton skeleton-text"></div>
              <div class="skeleton skeleton-text" style="width: 80%;"></div>
              <div class="d-flex justify-content-between mt-3 pt-3 border-top">
                <div class="skeleton skeleton-text" style="width: 30%;"></div>
                <div class="skeleton skeleton-text" style="width: 30%;"></div>
              </div>
            </div>
          </div>
        `;
      } else if (type === "list") {
        html += `
          <div class="p-3 mb-2 cc-card d-flex align-items-center gap-3">
            <div class="skeleton" style="width: 42px; height: 42px; border-radius: 8px;"></div>
            <div class="flex-grow-1">
              <div class="skeleton skeleton-text" style="width: 40%; height: 16px;"></div>
              <div class="skeleton skeleton-text" style="width: 70%; height: 12px;"></div>
            </div>
          </div>
        `;
      }
    }
    return html;
  },

  /**
   * Dynamic Modal Generator
   */
  showConfirmModal({
    title = "Confirm Action",
    message = "Are you sure you want to proceed?",
    confirmText = "Confirm",
    confirmClass = "btn-danger",
    onConfirm = () => {}
  }) {
    let modalEl = document.getElementById("cc-dynamic-modal");
    if (!modalEl) {
      modalEl = document.createElement("div");
      modalEl.id = "cc-dynamic-modal";
      modalEl.className = "modal fade";
      modalEl.tabIndex = -1;
      document.body.appendChild(modalEl);
    }

    modalEl.innerHTML = `
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content border-0 shadow-lg" style="border-radius: var(--radius-lg);">
          <div class="modal-header border-bottom-0 pb-0">
            <h5 class="modal-title font-heading fw-bold">${Utils.escapeHtml(title)}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body py-3">
            <p class="text-secondary mb-0">${Utils.escapeHtml(message)}</p>
          </div>
          <div class="modal-footer border-top-0 pt-0">
            <button type="button" class="btn btn-outline-secondary btn-sm" data-bs-dismiss="modal">Cancel</button>
            <button type="button" class="btn ${confirmClass} btn-sm" id="cc-modal-confirm-btn">${Utils.escapeHtml(confirmText)}</button>
          </div>
        </div>
      </div>
    `;

    const bsModal = new bootstrap.Modal(modalEl);
    const confirmBtn = modalEl.querySelector("#cc-modal-confirm-btn");
    
    confirmBtn.onclick = () => {
      bsModal.hide();
      onConfirm();
    };

    bsModal.show();
  }
};
