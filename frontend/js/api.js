/**
 * CampusConnect - Centralized API Client & Services
 * Integrates directly with FastAPI Backend.
 */

const API_BASE_URL = (window.APP_CONFIG && window.APP_CONFIG.API_BASE_URL) || "http://localhost:8000";

class ApiClient {
  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  /**
   * Core HTTP Request Dispatcher
   */
  async request(endpoint, options = {}) {
    const url = endpoint.startsWith("http") ? endpoint : `${this.baseUrl}${endpoint}`;
    const headers = {
      "Accept": "application/json",
      ...(options.headers || {})
    };

    // Attach Bearer token if available
    const token = typeof Auth !== "undefined" ? Auth.getAccessToken() : localStorage.getItem("cc_access_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    // JSON Body serialization
    let body = options.body;
    if (body && typeof body === "object" && !(body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(body);
    }

    const config = {
      ...options,
      headers,
      body
    };

    try {
      const response = await fetch(url, config);

      // Handle 401 Unauthorized (Expired / Invalid session)
      if (response.status === 401) {
        const isAuthPage = window.location.pathname.includes("login.html") || 
                           window.location.pathname.includes("register.html") ||
                           window.location.pathname.includes("index.html");
        
        if (!isAuthPage && typeof Auth !== "undefined") {
          Auth.logout(false);
          window.location.href = "login.html?session=expired";
          return Promise.reject(new Error("Your session has expired. Please sign in again."));
        }
      }

      // Parse JSON or text response
      let data;
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        data = await response.json();
      } else {
        data = await response.text();
      }

      // Check HTTP Success
      if (!response.ok) {
        let errorMessage = "An unexpected error occurred.";
        
        if (data && typeof data === "object") {
          if (typeof data.detail === "string") {
            errorMessage = data.detail;
          } else if (Array.isArray(data.detail)) {
            // FastAPI Pydantic Validation Errors
            errorMessage = data.detail.map(err => `${err.loc ? err.loc.join('.') + ': ' : ''}${err.msg}`).join(", ");
          } else if (data.message) {
            errorMessage = data.message;
          }
        } else if (typeof data === "string" && data.trim()) {
          errorMessage = data;
        }

        // Status code specific fallback messages
        if (response.status === 403) errorMessage = errorMessage || "You do not have permission to perform this action.";
        if (response.status === 404) errorMessage = errorMessage || "The requested resource was not found.";
        if (response.status === 409) errorMessage = errorMessage || "Conflict occurred. This record may already exist.";
        if (response.status === 429) errorMessage = "Too many requests. Please wait a moment before trying again.";
        if (response.status >= 500) errorMessage = "Server error. Please try again later.";

        const error = new Error(errorMessage);
        error.status = response.status;
        error.data = data;
        throw error;
      }

      return data;
    } catch (err) {
      if (err.name === "TypeError" && err.message.includes("Failed to fetch")) {
        throw new Error("Unable to connect to CampusConnect server. Please ensure the backend is running at " + this.baseUrl);
      }
      throw err;
    }
  }

  // HTTP Shorthands
  get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: "GET" });
  }

  post(endpoint, body, options = {}) {
    return this.request(endpoint, { ...options, method: "POST", body });
  }

  put(endpoint, body, options = {}) {
    return this.request(endpoint, { ...options, method: "PUT", body });
  }

  patch(endpoint, body, options = {}) {
    return this.request(endpoint, { ...options, method: "PATCH", body });
  }

  delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: "DELETE" });
  }
}

// Global API Client Instance
const API = new ApiClient();

/**
 * Domain-Specific API Services
 */
const api = {
  // Authentication Endpoints
  auth: {
    login: (email, password) => API.post("/api/auth/login", { email, password }),
    register: (userData) => API.post("/api/auth/register", userData),
    me: () => API.get("/api/auth/me"),
    requestPasswordReset: (email) => API.post("/api/auth/forgot-password", { email }),
    verifyPasswordReset: (email, otp) => API.post("/api/auth/forgot-password/verify", { email, otp }),
    resetPassword: (email, otp, newPassword) => API.post("/api/auth/forgot-password/reset", {
      email,
      otp,
      new_password: newPassword
    })
  },

  // Mentorship Endpoints
  mentors: {
    search: (skills = [], limit = 20) => {
      const params = new URLSearchParams();
      if (Array.isArray(skills) && skills.length > 0) {
        skills.forEach(s => params.append("skills", s));
      }
      if (limit) params.append("limit", limit);
      const queryString = params.toString();
      return API.get(`/api/mentors/search${queryString ? '?' + queryString : ''}`);
    },
    get: (mentorId) => API.get(`/api/mentors/${mentorId}`),
    becomeMentor: (profileData) => API.post("/api/mentors/become-mentor", profileData),
    calculateCost: (mentorId, durationMinutes = 60) => 
      API.post(`/api/mentors/calculate-cost?mentor_id=${encodeURIComponent(mentorId)}&duration_minutes=${encodeURIComponent(durationMinutes)}`)
  },

  // Booking Endpoints
  bookings: {
    create: (bookingData) => API.post("/api/bookings/", bookingData),
    get: (sessionId) => API.get(`/api/bookings/${sessionId}`),
    cancel: (sessionId) => API.post(`/api/bookings/${sessionId}/cancel`),
    feedback: (sessionId, rating, review) => API.post(`/api/bookings/${sessionId}/feedback`, { rating, review })
  },

  // Community Endpoints
  communities: {
    create: (communityData) => API.post("/api/communities/", communityData),
    get: (communityId) => API.get(`/api/communities/${communityId}`),
    join: (communityId) => API.post(`/api/communities/${communityId}/join`),
    createPost: (communityId, postData) => API.post(`/api/communities/${communityId}/posts`, postData),
    posts: (communityId, limit = 20) => API.get(`/api/communities/${communityId}/posts?limit=${limit}`)
  },

  // Messaging Endpoints
  messages: {
    send: (receiverId, content) => API.post("/api/messages/send", { receiver_id: receiverId, content }),
    conversation: (userId) => API.get(`/api/messages/conversation/${userId}`),
    markRead: (messageId) => API.post(`/api/messages/mark-read/${messageId}`)
  },

  // Payment Endpoints
  payments: {
    create: (sessionId, paymentMethod = "razorpay") => API.post("/api/payments/create", { session_id: sessionId, payment_method: paymentMethod }),
    confirm: (paymentId, transactionId) => API.post(`/api/payments/confirm/${paymentId}?transaction_id=${encodeURIComponent(transactionId)}`)
  },

  // Notification Endpoints
  notifications: {
    list: (unreadOnly = false, limit = 20) => API.get(`/api/notifications/?unread_only=${unreadOnly}&limit=${limit}`),
    markRead: (notificationId) => API.post(`/api/notifications/${notificationId}/read`)
  }
};
