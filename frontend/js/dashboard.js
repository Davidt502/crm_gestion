/**
 * dashboard.js - Dashboard principal
 * Correcciones:
 *   - Carga estadísticas completas (clientes, empleados, compras) desde /api/dashboard/stats
 *   - Muestra tarjetas de empleados y compras adicionales
 *   - Manejo de errores mejorado por sección independiente
 */

function mostrarFechaActual() {
    const fechaEl = document.getElementById('current-date');
    if (fechaEl) {
        const opciones = { year: 'numeric', month: 'long', day: 'numeric' };
        fechaEl.textContent = new Date().toLocaleDateString('es-ES', opciones);
    }
}

function setStatText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

async function cargarEstadisticas() {
    try {
        // Usar /api/dashboard/stats que consolida clientes + empleados + compras
        const data = await apiJSON('/api/dashboard/stats');
        if (!data) return;

        // ── Clientes ──────────────────────────────────────────
        setStatText('stat-activos',     data.clientes_activos   ?? 0);
        setStatText('stat-inactivos',   data.clientes_inactivos ?? 0);
        setStatText('stat-prospectos',  data.prospectos         ?? 0);
        setStatText('stat-proveedores', data.proveedores_activos ?? 0);

        // ── Empleados ─────────────────────────────────────────
        setStatText('stat-empleados-activos',   data.activos      ?? 0);
        setStatText('stat-empleados-inactivos', data.inactivos    ?? 0);
        setStatText('stat-dependencias',        data.dependencias ?? 0);

        // ── Compras ───────────────────────────────────────────
        setStatText('stat-total-compras',  data.total_compras ?? 0);
        setStatText('stat-compras-pend',   data.pendientes    ?? 0);
        setStatText('stat-compras-pag',    data.pagadas       ?? 0);

        const monto = parseFloat(data.monto_total ?? 0);
        setStatText('stat-monto-compras',
            'Q' + monto.toLocaleString('es-GT', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
        );

    } catch (error) {
        console.error('Error cargando estadísticas:', error);
        // Fallback: intentar endpoint de clientes individualmente
        try {
            const d = await apiJSON('/api/clientes/stats');
            if (d) {
                setStatText('stat-activos',     d.clientes_activos   ?? 0);
                setStatText('stat-inactivos',   d.clientes_inactivos ?? 0);
                setStatText('stat-prospectos',  d.prospectos         ?? 0);
                setStatText('stat-proveedores', d.proveedores_activos ?? 0);
            }
        } catch (e) {
            console.error('Fallback stats también falló:', e);
        }
    }
}

function getNombreMes() {
    const meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                   'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
    return meses[new Date().getMonth()];
}

function getAbreviaturaMes() {
    const meses = ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN',
                   'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC'];
    return meses[new Date().getMonth()];
}

function birthdayCard(persona) {
    const esHoy = persona.dia === new Date().getDate();
    return `
        <div class="birthday-item">
            <div class="birthday-day-box">
                <div class="birthday-day-num">${persona.dia}</div>
                <div class="birthday-day-mon">${getAbreviaturaMes()}</div>
            </div>
            <div class="birthday-info">
                <div class="birthday-name">${escapeHtml(persona.nombre)}</div>
                <div class="birthday-meta">${esHoy ? '🎉' : '🎂'} ${escapeHtml(persona.tipo)}</div>
            </div>
            <div class="birthday-age-pill">${persona.edad} años</div>
        </div>`;
}

async function cargarCumpleaños() {
    const container = document.getElementById('birthday-list');
    const monthBadge = document.getElementById('birthday-month-badge');

    if (monthBadge) monthBadge.textContent = getNombreMes();
    if (!container) return;

    try {
        const data = await apiJSON('/api/clientes/cumpleaneros');

        if (!data || data.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🎂</div>
                    <div>No hay cumpleaños este mes</div>
                </div>`;
            return;
        }

        const clientes   = data.filter(p => p.tipo === 'Cliente');
        const prospectos = data.filter(p => p.tipo === 'Prospecto');
        let html = '';

        if (clientes.length > 0) {
            html += `
                <div style="padding:8px 16px 0 16px;">
                    <div style="font-size:0.7rem;text-transform:uppercase;color:var(--gold);font-weight:700;letter-spacing:1px;">
                        👥 CLIENTES (${clientes.length})
                    </div>
                </div>`;
            html += clientes.map(p => birthdayCard(p)).join('');
        }

        if (prospectos.length > 0) {
            html += `
                <div style="padding:16px 16px 0 16px;margin-top:8px;">
                    <div style="font-size:0.7rem;text-transform:uppercase;color:var(--warning);font-weight:700;letter-spacing:1px;">
                        🎯 PROSPECTOS (${prospectos.length})
                    </div>
                </div>`;
            html += prospectos.map(p => birthdayCard(p)).join('');
        }

        container.innerHTML = html;

    } catch (error) {
        console.error('Error cargando cumpleaños:', error);
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚠️</div>
                <div>Error al cargar cumpleaños</div>
            </div>`;
    }
}

async function recargarDashboard() {
    await Promise.all([
        cargarEstadisticas(),
        cargarCumpleaños(),
    ]);
}

document.addEventListener('DOMContentLoaded', () => {
    if (!requireAuth()) return;
    mostrarFechaActual();
    recargarDashboard();
    setInterval(recargarDashboard, 300000);
});