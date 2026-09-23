/**
 * CampusConnect - Student Dashboard Controller
 * Aggregates real backend data for the student dashboard.
 */

document.addEventListener("DOMContentLoaded", async () => {
  // 1. Enforce Authentication
  const isAuth = await Auth.requireAuth();
  if (!isAuth) return;

  // 2. Initialize Navigation & User Info
  await Auth.initGlobalNav();

  const user = Auth.getCurrentUser();
  const welcomeName = document.getElementById("dashboard-welcome-name");
  if (welcomeName && user) {
    welcomeName.textContent = user.first_name || user.username || "Student";
  }

  // 3. Load Dashboard Components concurrently
  loadDashboardData();
});

async function loadDashboardData() {
  loadUpcomingSessions();
  loadRecommendedMentors();
  loadRecentNotifications();
}

/**
 * Load Upcoming Sessions from Backend
 */
async function loadUpcomingSessions() {
  const container = document.getElementById("upcoming-sessions-container");
  if (!container) return;

  container.innerHTML = UI.createSkeleton("list", 2);

  try {
    // Current backend doesn't have an aggregation endpoint, so we check notifications & bookings
    // For now we check notifications or empty state cleanly
    const notifs = await api.notifications.list(false, 5);
    const sessionNotifs = (notifs.notifications || []).filter(n => n.notification_type === "booking" || n.notification_type === "session");

    if (sessionNotifs.length === 0) {
      UI.renderEmptyState(container, {
        icon: "bi-calendar-check",
        title: "No upcoming sessions",
        description: "Connect with senior mentors or professors to accelerate your learning journey.",
        actionText: "Find a Mentor",
        actionHref: "mentors.html"
      });
      return;
    }

    let html = "";
    sessionNotifs.forEach(item => {
      html += `
        <div class="session-card d-flex align-items-center justify-content-between flex-wrap gap-3">
          <div class="d-flex align-items-center gap-3">
            <div class="session-date-badge">
              <div class="session-date-month">${new Date(item.created_at).toLocaleString('en-US', { month: 'short' })}</div>
              <div class="session-date-day">${new Date(item.created_at).getDate()}</div>
            </div>
            <div>
              <h6 class="fw-bold text-dark mb-1">${Utils.escapeHtml(item.title)}</h6>
              <p class="text-muted small mb-0">${Utils.escapeHtml(item.message)}</p>
            </div>
          </div>
          <div>
            <a href="bookings.html" class="btn btn-outline-primary btn-sm">View Details</a>
          </div>
        </div>
      `;
    });

    container.innerHTML = html;
  } catch (err) {
    console.error("Error loading upcoming sessions", err);
    UI.renderEmptyState(container, {
      icon: "bi-calendar-check",
      title: "Your mentorship journey starts here",
      description: "Book your first session with verified seniors, alumni, and professors.",
      actionText: "Explore Mentors",
      actionHref: "mentors.html"
    });
  }
}

/**
 * Load Top Mentors from Backend
 */
async function loadRecommendedMentors() {
  const container = document.getElementById("recommended-mentors-container");
  if (!container) return;

  container.innerHTML = UI.createSkeleton("card", 3);

  try {
    const mentors = await api.mentors.search([], 3);

    if (!mentors || mentors.length === 0) {
      UI.renderEmptyState(container, {
        icon: "bi-people",
        title: "No mentors found",
        description: "Be the first to join or explore all verified mentors across universities.",
        actionText: "Browse All Mentors",
        actionHref: "mentors.html"
      });
      return;
    }

    let html = "";
    mentors.forEach(m => {
      const initials = Utils.getInitials(m.first_name, m.last_name);
      const skillsHtml = (m.expertise || []).slice(0, 3).map(skill => 
        `<span class="skill-chip">${Utils.escapeHtml(skill)}</span>`
      ).join("");

      html += `
        <div class="col-md-6 col-lg-4 mb-4">
          <div class="mentor-card">
            <div class="mentor-card-top">
              <div class="mentor-avatar-wrap">
                <div class="mentor-avatar">${initials}</div>
                <div class="verified-badge" title="Verified Mentor"><i class="bi bi-check"></i></div>
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

            <p class="mentor-bio">${Utils.escapeHtml(m.bio || "Passionate about helping students excel in tech, research, and career paths.")}</p>

            <div class="skill-chips">
              ${skillsHtml || '<span class="skill-chip">Career Guidance</span>'}
            </div>

            <div class="mentor-card-footer">
              <div class="mentor-price-wrap">
                <span class="mentor-price">${Utils.formatCurrency(m.hourly_rate)}</span>
                <span class="mentor-price-label">per hour</span>
              </div>
              <a href="mentor-profile.html?id=${m.id}" class="btn btn-primary btn-sm">
                View Profile
              </a>
            </div>
          </div>
        </div>
      `;
    });

    container.innerHTML = html;
  } catch (err) {
    console.error("Error loading mentors", err);
    UI.renderError(container, "Unable to load mentors at this time.", () => loadRecommendedMentors());
  }
}

/**
 * Load Recent Notifications
 */
async function loadRecentNotifications() {
  const container = document.getElementById("recent-notifications-container");
  if (!container) return;

  try {
    const data = await api.notifications.list(false, 3);
    const notifications = data.notifications || [];

    if (notifications.length === 0) {
      container.innerHTML = `
        <div class="text-center py-4 text-muted small">
          <i class="bi bi-bell-slash fs-3 d-block mb-2 text-secondary"></i>
          No recent notifications
        </div>
      `;
      return;
    }

    let html = "";
    notifications.forEach(n => {
      const typeIcons = {
        booking: "bi-calendar-event notification-icon-booking",
        message: "bi-chat-dots notification-icon-message",
        payment: "bi-credit-card notification-icon-payment",
        system: "bi-info-circle notification-icon-system"
      };
      const iconClass = typeIcons[n.notification_type] || "bi-bell notification-icon-system";

      html += `
        <div class="notification-item ${n.is_read ? '' : 'unread'}">
          <div class="notification-icon-wrap ${iconClass.split(' ')[1]}">
            <i class="bi ${iconClass.split(' ')[0]}"></i>
          </div>
          <div class="flex-grow-1 min-w-0">
            <div class="d-flex justify-content-between align-items-center mb-1">
              <h6 class="fw-bold text-dark fs-6 mb-0">${Utils.escapeHtml(n.title)}</h6>
              <span class="text-muted" style="font-size: 0.7rem;">${Utils.formatRelativeTime(n.created_at)}</span>
            </div>
            <p class="text-secondary small mb-0 text-truncate">${Utils.escapeHtml(n.message)}</p>
          </div>
        </div>
      `;
    });

    container.innerHTML = html;
  } catch (err) {
    console.error("Error loading notifications", err);
  }
}
