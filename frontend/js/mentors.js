/**
 * CampusConnect - Mentor Marketplace & Profile Controller
 */

let currentSelectedSkills = [];
let allMentorsList = [];
let currentViewingMentor = null;

document.addEventListener("DOMContentLoaded", async () => {
  // Check auth and initialize nav
  const isAuth = await Auth.requireAuth();
  if (!isAuth) return;
  await Auth.initGlobalNav();

  // Page detection: mentors.html vs mentor-profile.html
  const isProfilePage = window.location.pathname.includes("mentor-profile.html");

  if (isProfilePage) {
    initMentorProfilePage();
  } else {
    initMentorsSearchPage();
  }
});

/**
 * =========================================================================
 * MENTOR DISCOVERY / SEARCH PAGE (mentors.html)
 * =========================================================================
 */
function initMentorsSearchPage() {
  const searchInput = document.getElementById("mentor-search-input");
  const skillChipsContainer = document.getElementById("skill-filter-chips");

  // Initial Load
  loadMentors();

  // Search input with debounce
  if (searchInput) {
    searchInput.addEventListener("input", Utils.debounce(() => {
      filterAndRenderMentors();
    }, 300));
  }

  // Skill filter chip click delegation
  if (skillChipsContainer) {
    skillChipsContainer.addEventListener("click", (e) => {
      const chip = e.target.closest(".skill-filter-btn");
      if (!chip) return;

      const skill = chip.dataset.skill;
      if (skill === "all") {
        currentSelectedSkills = [];
        skillChipsContainer.querySelectorAll(".skill-filter-btn").forEach(btn => btn.classList.remove("active"));
        chip.classList.add("active");
      } else {
        const allBtn = skillChipsContainer.querySelector('[data-skill="all"]');
        if (allBtn) allBtn.classList.remove("active");

        if (currentSelectedSkills.includes(skill)) {
          currentSelectedSkills = currentSelectedSkills.filter(s => s !== skill);
          chip.classList.remove("active");
          if (currentSelectedSkills.length === 0 && allBtn) {
            allBtn.classList.add("active");
          }
        } else {
          currentSelectedSkills.push(skill);
          chip.classList.add("active");
        }
      }

      loadMentors();
    });
  }
}

async function loadMentors() {
  const container = document.getElementById("mentors-grid-container");
  if (!container) return;

  container.innerHTML = UI.createSkeleton("card", 6);

  try {
    const data = await api.mentors.search(currentSelectedSkills, 30);
    allMentorsList = Array.isArray(data) ? data : [];

    filterAndRenderMentors();
  } catch (err) {
    console.error("Error loading mentors", err);
    UI.renderError(container, err.message || "Failed to load mentors.", () => loadMentors());
  }
}

