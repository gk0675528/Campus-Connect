/**
 * Pathzeo - Admin Dashboard Controller
 */

document.addEventListener("DOMContentLoaded", async () => {
  const isAuth = await Auth.requireAuth();
  if (!isAuth) return;
  await Auth.initGlobalNav();

  initAdminDashboard();
});

async function initAdminDashboard() {
  const healthStatusEl = document.getElementById("admin-health-status");
  const apiVersionEl = document.getElementById("admin-api-version");
  const baseUrlEl = document.getElementById("admin-api-base-url");

  if (baseUrlEl) baseUrlEl.textContent = API.baseUrl || "Not configured";

  // Check Backend Health
  try {
    const health = await API.get("/health");
    if (healthStatusEl) {
      healthStatusEl.className = "badge bg-success";
      healthStatusEl.innerHTML = `<i class="bi bi-check-circle-fill me-1"></i>${health.status.toUpperCase()}`;
    }
    if (apiVersionEl) apiVersionEl.textContent = `v${health.version || '1.0.0'}`;
  } catch (err) {
    if (healthStatusEl) {
      healthStatusEl.className = "badge bg-danger";
      healthStatusEl.innerHTML = `<i class="bi bi-x-circle-fill me-1"></i>DISCONNECTED`;
    }
  }
}
