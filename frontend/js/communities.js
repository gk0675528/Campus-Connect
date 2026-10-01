/**
 * CampusConnect - Communities & Discussions Controller
 */

let currentCommunityId = null;

document.addEventListener("DOMContentLoaded", async () => {
  const isAuth = await Auth.requireAuth();
  if (!isAuth) return;
  await Auth.initGlobalNav();

  const isDetailPage = window.location.pathname.includes("community.html");

  if (isDetailPage) {
    initCommunityDetailPage();
  } else {
    initCommunitiesListPage();
  }
});

/**
 * =========================================================================
 * COMMUNITIES LIST PAGE (communities.html)
 * =========================================================================
 */
function initCommunitiesListPage() {
  const createBtn = document.getElementById("open-create-community-btn");
  if (createBtn) {
    createBtn.addEventListener("click", openCreateCommunityModal);
  }

  loadCommunities();
}

async function loadCommunities() {
  const container = document.getElementById("communities-grid-container");
  if (!container) return;

  // Since backend creates and gets single community, we provide a clean interface
  // with default community cards or create action
  const defaultCommunities = [
    {
      id: "ai-ml-hub",
      name: "AI & Machine Learning Club",
      description: "Discussion on deep learning, generative AI, LLM research papers, and Kaggle competitions.",
      community_type: "academic",
      members_count: 142,
      posts_count: 38
    },
    {
      id: "faang-prep",
      name: "DSA & System Design Mastery",
      description: "Collaborative mock interviews, LeetCode daily solutions, and architecture breakdown.",
      community_type: "career",
      members_count: 289,
      posts_count: 94
    },
    {
      id: "research-scholars",
      name: "Research Scholars & Publications",
      description: "Guidance on writing conference papers (IEEE, ACM, NeurIPS), grants, and PhD admissions.",
      community_type: "research",
      members_count: 85,
      posts_count: 21
    }
  ];

  let html = "";
  defaultCommunities.forEach(c => {
    html += `
      <div class="col-md-6 col-lg-4 mb-4">
        <div class="community-card">
          <div class="community-thumb">
            <i class="bi bi-mortarboard"></i>
          </div>
          <div class="community-body">
            <div class="d-flex justify-content-between align-items-start mb-2">
              <h5 class="community-name">${Utils.escapeHtml(c.name)}</h5>
              <span class="badge bg-primary-light text-primary small">${Utils.escapeHtml(c.community_type)}</span>
            </div>
            <p class="text-secondary small mb-3">${Utils.escapeHtml(c.description)}</p>

            <div class="community-meta">
              <span><i class="bi bi-people me-1"></i>${c.members_count} Members</span>
              <span><i class="bi bi-chat-left-text me-1"></i>${c.posts_count} Posts</span>
              <a href="community.html?id=${c.id}" class="btn btn-outline-primary btn-sm ms-auto">
                Explore
              </a>
            </div>
          </div>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

/**
 * Create Community Modal (Calling POST /api/communities/)
 */
function openCreateCommunityModal() {
  let modalEl = document.getElementById("cc-create-community-modal");
  if (!modalEl) {
    modalEl = document.createElement("div");
    modalEl.id = "cc-create-community-modal";
    modalEl.className = "modal fade";
    modalEl.tabIndex = -1;
    document.body.appendChild(modalEl);
  }

  modalEl.innerHTML = `
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content border-0 shadow-lg" style="border-radius: var(--radius-lg);">
        <div class="modal-header border-bottom">
          <h5 class="modal-title font-heading fw-bold">
            <i class="bi bi-plus-circle text-primary me-2"></i>Create Campus Community
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <form id="create-community-form">
          <div class="modal-body p-4">
            <div class="mb-3">
              <label class="form-label" for="comm-name">Community Name <span class="text-danger">*</span></label>
              <input type="text" class="form-control" id="comm-name" placeholder="e.g. Cloud Computing & DevOps Circle" required>
            </div>

            <div class="mb-3">
              <label class="form-label" for="comm-type">Category</label>
              <select class="form-select" id="comm-type">
                <option value="academic" selected>Academic & Study</option>
                <option value="career">Career & Placement</option>
                <option value="research">Research & Innovation</option>
                <option value="alumni">Alumni Network</option>
              </select>
            </div>

            <div class="mb-3">
              <label class="form-label" for="comm-desc">Description <span class="text-danger">*</span></label>
              <textarea class="form-control" id="comm-desc" rows="3" placeholder="Explain the focus, rules, and discussion topics for this community..." required></textarea>
            </div>
          </div>
          <div class="modal-footer border-top bg-light">
            <button type="button" class="btn btn-outline-secondary btn-sm" data-bs-dismiss="modal">Cancel</button>
            <button type="submit" class="btn btn-primary btn-sm" id="submit-comm-btn">
              Create Community
            </button>
          </div>
        </form>
      </div>
    </div>
  `;

  const bsModal = new bootstrap.Modal(modalEl);
  bsModal.show();

  const form = modalEl.querySelector("#create-community-form");
  const submitBtn = modalEl.querySelector("#submit-comm-btn");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = modalEl.querySelector("#comm-name").value.trim();
    const communityType = modalEl.querySelector("#comm-type").value;
    const description = modalEl.querySelector("#comm-desc").value.trim();

    if (!name || !description) {
      UI.toast({ type: "warning", title: "Missing Fields", message: "Please fill in community name and description." });
      return;
    }

    UI.setLoading(submitBtn, true, "Creating...");

    try {
      const created = await api.communities.create({
        name,
        description,
        community_type: communityType
      });

      UI.setLoading(submitBtn, false);
      bsModal.hide();

      UI.toast({
        type: "success",
        title: "Community Created",
        message: `"${name}" community is now live!`
      });

      setTimeout(() => {
        window.location.href = `community.html?id=${created.id}`;
      }, 1000);
    } catch (err) {
      UI.setLoading(submitBtn, false);
      UI.toast({
        type: "error",
        title: "Creation Failed",
        message: err.message || "Failed to create community."
      });
    }
  });
}

/**
 * =========================================================================
 * SINGLE COMMUNITY DETAIL & POSTS FEED (community.html)
 * =========================================================================
 */
async function initCommunityDetailPage() {
  const communityId = Utils.getParam("id");
  currentCommunityId = communityId;

  if (!communityId) {
    window.location.href = "communities.html";
    return;
  }

  // Load Community Details
  loadCommunityDetails(communityId);
  // Load Community Posts
  loadCommunityPosts(communityId);

  // Post Submission Form Handler
  const postForm = document.getElementById("create-post-form");
  if (postForm) {
    postForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const title = document.getElementById("post-title-input").value.trim();
      const content = document.getElementById("post-content-input").value.trim();

      if (!title || !content) {
        UI.toast({ type: "warning", title: "Missing Content", message: "Please enter both a title and content." });
        return;
      }

      const submitBtn = document.getElementById("submit-post-btn");
      UI.setLoading(submitBtn, true, "Publishing...");

      try {
        await api.communities.createPost(communityId, { title, content });
        document.getElementById("post-title-input").value = "";
        document.getElementById("post-content-input").value = "";
        UI.setLoading(submitBtn, false);

        UI.toast({
          type: "success",
          title: "Post Published",
          message: "Your post is now visible to community members."
        });

        loadCommunityPosts(communityId);
      } catch (err) {
        UI.setLoading(submitBtn, false);
        UI.toast({
          type: "error",
          title: "Post Failed",
          message: err.message || "Could not publish post."
        });
      }
    });
  }
}

async function loadCommunityDetails(communityId) {
  const headerContainer = document.getElementById("community-header-container");
  if (!headerContainer) return;

  try {
    const comm = await api.communities.get(communityId);
    headerContainer.innerHTML = `
      <div class="cc-card mb-4 bg-gradient p-4">
        <div class="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3">
          <div>
            <span class="badge bg-primary text-white mb-2 text-uppercase">${Utils.escapeHtml(comm.community_type || 'Academic')}</span>
            <h2 class="font-heading fw-bold text-dark mb-1">${Utils.escapeHtml(comm.name)}</h2>
            <p class="text-secondary mb-0">${Utils.escapeHtml(comm.description)}</p>
          </div>
          <div class="d-flex align-items-center gap-2">
            <button type="button" class="btn btn-outline-primary" id="join-community-btn">
              <i class="bi bi-person-plus me-1"></i> Join Community
            </button>
          </div>
        </div>
      </div>
    `;

    document.getElementById("join-community-btn")?.addEventListener("click", async () => {
      try {
        await api.communities.join(communityId);
        UI.toast({ type: "success", title: "Joined!", message: "You are now a member of this community." });
      } catch (err) {
        UI.toast({ type: "error", title: "Join Failed", message: err.message || "Could not join." });
      }
    });
  } catch (err) {
    // If id is a demo string or not found, show friendly header
    headerContainer.innerHTML = `
      <div class="cc-card mb-4 p-4">
        <div class="d-flex justify-content-between align-items-center">
          <div>
            <h2 class="font-heading fw-bold text-dark mb-1">Campus Discussion Community</h2>
            <p class="text-secondary mb-0">Collaborate with peers, ask academic doubts, and share research insights.</p>
          </div>
        </div>
      </div>
    `;
  }
}

async function loadCommunityPosts(communityId) {
  const container = document.getElementById("community-posts-container");
  if (!container) return;

  container.innerHTML = UI.createSkeleton("list", 3);

  try {
    const posts = await api.communities.posts(communityId);

    if (!posts || posts.length === 0) {
      UI.renderEmptyState(container, {
        icon: "bi-chat-square-text",
        title: "No discussions yet",
        description: "Be the first to start a conversation in this community!",
        actionText: "Write a Post",
        actionCallback: () => {
          document.getElementById("post-title-input")?.focus();
        }
      });
      return;
    }

    let html = "";
    posts.forEach(p => {
      html += `
        <div class="post-card">
          <div class="post-header">
            <div class="post-author-avatar"><i class="bi bi-person-fill"></i></div>
            <div>
              <h6 class="post-author-name">Community Member</h6>
              <span class="post-time">${Utils.formatRelativeTime(p.created_at)}</span>
            </div>
          </div>
          <h5 class="post-title">${Utils.escapeHtml(p.title)}</h5>
          <p class="post-content">${Utils.escapeHtml(p.content)}</p>
          <div class="post-actions">
            <span><i class="bi bi-arrow-up-circle me-1"></i> ${p.upvote_count || 0} Upvotes</span>
            <span><i class="bi bi-chat-dots me-1"></i> ${p.comment_count || 0} Comments</span>
          </div>
        </div>
      `;
    });

    container.innerHTML = html;
  } catch (err) {
    console.error("Error loading posts", err);
    UI.renderEmptyState(container, {
      icon: "bi-chat-square-text",
      title: "Start the discussion",
      description: "Ask a question, share a project, or request mentorship guidance.",
      actionText: "Create Post",
      actionCallback: () => {
        document.getElementById("post-title-input")?.focus();
      }
    });
  }
}
