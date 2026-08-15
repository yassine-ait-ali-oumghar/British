function initAutoDismissAlerts() {
    document.querySelectorAll('.alert-auto-dismiss').forEach((alert) => {
        const delay = parseInt(alert.dataset.dismissDelay || '5000', 10);

        setTimeout(() => {
            alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-8px)';

            setTimeout(() => {
                alert.remove();
            }, 400);
        }, delay);
    });
}

document.addEventListener('DOMContentLoaded', initAutoDismissAlerts);
