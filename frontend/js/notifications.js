/**
 * CampusConnect - Notifications Controller
 */

let currentFilterUnreadOnly = false;

document.addEventListener("DOMContentLoaded", async () => {
  const isAuth = await Auth.requireAuth();
  if (!isAuth) return;
  await Auth.initGlobalNav();

  initNotificationsPage();
});

function initNotificationsPage() {
  const filterTabs = document.querySelectorAll(".notif-filter-tab");
  filterTabs.forEach(tab => {
    tab.addEventListener("click", (e) => {
      e.preventDefault();
      filterTabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      currentFilterUnreadOnly = tab.dataset.filter === "unread";
      loadNotifications();
    });
  });

  loadNotifications();
}

async function loadNotifications() {
  const container = document.getElementById("notifications-list-container");
  if (!container) return;

  container.innerHTML = UI.createSkeleton("list", 4);

  try {
    const data = await api.notifications.list(currentFilterUnreadOnly, 50);
    const list = data.notifications || [];

    if (list.length === 0) {
      UI.renderEmptyState(container, {
        icon: "bi-bell-slash",
        title: currentFilterUnreadOnly ? "No unread notifications" : "No notifications yet",
        description: "You are all caught up! Updates regarding bookings, messages, and communities will appear here."
      });
      return;
    }

    let html = "";
    list.forEach(n => {
      const typeIcons = {
        booking: "bi-calendar-check notification-icon-booking",
        session: "bi-camera-video notification-icon-booking",
        message: "bi-chat-dots notification-icon-message",
        payment: "bi-credit-card notification-icon-payment",
        system: "bi-info-circle notification-icon-system",
        community: "bi-people notification-icon-booking"
      };
      const iconClass = typeIcons[n.notification_type] || "bi-bell notification-icon-system";

      html += `
        <div class="notification-item ${n.is_read ? '' : 'unread'} d-flex align-items-center justify-content-between" data-id="${n.id}">
          <div class="d-flex align-items-start gap-3 flex-grow-1 min-w-0">
            <div class="notification-icon-wrap ${iconClass.split(' ')[1]}">
              <i class="bi ${iconClass.split(' ')[0]}"></i>
            </div>
            <div class="flex-grow-1 min-w-0">
              <div class="d-flex align-items-center justify-content-between mb-1">
                <h6 class="fw-bold text-dark fs-6 mb-0">${Utils.escapeHtml(n.title)}</h6>
                <span class="text-muted" style="font-size: 0.75rem;">${Utils.formatRelativeTime(n.created_at)}</span>
              </div>
              <p class="text-secondary small mb-0">${Utils.escapeHtml(n.message)}</p>
            </div>
          </div>
          ${!n.is_read ? `
            <button type="button" class="btn btn-sm btn-outline-secondary mark-read-btn ms-3 flex-shrink-0" data-id="${n.id}" title="Mark as Read">
              <i class="bi bi-check2"></i>
            </button>
          ` : ''}
        </div>
      `;
    });

    container.innerHTML = html;

    // Attach Mark Read Handlers
    container.querySelectorAll(".mark-read-btn").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const notifId = btn.dataset.id;
        try {
          await api.notifications.markRead(notifId);
          btn.closest(".notification-item")?.classList.remove("unread");
          btn.remove();
          UI.toast({ type: "success", title: "Marked Read", message: "Notification updated." });
        } catch (err) {
          console.error("Failed to mark read", err);
        }
      });
    });
  } catch (err) {
    console.error("Error loading notifications", err);
    UI.renderError(container, "Unable to load notifications.", () => loadNotifications());
  }
}
