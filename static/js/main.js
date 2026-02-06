/* static/js/main.js */

// 1. GLOBAL TOGGLE FUNCTION (Robust Version)
window.toggleProfileMenu = function(e) {
    // Safety check: get the event even if not passed explicitly
    const event = e || window.event; 
    if (event) {
        event.stopPropagation(); // Stop the click from closing the menu immediately
    }

    const menu = document.getElementById('profile-dropdown-menu');
    if (menu) {
        menu.classList.toggle('hidden');
        console.log("Toggle Menu Fired. Hidden status:", menu.classList.contains('hidden'));
    } else {
        console.error("Error: Element 'profile-dropdown-menu' not found.");
    }
};

document.addEventListener('DOMContentLoaded', function() {
    
    console.log("Main.js Loaded successfully.");

    // 2. CLOSE DROPDOWNS ON OUTSIDE CLICK
    window.addEventListener('click', function(e) {
        const menu = document.getElementById('profile-dropdown-menu');
        const btn = document.getElementById('profile-menu-btn');

        // Only close if menu exists and is currently OPEN (not hidden)
        if (menu && !menu.classList.contains('hidden')) {
            // Check if the click target is NOT the button (to prevent double-toggling)
            if (btn && !btn.contains(e.target)) {
                menu.classList.add('hidden');
            }
        }
        
        // Modal Closing Logic (Backdrop Click)
        if (e.target.classList.contains('modal') || e.target.classList.contains('fixed')) {
            if (e.target.id !== 'webcamModal') {
                if (typeof closeModal === 'function') {
                    closeModal(e.target.id);
                } else {
                    e.target.classList.add('hidden');
                }
            }
        }
    });

    // 3. AUTO-DISMISS TOASTS
    const notifications = document.querySelectorAll('.toast-notification');
    if (notifications.length > 0) {
        setTimeout(() => {
            notifications.forEach(toast => {
                toast.classList.add('hiding');
                toast.addEventListener('animationend', () => toast.remove());
            });
        }, 4000);
    }
});

// 4. HELPER FUNCTIONS (For Modals)
window.openModal = function(id) {
    const modal = document.getElementById(id);
    if(modal) {
        modal.classList.remove('hidden');
        setTimeout(() => modal.classList.remove('opacity-0'), 10);
        document.body.style.overflow = 'hidden';
    }
};

window.closeModal = function(id) {
    const modal = document.getElementById(id);
    if(modal) {
        modal.classList.add('opacity-0');
        setTimeout(() => {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }, 300);
    }
};