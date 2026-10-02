/**
 * Pathzeo - Global Configuration & State
 * Centralized configuration replaceable in production without modifying logic files.
 */

const configuredApiUrl = (window.APP_CONFIG && window.APP_CONFIG.API_BASE_URL) || window.PATHZEO_API_URL || "";
const isLocalDev = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
const buildApiUrl = "__PATHZEO_API_URL__";
const deployedApiUrl = buildApiUrl.startsWith("__") ? "" : buildApiUrl;
const defaultApiUrl = (configuredApiUrl || deployedApiUrl || (isLocalDev ? "http://localhost:8000" : ""))
  .replace(/\/+$/, "");

window.APP_CONFIG = {
  ...(window.APP_CONFIG || {}),
  API_BASE_URL: defaultApiUrl
};

if (!defaultApiUrl) {
  console.error("Pathzeo API URL is not configured for this deployment.");
}

document.querySelectorAll("[data-api-base-url]").forEach((element) => {
  if (element instanceof HTMLInputElement) {
    element.value = defaultApiUrl || "Not configured";
  } else {
    element.textContent = defaultApiUrl || "Not configured";
  }
});

/**
 * Feature Flags - Aligning with available backend endpoints vs roadmap
 */
window.FEATURES = window.FEATURES || {
  AI: false,
  AI_MENTOR_MATCHING: false,
  AI_CAREER_ADVISOR: false,
  RESUME_ANALYSIS: false,
  GOOGLE_AUTH: false,
  LINKEDIN_AUTH: false,
  WEBSOCKET_CHAT: false,
  ADVANCED_SEARCH: false,
  ADMIN_ANALYTICS: false,
  WALLET: false
};

/**
 * Lightweight Global Application State
 */
window.AppState = {
  user: null,
  accessToken: null,
  currentPage: null,
  notifications: [],
  unreadNotificationsCount: 0,
  unreadMessagesCount: 0,
  loading: {}
};
