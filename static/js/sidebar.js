document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.getElementById('sidebar') || document.querySelector('.sidebar');
  const content = document.getElementById('content') || document.querySelector('.main-content');
  const toggleBtn = document.getElementById('sidebar-toggle') || document.getElementById('sidebarToggle');

  if (!sidebar) return;

  // Mark body as having sidebar for header shift
  document.body.classList.add('has-sidebar');

  // Restore collapsed state preference from localStorage
  const savedState = localStorage.getItem('buildup_sidebar_collapsed');
  if (savedState === 'true' && window.innerWidth > 768) {
    sidebar.classList.add('sidebar-collapsed');
    document.body.classList.add('sidebar-collapsed-active');
    if (content) content.classList.add('content-collapsed');
  }

  // Toggle Sidebar Function
  function toggleSidebar() {
    const isMobile = window.innerWidth <= 768;

    if (isMobile) {
      // Mobile slide-over drawer toggle
      sidebar.classList.toggle('sidebar-open-mobile');
      document.body.classList.toggle('sidebar-open');
    } else {
      // Desktop collapsible width toggle
      const isCollapsed = sidebar.classList.toggle('sidebar-collapsed');
      document.body.classList.toggle('sidebar-collapsed-active', isCollapsed);
      if (content) content.classList.toggle('content-collapsed', isCollapsed);
      localStorage.setItem('buildup_sidebar_collapsed', isCollapsed);
    }
  }

  // Click event listener on toggle button
  if (toggleBtn) {
    toggleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleSidebar();
    });
  }

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
