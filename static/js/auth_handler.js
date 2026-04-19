/**
 * Auth Handler - Global JWT Management
 * Handles token storage, request interception, and auth state.
 */

const Auth = {
    TOKEN_KEY: 'vote_safe_token',

    // Get token from localStorage
    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    },

    // Save token to localStorage
    saveToken(token, is_admin = false) {
        localStorage.setItem(this.TOKEN_KEY, token);
        localStorage.setItem('vote_safe_admin', is_admin);
        // Set cookie so backend can protect standard frontend routes
        document.cookie = `vote_safe_token=${token}; path=/; max-age=86400;`;
    },

    // Remove token (logout)
    logout() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem('vote_safe_admin');
        document.cookie = 'vote_safe_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT;';
        window.location.href = '/';
    },

    // Check if user is authenticated
    isAuthenticated() {
        return !!this.getToken();
    },

    isAdmin() {
        return localStorage.getItem('vote_safe_admin') === 'true';
    },

    syncNavRoles() {
        if (this.isAuthenticated() && this.isAdmin()) {
            const adminLink = document.getElementById('adminLink');
            if (adminLink) adminLink.classList.remove('hidden');
        }
    },

    // Secure Fetch Wrapper
    async fetch(url, options = {}) {
        const token = this.getToken();
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                ...(token ? { 'Authorization': `Bearer ${token}` } : {})
            }
        };

        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...(options.headers || {})
            }
        };

        try {
            const response = await fetch(url, mergedOptions);
            
            if (response.status === 401) {
                // Token likely expired or invalid
                this.logout();
                throw new Error('Session expired. Please login again.');
            }

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'API Request failed');
            }

            return data;
        } catch (err) {
            console.error(`Auth.fetch error [${url}]:`, err);
            throw err;
        }
    }
};

// Global export
window.Auth = Auth;

document.addEventListener('DOMContentLoaded', () => {
    Auth.syncNavRoles();
});
