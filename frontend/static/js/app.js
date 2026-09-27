/**
 * PocketSmart AI™ - Executive Client-side Controller & View Router
 * Handles all 8 Real-World Budget Optimizers + Auth + History
 */

let activeToken = localStorage.getItem("pocketsmart_token") || null;
let activeUser = null;
let activeImageBase64 = null;

function renderIcons() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

function notify(message, type = "info") {
  const shelf = document.getElementById("toast-shelf");
  if (!shelf) return;
  const toast = document.createElement("div");
  toast.className = "toast-box";

  const icon = type === "success" ? "check-circle" : type === "error" ? "alert-circle" : "info";
  const iconColor = type === "success" ? "#34d399" : type === "error" ? "#f87171" : "#818cf8";

  toast.innerHTML = `<i data-lucide="${icon}" style="color: ${iconColor}; width: 16px; height: 16px;"></i><span>${message}</span>`;
  shelf.appendChild(toast);
  renderIcons();

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3800);
}

function togglePlannersDropdown(e) {
  if (e) e.stopPropagation();
  const wrapper = document.getElementById("planners-dropdown");
  if (wrapper) {
    wrapper.classList.toggle("open");
  }
}

function selectPlannerTab(plannerId) {
  const wrapper = document.getElementById("planners-dropdown");
  if (wrapper) wrapper.classList.remove("open");
  switchTab(plannerId);
}

function toggleMobileMenu() {
  const drawer = document.getElementById("mobile-nav-drawer");
  if (drawer) {
    drawer.classList.toggle("open");
  }
}

function switchTabMobile(viewId) {
  const drawer = document.getElementById("mobile-nav-drawer");
  if (drawer) drawer.classList.remove("open");
  switchTab(viewId);
}

// Close dropdown when clicking anywhere outside
document.addEventListener("click", (e) => {
  const wrapper = document.getElementById("planners-dropdown");
  if (wrapper && !wrapper.contains(e.target)) {
    wrapper.classList.remove("open");
  }
});

