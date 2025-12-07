/**
 * Authentication utilities
 * Handles login state and redirects
 */

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return !!localStorage.getItem('auth_token');
}

/**
 * Get current user info
 */
function getCurrentUser() {
    const userInfo = localStorage.getItem('user_info');
    return userInfo ? JSON.parse(userInfo) : null;
}

/**
 * Require authentication (redirect to login if not authenticated)
 */
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/login.html';
        return false;
    }
    return true;
}

/**
 * Redirect to main app if already authenticated
 */
function redirectIfAuthenticated() {
    if (isAuthenticated()) {
        window.location.href = '/upload.html';
        return true;
    }
    return false;
}

/**
 * Show/hide elements based on admin status
 */
function updateAdminUI() {
    const user = getCurrentUser();
    const isAdmin = user && user.is_admin;

    document.querySelectorAll('[data-admin-only]').forEach(el => {
        el.style.display = isAdmin ? '' : 'none';
    });
}

/**
 * Display user info in UI
 */
function displayUserInfo() {
    const user = getCurrentUser();
    if (!user) return;

    const usernameElements = document.querySelectorAll('[data-username]');
    usernameElements.forEach(el => {
        el.textContent = user.username;
    });

    updateAdminUI();
}

/**
 * Show loading overlay
 */
function showLoading(message = 'Loading...') {
    let overlay = document.getElementById('loading-overlay');

    if (!overlay) {
        // Create overlay if it doesn't exist (for pages without static overlay)
        overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
    <div class="loading-content">
      <div class="spinner"></div>
      <div class="loading-text">${message}</div>
    </div>
  `;
        document.body.appendChild(overlay);
    } else {
        // Update message in existing overlay
        const textEl = overlay.querySelector('.loading-text');
        if (textEl) {
            textEl.textContent = message;
        }
    }

    overlay.style.display = 'flex';
}

/**
 * Hide loading overlay
 */
function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} fade-in`;
    alertDiv.textContent = message;

    const container = document.querySelector('.container') || document.body;
    container.insertBefore(alertDiv, container.firstChild);

    setTimeout(() => {
        alertDiv.style.opacity = '0';
        setTimeout(() => alertDiv.remove(), 300);
    }, 5000);
}

/**
 * Show error message
 */
function showError(error) {
    const message = error.message || error.detail || 'An error occurred';
    showAlert(message, 'error');
}

/**
 * Show success message
 */
function showSuccess(message) {
    showAlert(message, 'success');
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Format date
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Logout current user
 */
async function logout() {
    try {
        showLoading('Logging out...');
        await api.logout();
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_info');
        hideLoading();
        window.location.href = '/login.html';
    } catch (error) {
        hideLoading();
        console.error('Logout error:', error);
        // Force logout even if API call fails
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_info');
        window.location.href = '/login.html';
    }
}

/**
 * Update user info display in navigation
 */
async function updateUserInfo() {
    const user = getCurrentUser();
    if (!user) return null;

    const userInfoEl = document.getElementById('user-info');
    if (userInfoEl) {
        userInfoEl.textContent = user.username;
    }

    // Bind logout button
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    }

    updateAdminUI();
    return user;
}