function filterAndRenderMentors() {
  const container = document.getElementById("mentors-grid-container");
  const searchInput = document.getElementById("mentor-search-input");
  const countBadge = document.getElementById("mentors-count-badge");
  if (!container) return;

  const query = searchInput ? searchInput.value.toLowerCase().trim() : "";

  let filtered = allMentorsList;
  if (query) {
    filtered = filtered.filter(m => {
      const name = `${m.first_name || ''} ${m.last_name || ''}`.toLowerCase();
      const bio = (m.bio || '').toLowerCase();
      const skills = (m.expertise || []).map(s => s.toLowerCase()).join(" ");
      const college = (m.college || '').toLowerCase();
      return name.includes(query) || bio.includes(query) || skills.includes(query) || college.includes(query);
    });
  }

  if (countBadge) {
    countBadge.textContent = `${filtered.length} mentors available`;
  }

  if (filtered.length === 0) {
    UI.renderEmptyState(container, {
      icon: "bi-search",
      title: "No mentors matched your search",
      description: "Try adjusting your search terms or exploring other skill filters.",
      actionText: "Clear Filters",
      actionCallback: () => {
        if (searchInput) searchInput.value = "";
        currentSelectedSkills = [];
        const allBtn = document.querySelector('[data-skill="all"]');
        if (allBtn) {
          document.querySelectorAll(".skill-filter-btn").forEach(b => b.classList.remove("active"));
          allBtn.classList.add("active");
        }
        loadMentors();
      }
    });
    return;
  }

  let html = "";
  filtered.forEach(m => {
    const initials = Utils.getInitials(m.first_name, m.last_name);
    const skillsHtml = (m.expertise || []).map(skill => 
      `<span class="skill-chip">${Utils.escapeHtml(skill)}</span>`
    ).join("");

    html += `
      <div class="col-md-6 col-lg-4 mb-4">
        <div class="mentor-card">
          <div class="mentor-card-top">
            <div class="mentor-avatar-wrap">
              <div class="mentor-avatar">${initials}</div>
              <div class="verified-badge" title="Verified"><i class="bi bi-check"></i></div>
            </div>
            <div class="mentor-info">
              <h5 class="mentor-name">${Utils.escapeHtml(m.first_name)} ${Utils.escapeHtml(m.last_name)}</h5>
              <div class="mentor-college">
                <i class="bi bi-building"></i>
                <span>${Utils.escapeHtml(m.college || "CampusConnect University")}</span>
              </div>
              <div class="mentor-rating-row">
                ${UI.renderStars(m.rating || 5.0)}
                <span class="text-muted small">(${m.total_sessions || 0} sessions)</span>
              </div>
            </div>
          </div>

          <p class="mentor-bio">${Utils.escapeHtml(m.bio || "Dedicated mentor offering practical guidance, career advice, and interview preparation.")}</p>

          <div class="skill-chips">
            ${skillsHtml || '<span class="skill-chip">Mentorship</span>'}
          </div>

          <div class="mentor-card-footer">
            <div class="mentor-price-wrap">
              <span class="mentor-price">${Utils.formatCurrency(m.hourly_rate)}</span>
              <span class="mentor-price-label">per hour</span>
            </div>
            <div class="d-flex gap-2">
              <button type="button" class="btn btn-outline-primary btn-sm calculate-cost-btn" data-mentor-id="${m.id}" data-mentor-name="${Utils.escapeHtml(m.first_name + ' ' + m.last_name)}" data-mentor-rate="${m.hourly_rate}">
                <i class="bi bi-calculator"></i> Cost
              </button>
              <a href="mentor-profile.html?id=${m.id}" class="btn btn-primary btn-sm">
                Profile
              </a>
            </div>
          </div>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;

  // Attach Calculate Cost Quick Modal Triggers
  container.querySelectorAll(".calculate-cost-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      openCostCalculatorModal(btn.dataset.mentorId, btn.dataset.mentorName, btn.dataset.mentorRate);
    });
  });
}

/**
 * =========================================================================
 * MENTOR PROFILE PAGE (mentor-profile.html)
 * =========================================================================
 */
async function initMentorProfilePage() {
  const mentorId = Utils.getParam("id");
  if (!mentorId) {
    UI.toast({ type: "error", title: "Error", message: "No mentor ID specified in URL." });
    setTimeout(() => window.location.href = "mentors.html", 1500);
    return;
  }

  const container = document.getElementById("mentor-profile-container");
  if (container) {
    container.innerHTML = `
      <div class="cc-card p-5 text-center">
        <div class="spinner-border text-primary mb-3" role="status"></div>
        <p class="text-muted">Loading mentor profile...</p>
      </div>
    `;
  }

  try {
    const mentor = await api.mentors.get(mentorId);
    currentViewingMentor = mentor;
    renderMentorProfile(mentor);
  } catch (err) {
    console.error("Error fetching mentor profile", err);
    if (container) {
      UI.renderError(container, "Could not find mentor profile.", () => initMentorProfilePage());
    }
  }
}

function renderMentorProfile(m) {
  const container = document.getElementById("mentor-profile-container");
  if (!container) return;

  const initials = Utils.getInitials(m.first_name, m.last_name);
  const fullName = `${m.first_name || ''} ${m.last_name || ''}`.trim();
  const skillsHtml = (m.expertise || []).map(skill => 
    `<span class="skill-chip py-1 px-3 fs-6">${Utils.escapeHtml(skill)}</span>`
  ).join("");

  container.innerHTML = `
    <div class="row">
      <!-- Left Profile Card -->
      <div class="col-lg-8 mb-4">
        <div class="cc-card mb-4">
          <div class="d-flex flex-column flex-sm-row align-items-center align-items-sm-start gap-4 mb-4 pb-4 border-bottom">
            <div class="mentor-avatar mentor-avatar-lg">
              ${initials}
            </div>
            <div class="text-center text-sm-start flex-grow-1">
              <div class="d-flex align-items-center justify-content-center justify-content-sm-start gap-2 mb-1">
                <h2 class="font-heading fw-bold mb-0">${Utils.escapeHtml(fullName)}</h2>
                <span class="badge bg-primary text-white rounded-pill"><i class="bi bi-patch-check-fill me-1"></i>Verified Mentor</span>
              </div>
              <p class="text-muted mb-2"><i class="bi bi-building me-1"></i>${Utils.escapeHtml(m.college || "CampusConnect University")}</p>
              <div class="d-flex align-items-center justify-content-center justify-content-sm-start gap-3">
                <div>${UI.renderStars(m.rating || 5.0)}</div>
                <div class="text-muted small">• ${m.total_sessions || 0} completed sessions</div>
              </div>
            </div>
          </div>

          <h5 class="fw-bold mb-3">About Me</h5>
          <p class="text-secondary leading-relaxed mb-4">${Utils.escapeHtml(m.bio || "Passionate about empowering the next generation of students and professionals.")}</p>

          <h5 class="fw-bold mb-3">Areas of Expertise</h5>
          <div class="skill-chips mb-4">
            ${skillsHtml || '<span class="skill-chip">Mentorship</span>'}
          </div>

          <div class="alert alert-light border d-flex align-items-center gap-3 p-3 rounded-3 mb-0">
            <i class="bi bi-shield-check fs-3 text-success"></i>
            <div class="small text-secondary">
              <strong>CampusConnect Guarantee:</strong> Verified profile credentials with end-to-end booking protection and quality assurance.
            </div>
          </div>
        </div>
      </div>

      <!-- Right Booking / Action Card -->
      <div class="col-lg-4 mb-4">
        <div class="cc-card sticky-top" style="top: 90px;">
          <div class="d-flex justify-content-between align-items-baseline mb-3 pb-3 border-bottom">
            <div>
              <span class="fs-6 text-muted">Session Rate</span>
              <div class="fs-2 font-heading fw-extrabold text-dark">${Utils.formatCurrency(m.hourly_rate)}</div>
            </div>
            <span class="badge bg-light text-dark border">60 Mins Standard</span>
          </div>

          <!-- Pricing tier indicator -->
          <div class="p-2 mb-3 rounded-2 bg-light border small text-muted">
            <i class="bi bi-info-circle text-primary me-1"></i> Same College discounts are calculated automatically at checkout.
          </div>

          <div class="d-grid gap-2 mb-3">
            <button type="button" class="btn btn-primary btn-lg" id="book-session-trigger-btn">
              <i class="bi bi-calendar-plus me-1"></i> Book a Session
            </button>
            <button type="button" class="btn btn-outline-primary" id="calculate-cost-trigger-btn">
              <i class="bi bi-calculator me-1"></i> Calculate Session Cost
            </button>
            <a href="messages.html?user=${m.id}" class="btn btn-outline-secondary">
              <i class="bi bi-chat-dots me-1"></i> Send Message
            </a>
          </div>

          <div class="text-center text-muted small">
            <i class="bi bi-clock-history me-1"></i> Usually responds within 24 hours
          </div>
        </div>
      </div>
    </div>
  `;

  // Attach button triggers
  document.getElementById("calculate-cost-trigger-btn")?.addEventListener("click", () => {
    openCostCalculatorModal(m.id, fullName, m.hourly_rate);
  });

  document.getElementById("book-session-trigger-btn")?.addEventListener("click", () => {
    openBookingModal(m);
  });
}

/**
 * =========================================================================
 * REAL-TIME COST CALCULATOR MODAL (Calling POST /api/mentors/calculate-cost)
 * =========================================================================
 */
function openCostCalculatorModal(mentorId, mentorName, baseRate) {
  let modalEl = document.getElementById("cc-cost-modal");
  if (!modalEl) {
    modalEl = document.createElement("div");
    modalEl.id = "cc-cost-modal";
    modalEl.className = "modal fade";
    modalEl.tabIndex = -1;
    document.body.appendChild(modalEl);
  }

  modalEl.innerHTML = `
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content border-0 shadow-lg" style="border-radius: var(--radius-lg);">
        <div class="modal-header border-bottom pb-3">
          <h5 class="modal-title font-heading fw-bold">
            <i class="bi bi-calculator text-primary me-2"></i>Cost Calculator
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body p-4">
          <p class="text-secondary small mb-3">
            Calculating real-time session cost with <strong>${Utils.escapeHtml(mentorName)}</strong> based on CampusConnect transparent pricing rules.
          </p>

          <div class="mb-3">
            <label class="form-label">Select Session Duration</label>
            <select class="form-select" id="cost-calc-duration-select">
              <option value="30">30 Minutes (Quick Doubt Clarification)</option>
              <option value="60" selected>60 Minutes (Standard Mentorship)</option>
              <option value="90">90 Minutes (Deep Dive / Mock Interview)</option>
              <option value="120">120 Minutes (Comprehensive Review)</option>
            </select>
          </div>

          <!-- Dynamic Results Container -->
          <div id="cost-calc-result-box" class="cost-calculator-card">
            <div class="text-center py-2">
              <div class="spinner-border spinner-border-sm text-primary me-2"></div> Calculating...
            </div>
          </div>
        </div>
        <div class="modal-footer border-top-0 pt-0">
          <button type="button" class="btn btn-outline-secondary btn-sm" data-bs-dismiss="modal">Close</button>
          <a href="mentor-profile.html?id=${mentorId}" class="btn btn-primary btn-sm">Proceed to Book</a>
        </div>
      </div>
    </div>
  `;

  const bsModal = new bootstrap.Modal(modalEl);
  bsModal.show();

  const durationSelect = modalEl.querySelector("#cost-calc-duration-select");
  const resultBox = modalEl.querySelector("#cost-calc-result-box");

  const runCalculation = async (duration) => {
    resultBox.innerHTML = `
      <div class="text-center py-2 text-muted">
        <div class="spinner-border spinner-border-sm text-primary me-2"></div> Calculating backend cost rules...
      </div>
    `;
    try {
      const costData = await api.mentors.calculateCost(mentorId, duration);
      
      resultBox.innerHTML = `
        <div class="cost-row">
          <span>Mentor Hourly Rate:</span>
          <span class="fw-semibold">${Utils.formatCurrency(costData.base_rate)}/hr</span>
        </div>
        <div class="cost-row">
          <span>Session Duration:</span>
          <span>${duration} mins</span>
        </div>
        <div class="cost-row">
          <span>Standard Base Cost:</span>
          <span>${Utils.formatCurrency(costData.hourly_cost)}</span>
        </div>
        <div class="cost-row">
          <span>Platform Fee (${(costData.commission_rate * 100).toFixed(0)}%):</span>
          <span>${Utils.formatCurrency(costData.platform_commission)}</span>
        </div>
        <div class="cost-row total">
          <span>Total You Pay:</span>
          <span class="text-primary fs-5">${Utils.formatCurrency(costData.student_pays)}</span>
        </div>
        <div class="text-muted" style="font-size: 0.75rem; margin-top: 6px;">
          * Mentor receives ${Utils.formatCurrency(costData.mentor_receives)} after platform service fee.
        </div>
      `;
    } catch (err) {
      resultBox.innerHTML = `
        <div class="text-danger small py-2">
          <i class="bi bi-exclamation-circle me-1"></i> ${Utils.escapeHtml(err.message || "Failed to calculate cost.")}
        </div>
      `;
    }
  };

  runCalculation(60);

  durationSelect.addEventListener("change", (e) => {
    runCalculation(parseInt(e.target.value, 10));
  });
}

/**
 * =========================================================================
 * BOOKING MODAL (Calling POST /api/bookings/)
 * =========================================================================
 */
function openBookingModal(mentor) {
  let modalEl = document.getElementById("cc-booking-modal");
  if (!modalEl) {
    modalEl = document.createElement("div");
    modalEl.id = "cc-booking-modal";
    modalEl.className = "modal fade";
    modalEl.tabIndex = -1;
    document.body.appendChild(modalEl);
  }

  // Calculate a default tomorrow 10:00 AM date string for the datetime-local input
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  tomorrow.setHours(10, 0, 0, 0);
  const defaultDateTime = tomorrow.toISOString().slice(0, 16);

  modalEl.innerHTML = `
    <div class="modal-dialog modal-dialog-centered modal-lg">
      <div class="modal-content border-0 shadow-lg" style="border-radius: var(--radius-lg);">
        <div class="modal-header border-bottom">
          <h5 class="modal-title font-heading fw-bold">
            <i class="bi bi-calendar-plus text-primary me-2"></i>Book Mentorship Session
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <form id="session-booking-form">
          <div class="modal-body p-4">
            <div class="alert alert-light border d-flex align-items-center gap-3 p-3 mb-4 rounded-3">
              <div class="mentor-avatar" style="width: 44px; height: 44px; font-size: 1rem;">
                ${Utils.getInitials(mentor.first_name, mentor.last_name)}
              </div>
              <div>
                <h6 class="fw-bold mb-0">${Utils.escapeHtml(mentor.first_name)} ${Utils.escapeHtml(mentor.last_name)}</h6>
                <div class="text-muted small">${Utils.escapeHtml(mentor.college || 'Verified Mentor')} • ${Utils.formatCurrency(mentor.hourly_rate)}/hr</div>
              </div>
            </div>

            <div class="row g-3">
              <div class="col-12">
                <label class="form-label" for="booking-title">Session Title <span class="text-danger">*</span></label>
                <input type="text" class="form-control" id="booking-title" placeholder="e.g. System Design Guidance & Resume Review" required>
              </div>

              <div class="col-md-6">
                <label class="form-label" for="booking-datetime">Scheduled Date & Time <span class="text-danger">*</span></label>
                <input type="datetime-local" class="form-control" id="booking-datetime" value="${defaultDateTime}" required>
              </div>

              <div class="col-md-6">
                <label class="form-label" for="booking-duration">Duration <span class="text-danger">*</span></label>
                <select class="form-select" id="booking-duration" required>
                  <option value="30">30 Minutes</option>
                  <option value="60" selected>60 Minutes (1 Hour)</option>
                  <option value="90">90 Minutes</option>
                  <option value="120">120 Minutes (2 Hours)</option>
                </select>
              </div>

              <div class="col-12">
                <label class="form-label" for="booking-description">Goals & Questions for the Mentor</label>
                <textarea class="form-control" id="booking-description" rows="3" placeholder="Share specific topics, doubts, or project links you want to discuss during this session..."></textarea>
              </div>
            </div>
          </div>
          <div class="modal-footer border-top bg-light">
            <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
            <button type="submit" class="btn btn-primary" id="confirm-booking-btn">
              <i class="bi bi-check2-circle me-1"></i> Confirm & Request Booking
            </button>
          </div>
        </form>
      </div>
    </div>
  `;

  const bsModal = new bootstrap.Modal(modalEl);
  bsModal.show();

  const form = modalEl.querySelector("#session-booking-form");
  const submitBtn = modalEl.querySelector("#confirm-booking-btn");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const title = document.getElementById("booking-title").value.trim();
    const scheduledAtRaw = document.getElementById("booking-datetime").value;
    const durationMinutes = parseInt(document.getElementById("booking-duration").value, 10);
    const description = document.getElementById("booking-description").value.trim();

    if (!title || !scheduledAtRaw) {
      UI.toast({ type: "warning", title: "Missing Fields", message: "Please enter session title and schedule time." });
      return;
    }

    const scheduledDate = new Date(scheduledAtRaw);
    if (isNaN(scheduledDate.getTime())) {
      UI.toast({ type: "error", title: "Invalid Date", message: "Please pick a valid date and time." });
      return;
    }

    UI.setLoading(submitBtn, true, "Creating booking...");

    try {
      const payload = {
        mentor_id: mentor.id,
        scheduled_at: scheduledDate.toISOString(),
        duration_minutes: durationMinutes,
        title: title,
        description: description || undefined
      };

      const bookingResponse = await api.bookings.create(payload);
      UI.setLoading(submitBtn, false);
      bsModal.hide();

      UI.toast({
        type: "success",
        title: "Session Booked!",
        message: "Your mentorship session request has been submitted successfully."
      });

      // Redirect to booking details / payments
      setTimeout(() => {
        window.location.href = `booking-detail.html?id=${bookingResponse.id}`;
      }, 1200);
    } catch (err) {
      UI.setLoading(submitBtn, false);
      console.error("Booking error", err);
      UI.toast({
        type: "error",
        title: "Booking Failed",
        message: err.message || "Failed to create booking."
      });
    }
  });
}
