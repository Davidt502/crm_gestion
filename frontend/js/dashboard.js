/**
 * dashboard.js - Funcionalidad del Dashboard
 * Correcciones:
 *   - Endpoints corregidos: /api/dashboard/* → /api/clientes/*
 *   - XSS: uso de escapeHtml() en birthday-list
 *   - animateCounter: limita paso mínimo para targets=0
 *   - Manejo de errores con showToast
 */

document.addEventListener('DOMContentLoaded', () => {
    if (!requireAuth()) return;
    setCurrentDate();
    loadStats();
    loadCumpleaneros();
});

function setCurrentDate() {
    const el = document.getElementById('current-date');
    if (!el) return;
    el.textContent = new Date().toLocaleDateString('es-GT', {
        weekday: 'long',
        year:    'numeric',
        month:   'long',
        day:     'numeric',
    });
}

async function loadStats() {
    try {
        const data = await apiJSON('/api/clientes/stats');   // ← corregido
        if (!data) return;
        animateCounter('stat-activos',     data.total_activos    || 0);
        animateCounter('stat-inactivos',   data.total_inactivos  || 0);
        animateCounter('stat-prospectos',  data.total_prospectos || 0);
        animateCounter('stat-proveedores', data.proveedores_activos || 0);
    } catch (e) {
        console.error('Error cargando estadísticas:', e);
        showToast('No se pudieron cargar las estadísticas', 'error');
    }
}

function animateCounter(id, target) {
    const el = document.getElementById(id);
    if (!el) return;
    if (target === 0) { el.textContent = '0'; return; }
    let current = 0;
    const step  = Math.max(1, Math.ceil(target / 30));
    const timer = setInterval(() => {
        current = Math.min(current + step, target);
        el.textContent = current;
        if (current >= target) clearInterval(timer);
    }, 30);
}

async function loadCumpleaneros() {
    const meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio',
                   'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
    const mesActual = meses[new Date().getMonth()];

    const badge = document.getElementById('birthday-month-badge');
    if (badge) badge.textContent = mesActual;

    const container = document.getElementById('birthday-list');
    if (!container) return;

    try {
        const data = await apiJSON('/api/clientes/cumpleaneros');  // ← corregido
        if (!data) return;

        // El endpoint devuelve un array directo (no un dict con .cumpleaneros)
        const lista = Array.isArray(data) ? data : (data.cumpleaneros || []);

        if (!lista.length) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🎂</div>
                    No hay cumpleaños registrados para este mes.
                </div>`;
            return;
        }

        container.innerHTML = lista.map(c => `
            <div class="birthday-item">
                <div class="birthday-day-box">
                    <span class="birthday-day-num">${escapeHtml(String(c.dia))}</span>
                    <span class="birthday-day-mon">${escapeHtml(mesActual.slice(0, 3))}</span>
                </div>
                <div class="birthday-info">
                    <div class="birthday-name">${escapeHtml(c.nombre)}</div>
                    <div class="birthday-meta">🎈 Cumpleaños este mes</div>
                </div>
                <div class="birthday-age-pill">🎁 ${escapeHtml(String(c.edad))} años</div>
            </div>
        `).join('');
    } catch (e) {
        console.error('Error cargando cumpleañeros:', e);
        container.innerHTML = '<div class="empty-state">Error cargando información.</div>';
        showToast('No se pudieron cargar los cumpleañeros', 'error');
    }
}