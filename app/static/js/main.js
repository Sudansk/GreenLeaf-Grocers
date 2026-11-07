// GreenLeaf Grocers - Main Application JavaScript

document.addEventListener('DOMContentLoaded', function () {
  // 1. Mobile Sidebar Toggle
  const toggleBtn = document.getElementById('sidebarToggle');
  const sidebar = document.querySelector('.sidebar');
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', function () {
      sidebar.classList.toggle('show');
    });
  }

  // 2. Auto-dismiss alerts after 4 seconds
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) {
        bsAlert.close();
      }
    }, 4500);
  });

  // 3. Confirm Delete Modals / Buttons
  document.querySelectorAll('[data-confirm]').forEach(function (element) {
    element.addEventListener('click', function (e) {
      const message = this.getAttribute('data-confirm') || 'Are you sure you want to proceed?';
      if (!confirm(message)) {
        e.preventDefault();
      }
    });
  });
});
