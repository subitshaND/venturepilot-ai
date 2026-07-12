// VenturePilot AI — script.js

(function () {
  "use strict";

  /* ================================================================
     Result page — Download Report button (print-to-PDF)
  ================================================================ */
  const downloadBtn = document.getElementById("downloadBtn");
  if (downloadBtn) {
    downloadBtn.addEventListener("click", () => {
      // Brief visual feedback before the print dialog
      downloadBtn.textContent = "Preparing…";
      downloadBtn.disabled    = true;
      setTimeout(() => {
        window.print();
        downloadBtn.innerHTML = "&#8681;&nbsp; Download Report";
        downloadBtn.disabled  = false;
      }, 200);
    });
  }


  /* ================================================================
     Navbar — scroll effect + hamburger
  ================================================================ */
  const navbar    = document.getElementById("navbar");
  const hamburger = document.getElementById("hamburger");
  const navLinks  = document.getElementById("navLinks");

  if (navbar) {
    const onScroll = () => navbar.classList.toggle("scrolled", window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  if (hamburger && navLinks) {
    hamburger.addEventListener("click", () => {
      const isOpen = navLinks.classList.toggle("open");
      hamburger.setAttribute("aria-expanded", isOpen);
      const [s0, s1, s2] = hamburger.querySelectorAll("span");
      if (isOpen) {
        s0.style.transform = "translateY(7px) rotate(45deg)";
        s1.style.opacity   = "0";
        s2.style.transform = "translateY(-7px) rotate(-45deg)";
      } else {
        s0.style.transform = s2.style.transform = "";
        s1.style.opacity   = "";
      }
    });

    navLinks.querySelectorAll("a").forEach(link => {
      link.addEventListener("click", () => {
        navLinks.classList.remove("open");
        hamburger.setAttribute("aria-expanded", "false");
        const [s0, s1, s2] = hamburger.querySelectorAll("span");
        s0.style.transform = s2.style.transform = "";
        s1.style.opacity   = "";
      });
    });
  }

  /* ================================================================
     Smooth scroll for anchor links
  ================================================================ */
  document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener("click", e => {
      const target = document.querySelector(link.getAttribute("href"));
      if (target) {
        e.preventDefault();
        const offset = navbar ? navbar.offsetHeight + 12 : 0;
        window.scrollTo({ top: target.getBoundingClientRect().top + window.scrollY - offset, behavior: "smooth" });
      }
    });
  });

  /* ================================================================
     Intersection Observer — landing page feature card reveal
  ================================================================ */
  const cards = document.querySelectorAll(".feature-card");
  if ("IntersectionObserver" in window && cards.length) {
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.style.animationPlayState = "running";
          obs.unobserve(e.target);
        }
      });
    }, { threshold: 0.1 });
    cards.forEach(c => { c.style.animationPlayState = "paused"; obs.observe(c); });
  }

  /* ================================================================
     Form page — only runs when #startupForm exists
  ================================================================ */
  const form = document.getElementById("startupForm");
  if (!form) return;

  /* -- Field config
       optional:true  → skip required + minLen validation
       select:true    → validate non-empty selection
  ---------------------------------------------------------------- */
  const FIELDS = [
    { id: "startup_name",    label: "Startup Name",    minLen: 2  },
    { id: "founder_name",    label: "Founder Name",    optional: true },
    { id: "industry",        label: "Industry",        select: true },
    { id: "startup_idea",    label: "Startup Idea",    minLen: 20 },
    { id: "target_audience", label: "Target Audience", minLen: 5  },
    { id: "business_stage",  label: "Business Stage",  select: true },
  ];

  /* -- Helpers -------------------------------------------------- */
  function getEl(id)    { return document.getElementById(id); }
  function getGroup(id) { return document.getElementById("group_" + id); }
  function getErr(id)   { return document.getElementById("err_" + id); }

  function setError(id, msg) {
    const group = getGroup(id);
    const err   = getErr(id);
    if (!group || !err) return;
    group.classList.toggle("has-error", !!msg);
    err.textContent = msg || "";
  }

  function clearError(id) { setError(id, ""); }

  function validateField(cfg) {
    if (cfg.optional) return true;           // skip validation for optional fields
    const el = getEl(cfg.id);
    if (!el) return true;
    const val = el.value.trim();

    if (!val) {
      setError(cfg.id, `${cfg.label} is required.`);
      return false;
    }
    if (!cfg.select && cfg.minLen && val.length < cfg.minLen) {
      setError(cfg.id, `${cfg.label} must be at least ${cfg.minLen} characters.`);
      return false;
    }
    clearError(cfg.id);
    return true;
  }

  /* -- Progress pill live update -------------------------------- */
  function updatePill(id) {
    const el   = getEl(id);
    const pill = document.querySelector(`.fp-pill[data-field="${id}"]`);
    if (!el || !pill) return;
    pill.classList.toggle("filled", el.value.trim() !== "");
  }

  FIELDS.forEach(cfg => {
    const el = getEl(cfg.id);
    if (!el) return;

    // Live validation on blur (required fields only)
    el.addEventListener("blur", () => {
      validateField(cfg);
      updatePill(cfg.id);
    });

    // Clear error + update pill on every keystroke / selection change
    el.addEventListener("input",  () => { clearError(cfg.id); updatePill(cfg.id); });
    el.addEventListener("change", () => { clearError(cfg.id); updatePill(cfg.id); });

    // Seed initial state
    updatePill(cfg.id);
  });

  /* -- Textarea character counter ------------------------------- */
  const ideaEl    = getEl("startup_idea");
  const charEl    = getEl("char_startup_idea");
  const MAX_CHARS = 2000;

  if (ideaEl && charEl) {
    function updateCharCount() {
      const len = ideaEl.value.length;
      charEl.textContent = `${len.toLocaleString()} / ${MAX_CHARS.toLocaleString()}`;
      charEl.classList.toggle("warn",  len > MAX_CHARS * 0.85 && len <= MAX_CHARS);
      charEl.classList.toggle("limit", len >= MAX_CHARS);
    }
    ideaEl.addEventListener("input", updateCharCount);
    updateCharCount();
  }

  /* -- Reset button -------------------------------------------- */
  const resetBtn = getEl("resetBtn");
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      // Delay so the native form reset fires first
      setTimeout(() => {
        FIELDS.forEach(cfg => {
          clearError(cfg.id);
          updatePill(cfg.id);
        });
        if (charEl) {
          charEl.textContent = `0 / ${MAX_CHARS.toLocaleString()}`;
          charEl.className = "fp-char-count";
        }
      }, 0);
    });
  }

  /* -- Form submit --------------------------------------------- */
  const submitBtn = getEl("submitBtn");

  form.addEventListener("submit", e => {
    e.preventDefault();

    // Validate all required fields
    const results  = FIELDS.map(cfg => validateField(cfg));
    const allValid = results.every(Boolean);

    if (!allValid) {
      // Shake & scroll to the first invalid group
      const firstBad = FIELDS.find((cfg, i) => !results[i]);
      if (firstBad) {
        const group = getGroup(firstBad.id);
        if (group) {
          group.classList.remove("shake");
          void group.offsetWidth;          // force reflow to restart CSS animation
          group.classList.add("shake");
          group.addEventListener("animationend", () => group.classList.remove("shake"), { once: true });
        }
        const el = getEl(firstBad.id);
        if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
      return;
    }

    // All valid — show loading state then submit natively
    if (submitBtn) {
      submitBtn.classList.add("loading");
      submitBtn.disabled = true;
    }
    form.submit();
  });

})();
