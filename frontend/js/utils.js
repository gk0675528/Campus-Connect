/**
 * CampusConnect - Utility Helper Functions
 */

const Utils = {
  /**
   * Format currency (INR)
   */
  formatCurrency(amount) {
    if (amount === undefined || amount === null || isNaN(amount)) return "₹0";
    if (amount === 0) return "Free";
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0
    }).format(amount);
  },

  /**
   * Format full readable date (e.g. 25 Aug 2026)
   */
  formatDate(dateString) {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    return date.toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric"
    });
  },

  /**
   * Format time (e.g. 03:30 PM)
   */
  formatTime(dateString) {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return "";
    return date.toLocaleTimeString("en-IN", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true
    });
  },

  /**
   * Format relative time (e.g. 5m ago, 2h ago, Yesterday)
   */
  formatRelativeTime(dateString) {
    if (!dateString) return "";
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);

    if (diffInSeconds < 60) return "Just now";
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`;
    return Utils.formatDate(dateString);
  },

  /**
   * Format duration in minutes (e.g. 60 mins -> 1 hour, 45 mins -> 45 mins)
   */
  formatDuration(minutes) {
    if (!minutes) return "0 mins";
    if (minutes === 60) return "1 hour";
    if (minutes % 60 === 0) return `${minutes / 60} hours`;
    return `${minutes} mins`;
  },

  /**
   * Extract initials from first and last name
   */
  getInitials(nameOrFirst, last = "") {
    if (!nameOrFirst) return "U";
    if (last) {
      return `${nameOrFirst.charAt(0)}${last.charAt(0)}`.toUpperCase();
    }
    const parts = nameOrFirst.trim().split(/\s+/);
    if (parts.length >= 2) {
      return `${parts[0].charAt(0)}${parts[1].charAt(0)}`.toUpperCase();
    }
    return parts[0].charAt(0).toUpperCase();
  },

  /**
   * Escape HTML to prevent XSS in dynamic rendering
   */
  escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  },

  /**
   * Get URL query parameter
   */
  getParam(paramName) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(paramName);
  },

  /**
   * Debounce helper
   */
  debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }
};
