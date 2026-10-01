/**
 * CampusConnect - Profile Controller
 */

document.addEventListener("DOMContentLoaded", async () => {
  const isAuth = await Auth.requireAuth();
  if (!isAuth) return;
  await Auth.initGlobalNav();

  loadUserProfile();
});

async function loadUserProfile() {
  const user = Auth.getCurrentUser() || await Auth.fetchCurrentUser();
  if (!user) return;

  const fullName = `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.username;
  const initials = Utils.getInitials(user.first_name || user.username, user.last_name || "");

  // Update Profile DOM Elements
  const avatarEl = document.getElementById("profile-avatar-display");
  const nameEl = document.getElementById("profile-name-display");
  const usernameEl = document.getElementById("profile-username-display");
  const emailEl = document.getElementById("profile-email-display");
  const roleEl = document.getElementById("profile-role-display");
  const createdEl = document.getElementById("profile-created-display");
  const mentorStatusBadge = document.getElementById("profile-mentor-status-badge");

  if (avatarEl) avatarEl.textContent = initials;
  if (nameEl) nameEl.textContent = fullName;
  if (usernameEl) usernameEl.textContent = `@${user.username}`;
  if (emailEl) emailEl.textContent = user.email;
  if (roleEl) roleEl.textContent = user.role ? (user.role.charAt(0).toUpperCase() + user.role.slice(1)) : "Student";
  if (createdEl) createdEl.textContent = Utils.formatDate(user.created_at);

  if (mentorStatusBadge) {
    if (user.is_mentor) {
      mentorStatusBadge.className = "badge bg-success";
      mentorStatusBadge.innerHTML = `<i class="bi bi-patch-check-fill me-1"></i>Active Mentor`;
    } else {
      mentorStatusBadge.className = "badge bg-secondary";
      mentorStatusBadge.textContent = "Student Account";
    }
  }

  // Pre-fill editable form inputs
  const fnameInput = document.getElementById("edit-first-name");
  const lnameInput = document.getElementById("edit-last-name");
  const emailInput = document.getElementById("edit-email");
  const usernameInput = document.getElementById("edit-username");

  if (fnameInput) fnameInput.value = user.first_name || "";
  if (lnameInput) lnameInput.value = user.last_name || "";
  if (emailInput) emailInput.value = user.email || "";
  if (usernameInput) usernameInput.value = user.username || "";
}
