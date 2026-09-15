/**
 * CampusConnect - Direct Messaging Controller
 * Supports 1-on-1 conversations and contact safety warnings.
 */

let activeReceiverId = null;
let activeReceiverName = "Mentor / Student";

document.addEventListener("DOMContentLoaded", async () => {
  const isAuth = await Auth.requireAuth();
  if (!isAuth) return;
  await Auth.initGlobalNav();

  initMessaging();
});

async function initMessaging() {
  const targetUserId = Utils.getParam("user");
  const conversationsContainer = document.getElementById("conversations-list");
  const chatForm = document.getElementById("chat-send-form");
  const messageInput = document.getElementById("chat-message-input");

  // If user parameter is passed in URL, set as active
  if (targetUserId) {
    activeReceiverId = targetUserId;
  }

  // Load active conversation if target ID is present
  if (activeReceiverId) {
    loadConversation(activeReceiverId);
  } else {
    // Check recent notifications for message senders
    loadRecentChatUsers();
  }

  // Send message submission
  if (chatForm && messageInput) {
    chatForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const content = messageInput.value.trim();
      if (!content) return;

      if (!activeReceiverId) {
        UI.toast({
          type: "warning",
          title: "Select Contact",
          message: "Please select a user from the left list or mentor profile to chat."
        });
        return;
      }

      // Check PRD Section 26: Chat Security Warning for contact sharing
      const phoneOrEmailRegex = /(\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b|\b\d{10}\b|\b\+?\d{1,3}[- ]?\d{10}\b|telegram|whatsapp|discord)/i;
      if (phoneOrEmailRegex.test(content)) {
        UI.toast({
          type: "warning",
          title: "Policy Reminder",
          message: "Platform policy prohibits sharing personal contact numbers, emails, or external handles. Backend moderation applies."
        });
      }

      const sendBtn = document.getElementById("chat-send-btn");
      UI.setLoading(sendBtn, true, "");

      try {
        await api.messages.send(activeReceiverId, content);
        messageInput.value = "";
        UI.setLoading(sendBtn, false);

        // Reload conversation messages
        await loadConversation(activeReceiverId);
      } catch (err) {
        UI.setLoading(sendBtn, false);
        console.error("Message send failed", err);
        UI.toast({
          type: "error",
          title: "Message Failed",
          message: err.message || "Unable to send message."
        });
      }
    });
  }
}

/**
 * Load Conversation messages with a specific user
 */
async function loadConversation(userId) {
  const messagesArea = document.getElementById("chat-messages-area");
  const chatHeaderName = document.getElementById("chat-active-name");
  const chatInputContainer = document.getElementById("chat-input-container");
  if (!messagesArea) return;

  activeReceiverId = userId;
  if (chatHeaderName) {
    chatHeaderName.textContent = activeReceiverName;
  }
  if (chatInputContainer) {
    chatInputContainer.style.display = "block";
  }

  try {
    const data = await api.messages.conversation(userId);
    const messages = data.messages || [];

    const currentUser = Auth.getCurrentUser();
    const currentUserId = currentUser ? currentUser.id : null;

    if (messages.length === 0) {
      messagesArea.innerHTML = `
        <div class="text-center py-5 text-muted my-auto">
          <i class="bi bi-chat-quote fs-1 d-block mb-2 text-primary opacity-50"></i>
          <h6 class="fw-bold text-dark">Start a conversation</h6>
          <p class="small mb-0">Ask questions, share goals, and coordinate session timings.</p>
        </div>
      `;
      return;
    }

    let html = "";
    // Note: Backend returns messages ordered by created_at desc, so we reverse for chat thread
    const chronMessages = [...messages].reverse();

    chronMessages.forEach(msg => {
      const isSentByMe = (currentUserId && msg.sender_id === currentUserId);
      html += `
        <div class="message-bubble ${isSentByMe ? 'sent' : 'received'}">
          ${Utils.escapeHtml(msg.content)}
          <span class="message-time">${Utils.formatTime(msg.created_at)}</span>
        </div>
      `;

      // Auto mark read if received and unread
      if (!isSentByMe && !msg.is_read) {
        api.messages.markRead(msg.id).catch(e => console.warn("Failed to mark message read", e));
      }
    });

    messagesArea.innerHTML = html;
    // Scroll to bottom
    messagesArea.scrollTop = messagesArea.scrollHeight;
  } catch (err) {
    console.error("Error loading conversation", err);
    messagesArea.innerHTML = `
      <div class="alert alert-danger m-3 small">
        <i class="bi bi-exclamation-triangle me-1"></i> ${Utils.escapeHtml(err.message || "Failed to load messages.")}
      </div>
    `;
  }
}

/**
 * Load recent contacts / notification senders
 */
async function loadRecentChatUsers() {
  const container = document.getElementById("conversations-list");
  const messagesArea = document.getElementById("chat-messages-area");
  if (!container) return;

  try {
    // If target userId not specified, display an initial helper screen in chat area
    if (messagesArea && !activeReceiverId) {
      messagesArea.innerHTML = `
        <div class="text-center py-5 text-muted my-auto">
          <i class="bi bi-chat-left-dots fs-1 d-block mb-2 text-secondary opacity-50"></i>
          <h6 class="fw-bold text-dark">No Chat Selected</h6>
          <p class="small mb-3">Choose a mentor from the marketplace or start a conversation.</p>
          <a href="mentors.html" class="btn btn-primary btn-sm">Find Mentors to Chat</a>
        </div>
      `;
      const chatInputContainer = document.getElementById("chat-input-container");
      if (chatInputContainer) chatInputContainer.style.display = "none";
    }
  } catch (err) {
    console.error("Error loading chat users", err);
  }
}
