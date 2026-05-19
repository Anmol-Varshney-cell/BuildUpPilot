// THEME TOGGLE
const themeToggle = document.getElementById("themeToggle");
const iconLight = document.getElementById("iconLight");
const iconDark = document.getElementById("iconDark");

function applyTheme(mode) {
  if (mode === "light") {
    document.body.classList.remove("theme-dark");
    document.body.classList.add("theme-light");
    iconLight.classList.add("hidden");
    iconDark.classList.remove("hidden");
  } else {
    document.body.classList.remove("theme-light");
    document.body.classList.add("theme-dark");
    iconLight.classList.remove("hidden");
    iconDark.classList.add("hidden");
    iconDark.classList.add("clip-primary-dark");
  }
  localStorage.setItem("buildUpPilotTheme", mode);
}

const storedTheme = localStorage.getItem("buildUpPilotTheme") || "dark";
applyTheme(storedTheme);

if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    const current = localStorage.getItem("buildUpPilotTheme") || "dark";
    applyTheme(current === "dark" ? "light" : "dark");
  });
}

// MOBILE NAV
const mobileToggle = document.getElementById("mobileToggle");
const mobileMenu = document.getElementById("mobileMenu");
const mobileIconOpen = document.getElementById("mobileIconOpen");
const mobileIconClose = document.getElementById("mobileIconClose");

if (mobileToggle && mobileMenu) {
  mobileToggle.addEventListener("click", () => {
    const isOpen = mobileMenu.classList.contains("open");
    if (isOpen) {
      mobileMenu.classList.remove("open");
      mobileIconOpen.classList.remove("hidden");
      mobileIconClose.classList.add("hidden");
    } else {
      mobileMenu.classList.add("open");
      mobileIconOpen.classList.add("hidden");
      mobileIconClose.classList.remove("hidden");
    }
  });
}

// Close mobile nav when clicking a link
const mobileLinks = document.querySelectorAll(".mobile-menu-links a");
mobileLinks.forEach((link) => {
  link.addEventListener("click", () => {
    if (mobileMenu.classList.contains("open")) {
      mobileMenu.classList.remove("open");
      mobileIconOpen.classList.remove("hidden");
      mobileIconClose.classList.add("hidden");
    }
  });
});

// SUPPORT TICKET FORM
const ticketForm = document.getElementById("ticketForm");
const ticketFeedback = document.getElementById("ticketFeedback");
const ticketStatusBadge = document.getElementById("ticketStatusBadge");

if (ticketForm) {
  ticketForm.addEventListener("submit", (e) => {
    e.preventDefault();

    const payload = {
      name: document.getElementById("ticketName").value,
      email: document.getElementById("ticketEmail").value,
      type: document.getElementById("ticketType").value,
      message: document.getElementById("ticketMessage").value,
      screenshot: document.getElementById("ticketScreenshot").value
    };

    // Send payload to backend API
    fetch("/api/tickets", { 
      method: "POST", 
      body: JSON.stringify(payload), 
      headers: { "Content-Type": "application/json" } 
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        if (ticketFeedback) {
          ticketFeedback.classList.remove("hidden");
          ticketFeedback.textContent = data.message || 'Ticket created successfully! Our admin team has been notified.';
        }
        if (ticketStatusBadge) {
          ticketStatusBadge.textContent = "Ticket sent to admin · tracking #" + (data.ticket_id || Math.floor(Math.random() * 9999));
        }
      } else {
        alert(data.message || 'Failed to create ticket. Please try again.');
      }
    })
    .catch(error => {
      console.error('Error creating ticket:', error);
      alert('Error creating ticket. Please try again later.');
    });

    ticketForm.reset();

    setTimeout(() => {
      if (ticketFeedback) ticketFeedback.classList.add("hidden");
    }, 6000);
  });
}
// PAGE LOAD ANIMATION
window.addEventListener("load", () => {
  const animItems = document.querySelectorAll(".animate-on-load");
  animItems.forEach((el) => {
    // small timeout so CSS has applied before we add the class
    setTimeout(() => {
      el.classList.add("is-visible");
    }, 50);
  });
});