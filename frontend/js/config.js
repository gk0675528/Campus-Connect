/**
 * CampusConnect - Global Configuration & State
 * Centralized configuration replaceable in production without modifying logic files.
 */

const configuredApiUrl = window.APP_CONFIG && window.APP_CONFIG.API_BASE_URL;
const injectedApiUrl = window.CAMPUSCONNECT_API_URL;
const isLocalDev = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
const defaultApiUrl = (isLocalDev && window.location.port !== "8000")
  ? "http://localhost:8000"
  : (window.location.protocol.startsWith("http") ? window.location.origin : "http://localhost:8000");

window.APP_CONFIG = {
  ...(window.APP_CONFIG || {}),
  // Set window.CAMPUSCONNECT_API_URL before this script for a separate API host.
  API_BASE_URL: configuredApiUrl || injectedApiUrl || defaultApiUrl
};

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
