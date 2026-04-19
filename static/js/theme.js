/**
 * Theme Manager - VoteSafe
 * Handles light/dark mode switching and persistence.
 */

const ThemeManager = {
    storageKey: 'votesafe_theme',

    init() {
        const savedTheme = localStorage.getItem(this.storageKey) || 'dark';
        this.applyTheme(savedTheme);
    },

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(this.storageKey, theme);
        this.updateToggleIcon(theme);
    },

    toggle() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(newTheme);
    },

    updateToggleIcon(theme) {
        const icons = document.querySelectorAll('.theme-toggle i');
        icons.forEach(icon => {
            if (theme === 'light') {
                icon.className = 'fas fa-moon'; // Show moon to switch to dark
            } else {
                icon.className = 'fas fa-sun'; // Show sun to switch to light
            }
        });
    }
};

// Initialize on script load
ThemeManager.init();

window.ThemeManager = ThemeManager;
