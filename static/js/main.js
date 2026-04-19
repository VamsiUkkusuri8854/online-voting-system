/**
 * main.js - Landing Page Logic
 * Handles Login and Registration forms using Auth utility.
 */

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
});

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    try {
        const data = await Auth.fetch('/api/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });

        // Save token and show success on next page (Dashboard)
        Auth.saveToken(data.token, data.user.is_admin);
        Notifier.showOnNextPage(`Welcome back, ${data.user.name}!`, 'success');
        
        if (data.user.is_admin) {
            window.location.href = '/admin';
        } else {
            window.location.href = '/dashboard';
        }
    } catch (err) {
        Notifier.show(err.message || 'Login failed', 'error');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const name = document.getElementById('regName').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;

    try {
        await Auth.fetch('/api/register', {
            method: 'POST',
            body: JSON.stringify({ name, email, password })
        });

        Notifier.show('Registration successful! You can now log in.', 'success');
        setTimeout(() => window.location.reload(), 1500);
    } catch (err) {
        Notifier.show(err.message || 'Registration failed', 'error');
    }
}
