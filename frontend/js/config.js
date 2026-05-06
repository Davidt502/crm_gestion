/**
 * config.js - Configuración del Frontend
 * Correcciones:
 *   - escapeHtml() para prevenir XSS al insertar contenido dinámico en el DOM
 *   - apiFetch maneja correctamente respuestas no-JSON (evita crash)
 *   - Logout limpia estado de forma segura
 */

const CONFIG = {
    API_BASE_URL: 'http://localhost:5000',
    TOKEN_KEY:    'crm_auth_token',
    USER_KEY:     'crm_user',
};

// ── Seguridad: escape de HTML para prevenir XSS ─────────────
/**
 * Escapa caracteres HTML especiales antes de insertar texto en el DOM.
 * USA SIEMPRE esta función al insertar datos del servidor o del usuario
 * en innerHTML / insertAdjacentHTML.
 * @param {string} str
 * @returns {string}
 */
function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g,  '&amp;')
        .replace(/</g,  '&lt;')
        .replace(/>/g,  '&gt;')
        .replace(/"/g,  '&quot;')
        .replace(/'/g,  '&#39;');
}

// ── Gestión de sesión ────────────────────────────────────────
function getToken()  { return localStorage.getItem(CONFIG.TOKEN_KEY); }
function setToken(t) { localStorage.setItem(CONFIG.TOKEN_KEY, t); }

function getUser() {
    try {
        const raw = localStorage.getItem(CONFIG.USER_KEY);
        return raw ? JSON.parse(raw) : null;
    } catch { return null; }
}
function setUser(u)  { localStorage.setItem(CONFIG.USER_KEY, JSON.stringify(u)); }

function clearSession() {
    localStorage.removeItem(CONFIG.TOKEN_KEY);
    localStorage.removeItem(CONFIG.USER_KEY);
}

function isAuthenticated() { return !!getToken(); }

function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/login.html';
        return false;
    }
    return true;
}

function logout() {
    clearSession();
    window.location.href = '/login.html';
}

// ── API Fetch con autenticación ──────────────────────────────
/**
 * Realiza una petición al backend con el token JWT adjunto.
 * Redirige al login si el servidor responde 401.
 * @param {string} endpoint - Ruta relativa, e.g. '/api/clientes'
 * @param {RequestInit} options - Opciones fetch
 * @returns {Promise<Response|null>}
 */
async function apiFetch(endpoint, options = {}) {
    const url   = `${CONFIG.API_BASE_URL}${endpoint}`;
    const token = getToken();

    const headers = {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...options.headers,
    };

    try {
        const response = await fetch(url, { ...options, headers });

        if (response.status === 401) {
            clearSession();
            window.location.href = '/login.html';
            return null;
        }

        return response;
    } catch (err) {
        console.error(`[apiFetch] Error en ${endpoint}:`, err);
        throw err;
    }
}

/**
 * Versión conveniente que parsea el JSON directamente.
 * Lanza un Error con el mensaje del servidor si la respuesta no es ok.
 * @param {string} endpoint
 * @param {RequestInit} options
 * @returns {Promise<any>}
 */
async function apiJSON(endpoint, options = {}) {
    const res = await apiFetch(endpoint, options);
    if (!res) return null;

    // Intentar parsear siempre como JSON, incluso en errores
    let data;
    try {
        data = await res.json();
    } catch {
        if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
        return null;
    }

    if (!res.ok) {
        throw new Error(data?.error || `Error ${res.status}`);
    }
    return data;
}

// ── Toast / notificaciones ───────────────────────────────────
/**
 * Muestra una notificación tipo toast.
 * @param {string} message - Texto del mensaje (se escapa automáticamente)
 * @param {'success'|'error'|'warning'|'info'} type
 * @param {number} duration - Duración en ms (default 3500)
 */
function showToast(message, type = 'info', duration = 3500) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    // textContent en lugar de innerHTML para el mensaje → sin riesgo XSS
    toast.innerHTML = `<span class="toast-icon">${icons[type] || 'ℹ️'}</span>`;
    const msgSpan = document.createElement('span');
    msgSpan.textContent = message;
    toast.appendChild(msgSpan);

    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('toast-show'));

    setTimeout(() => {
        toast.classList.remove('toast-show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}