function switchTab(viewId) {
  document.querySelectorAll(".tab-view").forEach(v => v.classList.remove("active"));
  document.querySelectorAll(".nav-tab-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".dropdown-item").forEach(d => d.classList.remove("active"));

  const targetView = document.getElementById(`view-${viewId}`);
  if (targetView) {
    targetView.classList.add("active");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  const activeBtn = document.getElementById(`tab-${viewId}`);
  if (activeBtn) {
    activeBtn.classList.add("active");
  }

  // Highlight planner dropdown trigger if a planner is currently active
  const dropdownTrigger = document.getElementById("tab-planners-dropdown");
  if (dropdownTrigger) {
    if (viewId.includes("planner")) {
      dropdownTrigger.classList.add("active");
    } else {
      dropdownTrigger.classList.remove("active");
    }
  }

  if (viewId === "dashboard") {
    syncUserSession();
  } else if (viewId === "history") {
    fetchHistoryLog();
  }
  renderIcons();
}


async function syncUserSession() {
  if (!activeToken) {
    renderAuthSlot(null);
    return;
  }
  try {
    const res = await fetch("/session-info", {
      headers: { "Authorization": `Bearer ${activeToken}` }
    });
    const data = await res.json();
    if (data.success && data.user) {
      activeUser = data.user;
      renderAuthSlot(activeUser);
      loadDashboardMetrics();
    } else {
      activeToken = null;
      localStorage.removeItem("pocketsmart_token");
      renderAuthSlot(null);
    }
  } catch (err) {
    console.error("Session sync error:", err);
  }
}

function renderAuthSlot(user) {
  const slot = document.getElementById("header-auth-slot");
  if (!slot) return;

  if (user) {
    slot.innerHTML = `
      <div style="display: flex; align-items: center; gap: 0.65rem;">
        <div style="width: 34px; height: 34px; border-radius: 50%; background: var(--gradient-brand); display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.85rem; color: #fff;">
          ${user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
        </div>
        <div style="display: none; @media(min-width: 600px){display: block;}">
          <div style="font-size: 0.85rem; font-weight: 700; color: var(--text-hero);">${user.full_name || 'User'}</div>
          <div style="font-size: 0.72rem; color: var(--text-muted);">${user.email}</div>
        </div>
        <button class="btn btn-outline btn-sm" onclick="executeLogout()"><i data-lucide="log-out" style="width: 14px; height: 14px;"></i> Logout</button>
      </div>
    `;
    const dashLabel = document.getElementById("dash-user-label");
    if (dashLabel) dashLabel.textContent = user.full_name;
    document.querySelectorAll(".currency-label").forEach(el => el.textContent = user.currency || "$");
  } else {
    slot.innerHTML = `
      <button class="btn btn-outline btn-sm" onclick="switchTab('login')"><i data-lucide="log-in" style="width: 14px; height: 14px;"></i> Sign In</button>
      <button class="btn btn-primary btn-sm" onclick="switchTab('register')"><i data-lucide="user-plus" style="width: 14px; height: 14px;"></i> Get Started</button>
    `;
  }
  renderIcons();
}

async function executeRegister(e) {
  e.preventDefault();
  const full_name = document.getElementById("reg-name").value;
  const email = document.getElementById("reg-email").value;
  const password = document.getElementById("reg-password").value;
  const currency = document.getElementById("reg-currency").value;

  try {
    const res = await fetch("/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ full_name, email, password, currency })
    });
    const data = await res.json();
    if (data.success) {
      activeToken = data.token;
      localStorage.setItem("pocketsmart_token", activeToken);
      activeUser = data.user;
      renderAuthSlot(activeUser);
      notify("Account created successfully! Welcome to PocketSmart AI.", "success");
      switchTab("dashboard");
    } else {
      notify(data.message || "Registration failed.", "error");
    }
  } catch (err) {
    notify("Network connection error during registration.", "error");
  }
}

async function executeLogin(e) {
  e.preventDefault();
  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;

  try {
    const res = await fetch("/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (data.success) {
      activeToken = data.token;
      localStorage.setItem("pocketsmart_token", activeToken);
      activeUser = data.user;
      renderAuthSlot(activeUser);
      notify("Authenticated successfully. Welcome back!", "success");
      switchTab("dashboard");
    } else {
      notify(data.message || "Invalid email or password credentials.", "error");
    }
  } catch (err) {
    notify("Authentication server unreachable.", "error");
  }
}

async function executeLogout() {
  if (activeToken) {
    try {
      await fetch("/logout", {
        method: "POST",
        headers: { "Authorization": `Bearer ${activeToken}` }
      });
    } catch (e) {}
  }
  activeToken = null;
  activeUser = null;
  localStorage.removeItem("pocketsmart_token");
  renderAuthSlot(null);
  notify("Signed out successfully.", "info");
  switchTab("home");
}

// 1. Home Interior Planner
async function executeGenerateHome(e) {
  e.preventDefault();
  const btn = document.getElementById("btn-run-home");
  btn.innerHTML = `<span class="spin-indicator"></span> Synthesizing Catalog...`;
  btn.disabled = true;

  const payload = {
    room_type: document.getElementById("home-room").value,
    style_preference: document.getElementById("home-style").value,
    budget: parseFloat(document.getElementById("home-budget").value),
    space_size: document.getElementById("home-space").value,
    custom_notes: document.getElementById("home-notes").value,
    currency: activeUser ? activeUser.currency || "$" : "$"
  };

  try {
    const res = await fetch("/generate-home", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": activeToken ? `Bearer ${activeToken}` : ""
      },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    populateHomeResults(data);
    notify("Home interior recommendations synthesized!", "success");
    switchTab("home-recs");
  } catch (err) {
    notify("Generation failed. Please try again.", "error");
  } finally {
    btn.innerHTML = `<span class="btn-text-content"><i data-lucide="sparkles"></i> Generate AI Interior Recommendations</span>`;
    btn.disabled = false;
    renderIcons();
  }
}

function populateHomeResults(data) {
  document.getElementById("home-recs-title").textContent = `${data.style} — ${data.room_type}`;
  document.getElementById("home-recs-summary").textContent = data.design_concept_summary || "Curated multi-store interior plan.";
  document.getElementById("home-recs-budget-badge").textContent = `${data.currency}${data.allocated_budget} / ${data.currency}${data.total_budget}`;

  const rulesEl = document.getElementById("home-styling-rules");
  rulesEl.innerHTML = (data.styling_rules || []).map(r => `<li>${r}</li>`).join("");

  const container = document.getElementById("home-products-container");
  container.innerHTML = (data.products || []).map(p => `
    <div class="catalog-item">
      <img src="${p.image}" class="catalog-img" alt="${p.name}" onerror="this.src='https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&w=600&q=80'" />
      <div class="catalog-body">
        <span class="catalog-retailer">${p.platform || p.store} • ${p.category}</span>
        <div class="catalog-name">${p.name}</div>
        <p class="catalog-desc">${p.description}</p>
        ${p.saving_tip ? `<div style="font-size: 0.8rem; color: var(--emerald); margin-bottom: 0.8rem; font-weight: 500;">💡 ${p.saving_tip}</div>` : ''}
        <div class="catalog-footer">
          <span class="catalog-price">${p.currency || '$'}${p.price}</span>
          <a href="${p.link || '#'}" target="_blank" class="btn btn-outline btn-sm">
            Procure Item <i data-lucide="external-link" style="width: 13px; height: 13px;"></i>
          </a>
        </div>
      </div>
    </div>
  `).join("");
  renderIcons();
}

// 2. Party & Event Planner
async function executeGenerateParty(e) {
  e.preventDefault();
  const btn = document.getElementById("btn-run-party");
  btn.innerHTML = `<span class="spin-indicator"></span> Balancing Event Logistics...`;
  btn.disabled = true;

  const payload = {
    event_type: document.getElementById("party-event").value,
    guest_count: parseInt(document.getElementById("party-guests").value),
    budget: parseFloat(document.getElementById("party-budget").value),
    theme_preference: document.getElementById("party-theme").value,
    custom_notes: document.getElementById("party-notes").value,
    currency: activeUser ? activeUser.currency || "$" : "$"
  };

  try {
    const res = await fetch("/generate-party", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": activeToken ? `Bearer ${activeToken}` : ""
      },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    populatePartyResults(data);
    notify("Party budget logistics synthesized!", "success");
    switchTab("party-recs");
  } catch (err) {
    notify("Event planning error.", "error");
  } finally {
    btn.innerHTML = `<span class="btn-text-content"><i data-lucide="sparkles"></i> Synthesize Event Logistics Plan</span>`;
    btn.disabled = false;
    renderIcons();
  }
}

function populatePartyResults(data) {
  document.getElementById("party-recs-title").textContent = `${data.event_type} (${data.guest_count} Confirmed Guests)`;
  document.getElementById("party-recs-summary").textContent = data.theme_summary || "Multi-category party budget synthesis.";
  document.getElementById("party-cost-per-guest").textContent = `${data.currency}${data.cost_per_guest} / guest`;

  const vEl = document.getElementById("party-venue-list");
  vEl.innerHTML = (data.venue_suggestions || []).map(v => `
    <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: var(--radius-md); margin-bottom: 0.8rem; border: 1px solid var(--border-subtle);">
      <div style="display: flex; justify-content: space-between; font-weight: 700; font-size: 1rem; color: var(--text-hero);">
        <span>${v.title}</span>
        <span style="color: #f472b6;">${data.currency}${v.estimated_cost}</span>
      </div>
      <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem;">${v.type} • Capacity: ${v.capacity}</div>
      ${v.saving_hack ? `<div style="font-size: 0.78rem; color: var(--emerald); margin-top: 0.45rem; font-weight: 500;">💡 ${v.saving_hack}</div>` : ''}
    </div>
  `).join("");

  const tEl = document.getElementById("party-smart-tips");
  tEl.innerHTML = (data.smart_organizer_tips || []).map(t => `<li>${t}</li>`).join("");

  const cEl = document.getElementById("party-catering-list");
  cEl.innerHTML = (data.food_catering || []).map(c => `
    <div style="margin-bottom: 0.9rem; padding-bottom: 0.9rem; border-bottom: 1px solid var(--border-subtle);">
      <div style="display: flex; justify-content: space-between; font-weight: 700; color: var(--text-hero);">
        <span>${c.item}</span>
        <span style="color: var(--cyan);">${data.currency}${c.estimated_cost}</span>
      </div>
      <div style="font-size: 0.82rem; color: var(--text-muted); margin-top: 0.25rem;">${c.details} (${c.provider_type})</div>
    </div>
  `).join("");

  const dEl = document.getElementById("party-decor-list");
  dEl.innerHTML = (data.decorations || []).map(d => `
    <div style="margin-bottom: 0.9rem; padding-bottom: 0.9rem; border-bottom: 1px solid var(--border-subtle);">
      <div style="display: flex; justify-content: space-between; font-weight: 700; color: var(--text-hero);">
        <span>${d.item}</span>
        <span style="color: var(--amber);">${data.currency}${d.estimated_cost}</span>
      </div>
      <div style="font-size: 0.82rem; color: var(--text-muted); margin-top: 0.25rem;">Type: ${d.type}</div>
    </div>
  `).join("");

  renderIcons();
}

// 3. Jewelry Studio
function processJewelImageUpload(event) {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function(e) {
    activeImageBase64 = e.target.result.split(',')[1];
    const wrapper = document.getElementById("jewel-img-preview-wrapper");
    const imgTag = document.getElementById("jewel-preview-tag");
    imgTag.src = e.target.result;
    wrapper.style.display = "block";
  };
  reader.readAsDataURL(file);
}

async function executeGenerateJewelry(e) {
  e.preventDefault();
  const btn = document.getElementById("btn-run-jewelry");
  btn.innerHTML = `<span class="spin-indicator"></span> Curating Joaillerie...`;
  btn.disabled = true;

  const payload = {
    occasion: document.getElementById("jewel-occasion").value,
    outfit_style: document.getElementById("jewel-outfit").value,
    metal_preference: document.getElementById("jewel-metal").value,
    budget: parseFloat(document.getElementById("jewel-budget").value),
    custom_notes: document.getElementById("jewel-notes").value,
    image_base64: activeImageBase64,
    currency: activeUser ? activeUser.currency || "$" : "$"
  };

  try {
    const res = await fetch("/generate-jewelry", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": activeToken ? `Bearer ${activeToken}` : ""
      },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    populateJewelryResults(data);
    notify("Jewelry ensemble curated successfully!", "success");
    switchTab("jewelry-recs");
  } catch (err) {
    notify("Jewelry styling generation error.", "error");
  } finally {
    btn.innerHTML = `<span class="btn-text-content"><i data-lucide="sparkles"></i> Curate Haute Joaillerie Pairing</span>`;
    btn.disabled = false;
    renderIcons();
  }
}

function populateJewelryResults(data) {
  document.getElementById("jewel-recs-title").textContent = `${data.occasion} • ${data.metal_preference}`;
  document.getElementById("jewel-recs-summary").textContent = `Curated Ensemble for: ${data.outfit_style}`;
  document.getElementById("jewel-allocated-badge").textContent = `${data.currency}${data.allocated_budget} / ${data.currency}${data.total_budget}`;
  document.getElementById("jewel-verdict-content").textContent = data.styling_verdict || "Harmonious jewelry selection matching outfit neckline, color tones, and occasion prestige.";

  const container = document.getElementById("jewelry-items-catalog");
  container.innerHTML = (data.recommendations || []).map(j => `
    <div class="catalog-item">
      <img src="${j.image}" class="catalog-img" alt="${j.piece_name}" onerror="this.src='https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?auto=format&fit=crop&w=600&q=80'" />
      <div class="catalog-body">
        <span class="catalog-retailer">${j.retailer} • ${j.matching_score || '96% Match'}</span>
        <div class="catalog-name">${j.piece_name}</div>
        <div style="font-size: 0.8rem; color: var(--emerald); margin-bottom: 0.45rem; font-weight: 600;">${j.metal_type}</div>
        <p class="catalog-desc">${j.outfit_pairing || j.occasion_fit}</p>
        ${j.smart_buyer_tip ? `<div style="font-size: 0.78rem; color: var(--amber); margin-bottom: 0.8rem; font-weight: 500;">💎 ${j.smart_buyer_tip}</div>` : ''}
        <div class="catalog-footer">
          <span class="catalog-price">${j.currency || '$'}${j.estimated_price}</span>
          <span class="category-badge" style="background: rgba(16, 185, 129, 0.15); color: #34d399; border-color: rgba(16, 185, 129, 0.3);">${j.gemstone || 'Fine Finish'}</span>
        </div>
      </div>
    </div>
  `).join("");
  renderIcons();
}

// 4. Global Travel & Vacation Planner
async function executeGenerateTravel(e) {
  e.preventDefault();
  const btn = document.getElementById("btn-run-travel");
  btn.innerHTML = `<span class="spin-indicator"></span> Optimizing Itinerary Logistics...`;
  btn.disabled = true;

  const payload = {
    destination: document.getElementById("travel-dest").value,
    duration_days: parseInt(document.getElementById("travel-days").value),
    travelers_count: parseInt(document.getElementById("travel-pax").value),
    budget: parseFloat(document.getElementById("travel-budget").value),
    travel_style: document.getElementById("travel-style").value,
    custom_notes: document.getElementById("travel-notes").value,
    currency: activeUser ? activeUser.currency || "$" : "$"
  };

  try {
    const res = await fetch("/generate-travel", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": activeToken ? `Bearer ${activeToken}` : ""
      },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    populateTravelResults(data);
    notify("Travel optimization blueprint completed!", "success");
    switchTab("travel-recs");
  } catch (err) {
    notify("Travel planning error.", "error");
  } finally {
    btn.innerHTML = `<span class="btn-text-content"><i data-lucide="sparkles"></i> Synthesize Global Travel Itinerary</span>`;
    btn.disabled = false;
    renderIcons();
  }
}

function populateTravelResults(data) {
  document.getElementById("travel-recs-title").textContent = `${data.destination} (${data.duration_days} Days / ${data.travelers_count} Travelers)`;
  document.getElementById("travel-recs-summary").textContent = data.itinerary_concept || "Optimized flight, lodging, and cultural excursion allocation.";
  document.getElementById("travel-burn-badge").textContent = `${data.currency}${data.daily_burn_rate} / day`;

  const tEl = document.getElementById("travel-flights-list");
  tEl.innerHTML = (data.flights_transport || []).map(f => `
    <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: var(--radius-md); margin-bottom: 0.8rem; border: 1px solid var(--border-subtle);">
      <div style="display: flex; justify-content: space-between; font-weight: 700; color: var(--text-hero);">
        <span>${f.item}</span>
        <span style="color: var(--cyan);">${data.currency}${f.estimated_cost}</span>
      </div>
      <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem;">Provider: ${f.provider}</div>
      ${f.saving_hack ? `<div style="font-size: 0.78rem; color: var(--emerald); margin-top: 0.4rem;">💡 ${f.saving_hack}</div>` : ''}
    </div>
  `).join("");

  const aEl = document.getElementById("travel-lodging-list");
  aEl.innerHTML = (data.accommodation || []).map(a => `
    <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: var(--radius-md); margin-bottom: 0.8rem; border: 1px solid var(--border-subtle);">
      <div style="display: flex; justify-content: space-between; font-weight: 700; color: var(--text-hero);">
        <span>${a.item}</span>
        <span style="color: var(--amber);">${data.currency}${a.estimated_cost}</span>
      </div>
      <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem;">Platform: ${a.provider}</div>
      ${a.saving_hack ? `<div style="font-size: 0.78rem; color: var(--emerald); margin-top: 0.4rem;">💡 ${a.saving_hack}</div>` : ''}
    </div>
  `).join("");

  const rulesEl = document.getElementById("travel-pro-rules");
  rulesEl.innerHTML = (data.pro_traveler_rules || []).map(r => `<li>${r}</li>`).join("");

  renderIcons();
}

// 5. Tech Workstation Planner
async function executeGenerateTech(e) {
  e.preventDefault();
  const btn = document.getElementById("btn-run-tech");
  btn.innerHTML = `<span class="spin-indicator"></span> Architecting Hardware Stack...`;
  btn.disabled = true;

  const payload = {
    workflow_type: document.getElementById("tech-workflow").value,
    form_factor: document.getElementById("tech-form").value,
    budget: parseFloat(document.getElementById("tech-budget").value),
    custom_notes: document.getElementById("tech-notes").value,
    currency: activeUser ? activeUser.currency || "$" : "$"
  };

  try {
    const res = await fetch("/generate-tech", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": activeToken ? `Bearer ${activeToken}` : ""
      },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    populateTechResults(data);
    notify("Tech workstation architecture finalized!", "success");
    switchTab("tech-recs");
  } catch (err) {
    notify("Hardware generation error.", "error");
  } finally {
    btn.innerHTML = `<span class="btn-text-content"><i data-lucide="sparkles"></i> Synthesize Hardware Architecture</span>`;
    btn.disabled = false;
    renderIcons();
  }
}

function populateTechResults(data) {
  document.getElementById("tech-recs-title").textContent = `${data.workflow_type} Hardware Stack`;
  document.getElementById("tech-recs-summary").textContent = data.architecture_summary || "High price-to-performance workstation setup.";
  document.getElementById("tech-budget-badge").textContent = `${data.currency}${data.allocated_budget} / ${data.currency}${data.total_budget}`;

  const benchEl = document.getElementById("tech-benchmarks-list");
  benchEl.innerHTML = (data.efficiency_benchmarks || []).map(b => `<li>${b}</li>`).join("");

  const container = document.getElementById("tech-hardware-catalog");
  container.innerHTML = (data.hardware_items || []).map(h => `
    <div class="catalog-item">
      <img src="${h.image}" class="catalog-img" alt="${h.item_name}" onerror="this.src='https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=600&q=80'" />
      <div class="catalog-body">
        <span class="catalog-retailer">${h.retailer} • ${h.category}</span>
        <div class="catalog-name">${h.item_name}</div>
        <p class="catalog-desc">${h.description}</p>
        ${h.saving_tip ? `<div style="font-size: 0.8rem; color: var(--emerald); margin-bottom: 0.8rem; font-weight: 500;">💡 ${h.saving_tip}</div>` : ''}
        <div class="catalog-footer">
          <span class="catalog-price">${data.currency || '$'}${h.price}</span>
          <span class="category-badge">${h.rating} ★ Rating</span>
        </div>
      </div>
    </div>
  `).join("");
  renderIcons();
}

// 6. Milestone Wedding Planner
async function executeGenerateWedding(e) {
  e.preventDefault();
  const btn = document.getElementById("btn-run-wedding");
  btn.innerHTML = `<span class="spin-indicator"></span> Optimizing Celebration Capital...`;
  btn.disabled = true;

  const payload = {
    event_scale: document.getElementById("wedding-scale").value,
    guest_count: parseInt(document.getElementById("wedding-guests").value),
    budget: parseFloat(document.getElementById("wedding-budget").value),
    cultural_theme: document.getElementById("wedding-theme").value,
    custom_notes: document.getElementById("wedding-notes").value,
    currency: activeUser ? activeUser.currency || "$" : "$"
  };

  try {
    const res = await fetch("/generate-wedding", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": activeToken ? `Bearer ${activeToken}` : ""
      },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    populateWeddingResults(data);
    notify("Wedding celebration capital blueprint completed!", "success");
    switchTab("wedding-recs");
  } catch (err) {
    notify("Wedding planning error.", "error");
  } finally {
    btn.innerHTML = `<span class="btn-text-content"><i data-lucide="sparkles"></i> Structure Wedding Budget Blueprint</span>`;
    btn.disabled = false;
    renderIcons();
  }
}

function populateWeddingResults(data) {
  document.getElementById("wedding-recs-title").textContent = `${data.event_scale} (${data.guest_count} Guests)`;
  document.getElementById("wedding-recs-summary").textContent = data.curation_summary || "Disciplined wedding capital allocation.";
  document.getElementById("wedding-cost-badge").textContent = `${data.currency}${data.cost_per_guest} / guest`;

  const vEl = document.getElementById("wedding-venue-list");
  vEl.innerHTML = (data.venue_decor || []).map(v => `
    <div style="background: rgba(15, 23, 42, 0.6); padding: 0.9rem; border-radius: var(--radius-md); margin-bottom: 0.8rem; border: 1px solid var(--border-subtle);">
      <div style="display: flex; justify-content: space-between; font-weight: 700; color: var(--text-hero);">
        <span>${v.category}</span>
        <span style="color: var(--primary-light);">${data.currency}${v.estimated_cost}</span>
      </div>
      ${v.saving_hack ? `<div style="font-size: 0.78rem; color: var(--emerald); margin-top: 0.35rem;">💡 ${v.saving_hack}</div>` : ''}
    </div>
  `).join("");

  const cEl = document.getElementById("wedding-catering-list");
  cEl.innerHTML = (data.catering_hospitality || []).map(c => `
    <div style="background: rgba(15, 23, 42, 0.6); padding: 0.9rem; border-radius: var(--radius-md); margin-bottom: 0.8rem; border: 1px solid var(--border-subtle);">
      <div style="display: flex; justify-content: space-between; font-weight: 700; color: var(--text-hero);">
        <span>${c.category}</span>
        <span style="color: var(--cyan);">${data.currency}${c.estimated_cost}</span>
      </div>
      ${c.saving_hack ? `<div style="font-size: 0.78rem; color: var(--emerald); margin-top: 0.35rem;">💡 ${c.saving_hack}</div>` : ''}
    </div>
  `).join("");

  const rulesEl = document.getElementById("wedding-rules-list");
  rulesEl.innerHTML = (data.wedding_financial_rules || []).map(r => `<li>${r}</li>`).join("");

  renderIcons();
}

// 7. Weekly Grocery & Meal Prep
async function executeGenerateGrocery(e) {
  e.preventDefault();
  const btn = document.getElementById("btn-run-grocery");
  btn.innerHTML = `<span class="spin-indicator"></span> Optimizing Nutrient Matrix...`;
  btn.disabled = true;

  const payload = {
    household_size: parseInt(document.getElementById("grocery-household").value),
    dietary_regime: document.getElementById("grocery-diet").value,
    weekly_budget: parseFloat(document.getElementById("grocery-budget").value),
    custom_notes: document.getElementById("grocery-notes").value,
    currency: activeUser ? activeUser.currency || "$" : "$"
  };

  try {
    const res = await fetch("/generate-grocery", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": activeToken ? `Bearer ${activeToken}` : ""
      },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    populateGroceryResults(data);
    notify("Weekly nutrition & grocery blueprint synthesized!", "success");
    switchTab("grocery-recs");
  } catch (err) {
    notify("Grocery synthesis error.", "error");
  } finally {
    btn.innerHTML = `<span class="btn-text-content"><i data-lucide="sparkles"></i> Generate Weekly Nutrition Blueprint</span>`;
    btn.disabled = false;
    renderIcons();
  }
}

function populateGroceryResults(data) {
  document.getElementById("grocery-recs-title").textContent = `${data.dietary_regime} (${data.household_size} Persons)`;
  document.getElementById("grocery-recs-summary").textContent = data.nutrition_summary || "High bioavailability nutrition and zero produce waste.";
  document.getElementById("grocery-cost-badge").textContent = `${data.currency}${data.cost_per_meal} / meal`;

  const basketEl = document.getElementById("grocery-basket-list");
  basketEl.innerHTML = (data.grocery_items || []).map(g => `
    <div style="margin-bottom: 0.9rem; padding-bottom: 0.9rem; border-bottom: 1px solid var(--border-subtle);">
      <div style="display: flex; justify-content: space-between; font-weight: 700; color: var(--text-hero);">
        <span>${g.item}</span>
        <span style="color: var(--emerald);">${data.currency}${g.cost}</span>
      </div>
      <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem;">Market: ${g.store}</div>
      ${g.tip ? `<div style="font-size: 0.78rem; color: var(--cyan); margin-top: 0.35rem;">💡 ${g.tip}</div>` : ''}
    </div>
  `).join("");

  const prepEl = document.getElementById("grocery-prep-list");
  prepEl.innerHTML = (data.batch_prep_protocol || []).map(p => `<li>${p}</li>`).join("");

  renderIcons();
}

// 8. Collegiate Student Survival
async function executeGenerateStudent(e) {
  e.preventDefault();
  const btn = document.getElementById("btn-run-student");
  btn.innerHTML = `<span class="spin-indicator"></span> Calibrating Zero-Debt Living Matrix...`;
  btn.disabled = true;

  const payload = {
    academic_level: document.getElementById("student-level").value,
    monthly_allowance: parseFloat(document.getElementById("student-budget").value),
    city_tier: document.getElementById("student-city").value,
    custom_notes: document.getElementById("student-notes").value,
    currency: activeUser ? activeUser.currency || "$" : "$"
  };

  try {
    const res = await fetch("/generate-student", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": activeToken ? `Bearer ${activeToken}` : ""
      },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    populateStudentResults(data);
    notify("Collegiate survival blueprint ready!", "success");
    switchTab("student-recs");
  } catch (err) {
    notify("Student planner error.", "error");
  } finally {
    btn.innerHTML = `<span class="btn-text-content"><i data-lucide="sparkles"></i> Structure Zero-Debt Living Plan</span>`;
    btn.disabled = false;
    renderIcons();
  }
}

function populateStudentResults(data) {
  document.getElementById("student-recs-title").textContent = `${data.academic_level} Monthly Living Plan`;
  document.getElementById("student-recs-summary").textContent = data.strategy_summary || "Zero-debt collegiate cash-flow management.";
  document.getElementById("student-daily-badge").textContent = `${data.currency}${data.daily_discretionary} / day`;

  const catEl = document.getElementById("student-categories-list");
  catEl.innerHTML = (data.allocation_categories || []).map(c => `
    <div style="background: rgba(15, 23, 42, 0.6); padding: 0.9rem; border-radius: var(--radius-md); margin-bottom: 0.8rem; border: 1px solid var(--border-subtle);">
      <div style="display: flex; justify-content: space-between; font-weight: 700; color: var(--text-hero);">
        <span>${c.category}</span>
        <span style="color: var(--primary-light);">${data.currency}${c.estimated_cost}</span>
      </div>
      ${c.hack ? `<div style="font-size: 0.78rem; color: var(--emerald); margin-top: 0.35rem;">💡 ${c.hack}</div>` : ''}
    </div>
  `).join("");

  const rulesEl = document.getElementById("student-rules-list");
  rulesEl.innerHTML = (data.student_survival_commandments || []).map(r => `<li>${r}</li>`).join("");

  renderIcons();
}

// History & Dashboard
async function fetchHistoryLog() {
  try {
    const res = await fetch("/history", {
      headers: { "Authorization": activeToken ? `Bearer ${activeToken}` : "" }
    });
    const items = await res.json();
    const container = document.getElementById("history-log-shelf");
    if (!items || items.length === 0) {
      container.innerHTML = `<p style="color: var(--text-muted); text-align: center; padding: 2.5rem;">No historical queries recorded yet.</p>`;
      return;
    }
    container.innerHTML = items.map(h => `
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 1.1rem 0; border-bottom: 1px solid var(--border-subtle); flex-wrap: wrap; gap: 0.8rem;">
        <div>
          <div style="display: flex; align-items: center; gap: 0.6rem;">
            <span class="category-badge">${h.type}</span>
            <span style="font-weight: 700; font-size: 1.05rem; color: var(--text-hero);">${h.title}</span>
          </div>
          <div style="font-size: 0.82rem; color: var(--text-muted); margin-top: 0.3rem;">
            ${h.summary} • <span style="color: var(--text-dim);">${h.timestamp}</span>
          </div>
        </div>
        <div style="text-align: right;">
          <span style="font-size: 1.2rem; font-weight: 800; color: var(--primary-light);">${h.currency}${h.budget}</span>
        </div>
      </div>
    `).join("");
    renderIcons();
  } catch (err) {
    console.error("History fetch error:", err);
  }
}

async function loadDashboardMetrics() {
  try {
    const res = await fetch("/history", {
      headers: { "Authorization": activeToken ? `Bearer ${activeToken}` : "" }
    });
    const items = await res.json();
    if (items) {
      document.getElementById("dash-stat-plans").textContent = items.length;
      const totalBudget = items.reduce((acc, it) => acc + (parseFloat(it.budget) || 0), 0);
      const estimatedSavings = totalBudget * 0.18;
      document.getElementById("dash-stat-savings").textContent = `$${estimatedSavings.toFixed(2)}`;

      const dashShelf = document.getElementById("dash-recent-records");
      dashShelf.innerHTML = items.slice(0, 4).map(h => `
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.9rem 0; border-bottom: 1px solid var(--border-subtle);">
          <div>
            <span style="font-weight: 700; font-size: 0.95rem; color: var(--text-hero);">${h.title}</span>
            <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 0.2rem;">${h.type} • ${h.timestamp}</div>
          </div>
          <span style="font-weight: 800; color: var(--emerald); font-size: 1rem;">${h.currency}${h.budget}</span>
        </div>
      `).join("");
    }
  } catch (e) {}
}

async function verifySystemStartup() {
  try {
    const res = await fetch("/startup");
    const data = await res.json();
    notify(`Status: ${data.status.toUpperCase()} | Services: ${data.services_loaded.length}`, "success");
  } catch (e) {
    notify("Service status check error.", "error");
  }
}

window.addEventListener("DOMContentLoaded", () => {
  renderIcons();
  syncUserSession();
});
