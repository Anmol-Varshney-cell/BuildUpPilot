document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.getElementById('sidebar') || document.querySelector('.sidebar');
  const content = document.getElementById('content') || document.querySelector('.main-content');
  const toggleButtons = document.querySelectorAll('#sidebar-toggle, .sidebar-toggle, #sidebarToggle, .sidebar-toggle-btn');

  if (!sidebar) return;

  // Mark body as having sidebar for header shift
  document.body.classList.add('has-sidebar');

  // Restore sidebar closed preference from localStorage
  const savedState = localStorage.getItem('buildup_sidebar_closed');
  if (savedState === 'true') {
    document.body.classList.add('sidebar-closed');
  }

  // Toggle Sidebar Function
  function toggleSidebar() {
    const isClosed = document.body.classList.toggle('sidebar-closed');
    localStorage.setItem('buildup_sidebar_closed', isClosed ? 'true' : 'false');
  }

  // Click event listener on all toggle buttons
  toggleButtons.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleSidebar();
    });
  });

  // Highlight active link automatically based on current page URL
  const currentPath = window.location.pathname;
  const menuLinks = document.querySelectorAll('.sidebar-menu a, .menu-link');

  menuLinks.forEach((link) => {
    const href = link.getAttribute('href');
    if (href && href !== '#' && (currentPath === href || (href !== '/' && currentPath.startsWith(href)))) {
      menuLinks.forEach((l) => l.classList.remove('active'));
      link.classList.add('active');
    }
  });
});
