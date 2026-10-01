/**
 * CampusConnect - Authentication & Session Management
 */

const Auth = {
  TOKEN_KEY: "cc_access_token",
  REFRESH_TOKEN_KEY: "cc_refresh_token",
  USER_KEY: "cc_current_user",

  /**
   * Save session tokens and user data
   */
  login(tokenData, userData = null) {
    if (tokenData && tokenData.access_token) {
      localStorage.setItem(this.TOKEN_KEY, tokenData.access_token);
      if (tokenData.refresh_token) {
        localStorage.setItem(this.REFRESH_TOKEN_KEY, tokenData.refresh_token);
      }
    }
    if (userData) {
      localStorage.setItem(this.USER_KEY, JSON.stringify(userData));
      window.AppState.user = userData;
    }
  },

  /**
   * Clear session
   */
  logout(redirect = true) {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    window.AppState.user = null;
    window.AppState.accessToken = null;

    if (redirect) {
      window.location.href = "login.html";
    }
  },

  /**
   * Retrieve access token
   */
  getAccessToken() {
    return localStorage.getItem(this.TOKEN_KEY);
  },

  /**
   * Retrieve refresh token
   */
  getRefreshToken() {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    return !!this.getAccessToken();
  },

  /**
   * Get cached current user
   */
  getCurrentUser() {
    if (window.AppState.user) return window.AppState.user;
    const stored = localStorage.getItem(this.USER_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        window.AppState.user = parsed;
        return parsed;
      } catch (e) {
        console.error("Failed to parse stored user", e);
      }
    }
    return null;
  },

  /**
   * Fetch authenticated user profile from backend
   */
  async fetchCurrentUser() {
    if (!this.isAuthenticated()) return null;
    try {
      const user = await api.auth.me();
      localStorage.setItem(this.USER_KEY, JSON.stringify(user));
      window.AppState.user = user;
      return user;
    } catch (err) {
      console.warn("Could not fetch current user profile", err);
      return null;
    }
  },

  /**
   * Auth Guard - Protects pages
   */
  async requireAuth(redirectIfNotAuth = true) {
    if (!this.isAuthenticated()) {
      if (redirectIfNotAuth) {
        const returnUrl = encodeURIComponent(window.location.pathname + window.location.search);
        window.location.href = `login.html?return_url=${returnUrl}`;
      }
      return false;
    }

    // Refresh user state from backend
    let user = this.getCurrentUser();
    if (!user) {
      user = await this.fetchCurrentUser();
    }
    return true;
  },

  /**
   * Redirect user based on role after login
   */
  redirectByRole(user) {
    if (!user) {
      window.location.href = "dashboard.html";
      return;
    }
    if (user.role === "admin") {
      window.location.href = "admin-dashboard.html";
    } else if (user.is_mentor) {
      window.location.href = "dashboard.html";
    } else {
      window.location.href = "dashboard.html";
    }
  },

  /**
   * Initialize Global Navigation (Sidebar, Topbar, Badges, Profile Cards)
   */
  async initGlobalNav() {
    const user = this.getCurrentUser() || await this.fetchCurrentUser();

    // Populate user elements dynamically
    if (user) {
      const fullName = `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.username || "User";
      const initials = Utils.getInitials(user.first_name || user.username, user.last_name || "");
      const roleName = user.role ? (user.role.charAt(0).toUpperCase() + user.role.slice(1)) : (user.is_mentor ? "Mentor" : "Student");

      // Sidebar elements
      document.querySelectorAll(".sidebar-user-name, #sidebar-user-name").forEach(el => el.textContent = fullName);
      document.querySelectorAll(".sidebar-user-role, #sidebar-user-role").forEach(el => el.textContent = roleName);
      document.querySelectorAll(".sidebar-user-avatar, #sidebar-user-avatar").forEach(el => el.textContent = initials);

      // Topbar elements
      document.querySelectorAll(".topbar-user-name, #topbar-user-name").forEach(el => el.textContent = fullName);
      document.querySelectorAll(".topbar-user-avatar, #topbar-user-avatar").forEach(el => el.textContent = initials);

      // Mentor navigation adjustments
      const mentorLink = document.getElementById("nav-mentor-dashboard");
      if (mentorLink) {
        if (user.is_mentor) {
          mentorLink.style.display = "flex";
        } else {
          // If not mentor, change text to "Become a Mentor"
          mentorLink.innerHTML = `<i class="bi bi-award"></i><span>Become a Mentor</span>`;
          mentorLink.href = "mentor-dashboard.html?action=onboard";
        }
      }

      // Admin navigation adjustments
      const adminLink = document.getElementById("nav-admin-dashboard");
      if (adminLink) {
        adminLink.style.display = (user.role === "admin") ? "flex" : "none";
      }
    }

    // Setup Mobile Sidebar Toggle
    const toggleBtn = document.getElementById("sidebar-toggle-btn");
    const sidebar = document.querySelector(".app-sidebar");
    let backdrop = document.querySelector(".sidebar-backdrop");

    if (!backdrop) {
      backdrop = document.createElement("div");
      backdrop.className = "sidebar-backdrop";
      document.body.appendChild(backdrop);
    }

    if (toggleBtn && sidebar) {
      toggleBtn.addEventListener("click", () => {
        sidebar.classList.toggle("show");
        backdrop.classList.toggle("show");
      });

      backdrop.addEventListener("click", () => {
        sidebar.classList.remove("show");
        backdrop.classList.remove("show");
      });
    }

    // Setup Logout Handler
    document.querySelectorAll(".logout-btn, #nav-logout-btn").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        UI.showConfirmModal({
          title: "Sign Out",
          message: "Are you sure you want to sign out of CampusConnect?",
          confirmText: "Sign Out",
          confirmClass: "btn-primary",
          onConfirm: () => {
            Auth.logout(true);
          }
        });
      });
    });

    // Fetch Unread Notifications Count for Topbar Badge
    if (this.isAuthenticated()) {
      try {
        const notifData = await api.notifications.list(true, 5);
        const count = notifData.count || (notifData.notifications ? notifData.notifications.length : 0);
        const notifBadge = document.getElementById("topbar-notif-badge");
        if (notifBadge) {
          if (count > 0) {
            notifBadge.textContent = count > 9 ? "9+" : count;
            notifBadge.style.display = "flex";
          } else {
            notifBadge.style.display = "none";
          }
        }
      } catch (e) {
        // Notification count fetch is non-blocking
      }
    }
  }
};
