/**
 * Notifications Utility - VoteSafe
 * Manages toast notifications and cross-page messaging.
 */

const Notifier = {
    containerId: 'notifier-container',
    storageKey: 'votesafe_pending_notif',

    // Initialize container if it doesn't exist
    _getContainer() {
        let container = document.getElementById(this.containerId);
        if (!container) {
            container = document.createElement('div');
            container.id = this.containerId;
            container.className = 'notifier-container';
            document.body.appendChild(container);
        }
        return container;
    },

    /**
     * Show a toast notification
     * @param {string} msg 
     * @param {string} type - 'success', 'error', 'info'
     * @param {number} duration - ms
     */
    show(msg, type = 'info', duration = 4000) {
        const container = this._getContainer();
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icons = {
            success: '✓',
            error: '✕',
            info: 'ℹ'
        };

        toast.innerHTML = `
            <div class="toast-icon">${icons[type] || '•'}</div>
            <div class="toast-msg">${msg}</div>
            <div class="toast-close">&times;</div>
        `;

        container.appendChild(toast);

        // Click to close
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.onclick = () => this._removeToast(toast);

        // Auto remove
        setTimeout(() => {
            this._removeToast(toast);
        }, duration);
    },

    _removeToast(toast) {
        if (!toast.parentElement) return;
        toast.classList.add('removing');
        setTimeout(() => {
            if (toast.parentElement) {
                toast.parentElement.removeChild(toast);
            }
        }, 300);
    },

    /**
     * Save a notification to be shown on the next page load (e.g., after redirect)
     */
    showOnNextPage(msg, type = 'info') {
        sessionStorage.setItem(this.storageKey, JSON.stringify({ msg, type }));
    },

    /**
     * Check for and show any pending notifications from sessionStorage
     */
    checkPending() {
        const pending = sessionStorage.getItem(this.storageKey);
        if (pending) {
            const { msg, type } = JSON.parse(pending);
            this.show(msg, type);
            sessionStorage.removeItem(this.storageKey);
        }
    }
};

// Auto-check for pending notifications on script load
document.addEventListener('DOMContentLoaded', () => {
    Notifier.checkPending();
});

// Global export
window.Notifier = Notifier;
