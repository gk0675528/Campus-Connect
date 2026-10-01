/**
 * CampusConnect - Mentor Portal & Onboarding Wizard Controller
 */

let wizardStep = 1;
let onboardingData = {
  hourly_rate: 500,
  expertise: [],
  bio: ""
};

document.addEventListener("DOMContentLoaded", async () => {
  const isAuth = await Auth.requireAuth();
  if (!isAuth) return;
  await Auth.initGlobalNav();

  const user = Auth.getCurrentUser();
  const forceOnboard = Utils.getParam("action") === "onboard";

  if (user && user.is_mentor && !forceOnboard) {
    showMentorDashboardView(user);
  } else {
    showOnboardingWizardView();
  }
});

/**
 * =========================================================================
 * 5-STEP ONBOARDING WIZARD (Calling POST /api/mentors/become-mentor)
 * =========================================================================
 */
function showOnboardingWizardView() {
  const onboardView = document.getElementById("mentor-onboarding-view");
  const dashboardView = document.getElementById("mentor-active-dashboard-view");

  if (onboardView) onboardView.style.display = "block";
  if (dashboardView) dashboardView.style.display = "none";

  initOnboardingWizard();
}

function initOnboardingWizard() {
  wizardStep = 1;
  renderWizardStep();

  // Wizard Next Button
  document.getElementById("wizard-next-btn")?.addEventListener("click", () => {
    if (validateCurrentStep()) {
      if (wizardStep < 5) {
        wizardStep++;
        renderWizardStep();
      } else {
        submitBecomeMentor();
      }
    }
  });

  // Wizard Prev Button
  document.getElementById("wizard-prev-btn")?.addEventListener("click", () => {
    if (wizardStep > 1) {
      wizardStep--;
      renderWizardStep();
    }
  });

  // Wizard Expertise Tag Toggle Delegation
  document.getElementById("wizard-expertise-container")?.addEventListener("click", (e) => {
    const chip = e.target.closest(".wizard-skill-btn");
    if (!chip) return;

    const skill = chip.dataset.skill;
    if (onboardingData.expertise.includes(skill)) {
      onboardingData.expertise = onboardingData.expertise.filter(s => s !== skill);
      chip.classList.remove("active");
    } else {
      onboardingData.expertise.push(skill);
      chip.classList.add("active");
    }
  });
}

function renderWizardStep() {
  // Update step indicators
  for (let i = 1; i <= 5; i++) {
    const stepEl = document.getElementById(`wizard-step-indicator-${i}`);
    const cardEl = document.getElementById(`wizard-step-card-${i}`);
    if (stepEl) {
      stepEl.className = `journey-step ${i === wizardStep ? 'active' : (i < wizardStep ? 'completed' : '')}`;
    }
    if (cardEl) {
      cardEl.style.display = (i === wizardStep) ? "block" : "none";
    }
  }

  // Update Buttons
  const prevBtn = document.getElementById("wizard-prev-btn");
  const nextBtn = document.getElementById("wizard-next-btn");

  if (prevBtn) prevBtn.style.visibility = (wizardStep === 1) ? "hidden" : "visible";
  if (nextBtn) {
    if (wizardStep === 5) {
      nextBtn.innerHTML = `<i class="bi bi-check2-circle me-1"></i> Submit & Activate Mentor Profile`;
      nextBtn.className = "btn btn-success btn-lg";
      populateWizardReview();
    } else {
      nextBtn.innerHTML = `Next Step <i class="bi bi-arrow-right ms-1"></i>`;
      nextBtn.className = "btn btn-primary btn-lg";
    }
  }
}

function validateCurrentStep() {
  if (wizardStep === 1) {
    return true; // About info confirmed
  } else if (wizardStep === 2) {
    // Collect any custom skills added
    const customSkill = document.getElementById("custom-skill-input")?.value.trim();
    if (customSkill && !onboardingData.expertise.includes(customSkill)) {
      onboardingData.expertise.push(customSkill);
    }
    if (onboardingData.expertise.length === 0) {
      UI.toast({ type: "warning", title: "Expertise Required", message: "Please select at least 1 area of expertise." });
      return false;
    }
    return true;
  } else if (wizardStep === 3) {
    const rateInput = document.getElementById("wizard-rate-input");
    const rate = parseFloat(rateInput ? rateInput.value : 0);
    if (isNaN(rate) || rate < 0) {
      UI.toast({ type: "warning", title: "Invalid Rate", message: "Please enter a valid hourly rate (₹0 or higher)." });
      return false;
    }
    onboardingData.hourly_rate = rate;
    return true;
  } else if (wizardStep === 4) {
    const bioInput = document.getElementById("wizard-bio-input");
    const bio = bioInput ? bioInput.value.trim() : "";
    if (!bio || bio.length < 20) {
      UI.toast({ type: "warning", title: "Detailed Bio Required", message: "Please write at least 20 characters about your experience and how you can guide mentees." });
      return false;
    }
    onboardingData.bio = bio;
    return true;
  }
  return true;
}

function populateWizardReview() {
  const user = Auth.getCurrentUser();
  const reviewName = document.getElementById("review-name");
  const reviewSkills = document.getElementById("review-skills");
  const reviewRate = document.getElementById("review-rate");
  const reviewBio = document.getElementById("review-bio");

  if (reviewName && user) reviewName.textContent = `${user.first_name || ''} ${user.last_name || ''}`;
  if (reviewSkills) {
    reviewSkills.innerHTML = onboardingData.expertise.map(s => `<span class="skill-chip">${Utils.escapeHtml(s)}</span>`).join("");
  }
  if (reviewRate) reviewRate.textContent = Utils.formatCurrency(onboardingData.hourly_rate);
  if (reviewBio) reviewBio.textContent = onboardingData.bio;
}

async function submitBecomeMentor() {
  const submitBtn = document.getElementById("wizard-next-btn");
  UI.setLoading(submitBtn, true, "Activating Mentor Account...");

  try {
    const response = await api.mentors.becomeMentor({
      hourly_rate: onboardingData.hourly_rate,
      expertise: onboardingData.expertise,
      bio: onboardingData.bio
    });

    UI.setLoading(submitBtn, false);

    // Refresh user state
    await Auth.fetchCurrentUser();

    UI.toast({
      type: "success",
      title: "Welcome Mentor!",
      message: "You are now an active mentor on CampusConnect."
    });

    setTimeout(() => {
      window.location.href = "mentor-dashboard.html";
    }, 1200);
  } catch (err) {
    UI.setLoading(submitBtn, false);
    console.error("Mentor activation failed", err);
    UI.toast({
      type: "error",
      title: "Activation Failed",
      message: err.message || "Failed to activate mentor profile."
    });
  }
}

/**
 * =========================================================================
 * ACTIVE MENTOR PORTAL DASHBOARD VIEW
 * =========================================================================
 */
function showMentorDashboardView(user) {
  const onboardView = document.getElementById("mentor-onboarding-view");
  const dashboardView = document.getElementById("mentor-active-dashboard-view");

  if (onboardView) onboardView.style.display = "none";
  if (dashboardView) dashboardView.style.display = "block";

  const mentorName = document.getElementById("mentor-portal-name");
  if (mentorName) mentorName.textContent = user.first_name || "Mentor";
}
