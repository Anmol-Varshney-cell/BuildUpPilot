document.addEventListener('DOMContentLoaded', () => {
    const root = document.documentElement;
    const body = document.body;
    const themeToggle = document.getElementById('themeToggle');
    const iconLight = document.getElementById('iconLight');
    const iconDark = document.getElementById('iconDark');
    const storedTheme = localStorage.getItem('buildUpPilotTheme') || 'dark';

    function applyTheme(theme) {
        root.classList.remove('theme-dark', 'theme-light');
        body.classList.remove('theme-dark', 'theme-light');
        root.classList.add(`theme-${theme}`);
        body.classList.add(`theme-${theme}`);
        localStorage.setItem('buildUpPilotTheme', theme);

        if (iconLight && iconDark) {
            if (theme === 'light') {
                iconLight.classList.add('hidden');
                iconDark.classList.remove('hidden');
            } else {
                iconLight.classList.remove('hidden');
                iconDark.classList.add('hidden');
            }
        }
    }

    applyTheme(storedTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const currentTheme = localStorage.getItem('buildUpPilotTheme') || 'dark';
            applyTheme(currentTheme === 'dark' ? 'light' : 'dark');
        });
    }

    document.querySelectorAll('nav.navbar[style]').forEach((navbar) => {
        navbar.removeAttribute('style');
    });

    document.querySelectorAll('.nav-links span').forEach((span) => {
        if (span.textContent.includes('Student ID')) {
            span.classList.add('portal-id-chip');
            span.removeAttribute('style');
        }
    });

    document.querySelectorAll('.logo').forEach((logo) => {
        if (!logo.querySelector('.logo-wordmark')) {
            const wordmark = document.createElement('span');
            wordmark.className = 'logo-wordmark';
            wordmark.innerHTML = '<strong>BUILD UP</strong><small>PILOT</small>';
            logo.appendChild(wordmark);
        }
    });

    document.querySelectorAll('.page-header h1, .page-header h2, .page-header h3').forEach((heading) => {
        heading.classList.add('portal-heading');
        heading.removeAttribute('style');
    });

    document.querySelectorAll('.page-header p').forEach((paragraph) => {
        paragraph.classList.add('portal-subheading');
        paragraph.removeAttribute('style');
    });

    document.querySelectorAll('.card h2, .card h3').forEach((heading) => {
        heading.classList.add('portal-card-heading');
        if (heading.closest('.page-header')) {
            return;
        }
        if (heading.getAttribute('style')?.includes('color:')) {
            heading.removeAttribute('style');
        }
    });

    document.querySelectorAll('.sidebar > div').forEach((panel) => {
        if (panel.getAttribute('style')?.includes('text-align: center')) {
            panel.classList.add('sidebar-profile-panel');
        }
    });

    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });

    document.querySelectorAll('details').forEach(detail => {
        detail.addEventListener('toggle', () => {
            if (detail.open) {
                document.querySelectorAll('details').forEach(d => {
                    if (d !== detail) d.open = false;
                });
            }
        });
    });

    const smoothScrollLinks = document.querySelectorAll('a[href^="#"]');
    smoothScrollLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });

    const animatedElements = document.querySelectorAll('.fade-in');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animationPlayState = 'running';
            }
        });
    });
    animatedElements.forEach(el => observer.observe(el));

    const revealTargets = document.querySelectorAll(
        '.page-header, .card, .stat-card, .job-card, .mentor-card, .discussion-card, .roadmap-week-card, .question-card, .interview-header, .interview-question'
    );

    const shouldSkipReveal = document.body.dataset.disableRevealAnimation === 'true';
    if (shouldSkipReveal) {
        revealTargets.forEach((element) => {
            element.classList.remove('animate-in');
            element.classList.add('is-visible');
            element.style.transitionDelay = '0ms';
        });
        return;
    }

    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
                revealObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.12 });

    revealTargets.forEach((element, index) => {
        element.classList.add('animate-in');
        element.style.transitionDelay = `${Math.min(index * 40, 240)}ms`;
        revealObserver.observe(element);
    });
});

function showModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function hideModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });
});

async function updateApplicationStatus(applicationId, status) {
    try {
        const response = await fetch(`/api/update-application/${applicationId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        const data = await response.json();
        if (data.success) {
            alert('Status updated successfully!');
        }
    } catch (error) {
        alert('Error updating status');
    }
}

async function updateTicketStatus(ticketId, status) {
    try {
        const response = await fetch(`/api/update-ticket/${ticketId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        const data = await response.json();
        if (data.success) {
            alert('Ticket status updated!');
            location.reload();
        }
    } catch (error) {
        alert('Error updating ticket');
    }
}

function startTimer(duration, display) {
    let timer = duration, minutes, seconds;
    setInterval(function () {
        minutes = parseInt(timer / 60, 10);
        seconds = parseInt(timer % 60, 10);
        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;
        display.textContent = minutes + ":" + seconds;
        if (--timer < 0) {
            timer = duration;
        }
    }, 1000);
}

document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        console.log('Tab switched - logging for proctoring');
    }
});
