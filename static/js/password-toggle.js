// Password toggle functionality
document.addEventListener('DOMContentLoaded', function() {
  const toggles = document.querySelectorAll('.toggle-password');
  
  toggles.forEach(toggle => {
    toggle.addEventListener('click', function() {
      const targetId = this.dataset.target;
      const passwordField = document.getElementById(targetId);
      if (!passwordField) return;
      
      if (passwordField.type === 'password') {
        passwordField.type = 'text';
        this.innerHTML = '&#128683;';
        this.setAttribute('aria-label', 'Hide password');
        this.setAttribute('title', 'Hide password');
      } else {
        passwordField.type = 'password';
        this.innerHTML = '&#128065;';
        this.setAttribute('aria-label', 'Show password');
        this.setAttribute('title', 'Show password');
      }
    });
  });
});

