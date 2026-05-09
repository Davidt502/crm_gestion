/**
 * dashboard.js - Dashboard principal
 */

function mostrarFechaActual() {
    const fechaEl = document.getElementById('current-date');
    if (fechaEl) {
        const opciones = { year: 'numeric', month: 'long', day: 'numeric' };
        fechaEl.textContent = new Date().toLocaleDateString('es-ES', opciones);
    }
}

async function cargarEstadisticas() {
    try {
        // ⭐ Usar el endpoint correcto /api/clientes/stats ⭐
        const data = await apiJSON('/api/clientes/stats');
        if (data) {
            document.getElementById('stat-activos').textContent = data.clientes_activos || 0;
            document.getElementById('stat-inactivos').textContent = data.clientes_inactivos || 0;
            document.getElementById('stat-prospectos').textContent = data.prospectos || 0;
            document.getElementById('stat-proveedores').textContent = data.proveedores_activos || 0;
        }
    } catch (error) {
        console.error('Error cargando estadísticas:', error);
        showToast('Error al cargar estadísticas', 'error');
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

async function cargarCumpleaños() {
    const container = document.getElementById('birthday-list');
    const monthBadge = document.getElementById('birthday-month-badge');
    
    if (monthBadge) {
        monthBadge.textContent = getNombreMes();
    }
    
    try {
        const data = await apiJSON('/api/clientes/cumpleaneros');
        
        if (!data || data.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🎂</div>
                    <div>No hay cumpleaños este mes</div>
                </div>
            `;
            return;
        }
        
        // Separar Clientes y Prospectos
        const clientes = data.filter(p => p.tipo === 'Cliente');
        const prospectos = data.filter(p => p.tipo === 'Prospecto');
        
        let html = '';
        
        if (clientes.length > 0) {
            html += `
                <div style="padding: 8px 16px 0 16px;">
                    <div style="font-size: 0.7rem; text-transform: uppercase; color: var(--gold); font-weight: 700; letter-spacing: 1px;">
                        👥 CLIENTES (${clientes.length})
                    </div>
                </div>
            `;
            html += clientes.map(persona => `
                <div class="birthday-item">
                    <div class="birthday-day-box">
                        <div class="birthday-day-num">${persona.dia}</div>
                        <div class="birthday-day-mon">${getAbreviaturaMes()}</div>
                    </div>
                    <div class="birthday-info">
                        <div class="birthday-name">${escapeHtml(persona.nombre)}</div>
                        <div class="birthday-meta">🎂 Cliente</div>
                    </div>
                    <div class="birthday-age-pill">${persona.edad} años</div>
                </div>
            `).join('');
        }
        
        if (prospectos.length > 0) {
            html += `
                <div style="padding: 16px 16px 0 16px; margin-top: 8px;">
                    <div style="font-size: 0.7rem; text-transform: uppercase; color: var(--warning); font-weight: 700; letter-spacing: 1px;">
                        🎯 PROSPECTOS (${prospectos.length})
                    </div>
                </div>
            `;
            html += prospectos.map(persona => `
                <div class="birthday-item">
                    <div class="birthday-day-box">
                        <div class="birthday-day-num">${persona.dia}</div>
                        <div class="birthday-day-mon">${getAbreviaturaMes()}</div>
                    </div>
                    <div class="birthday-info">
                        <div class="birthday-name">${escapeHtml(persona.nombre)}</div>
                        <div class="birthday-meta">🎯 Prospecto</div>
                    </div>
                    <div class="birthday-age-pill">${persona.edad} años</div>
                </div>
            `).join('');
        }
        
        container.innerHTML = html;
        
    } catch (error) {
        console.error('Error cargando cumpleaños:', error);
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚠️</div>
                <div>Error al cargar cumpleaños</div>
            </div>
        `;
    }
}

async function recargarDashboard() {
    await Promise.all([
        cargarEstadisticas(),
        cargarCumpleaños()
    ]);
}

document.addEventListener('DOMContentLoaded', () => {
    if (!requireAuth()) return;
    mostrarFechaActual();
    recargarDashboard();
    setInterval(() => {
        cargarEstadisticas();
        cargarCumpleaños();
    }, 300000);
});