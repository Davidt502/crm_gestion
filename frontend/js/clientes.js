/**
 * clientes.js - Gestión de Clientes
 * Correcciones:
 *   - XSS: escapeHtml() en todos los datos insertados en innerHTML
 *   - showToast movido a config.js (eliminada definición duplicada)
 *   - renderPaginacion usa textContent para el texto de info
 *   - inactivar usa apiJSON en lugar de apiFetch manual
 */

function cerrarModal(id) { document.getElementById(id)?.classList.remove('open'); }
function abrirModal(id)  { document.getElementById(id)?.classList.add('open'); }

let currentPage      = 1;
let pendingInactivarId = null;

document.addEventListener('DOMContentLoaded', () => {
    if (!requireAuth()) return;
    if (document.getElementById('clientes-tbody')) {
        cargarClientes();
    }
});

async function cargarClientes(page = 1) {
    currentPage = page;
    const nombre    = document.getElementById('search-nombre')?.value.trim()  || '';
    const documento = document.getElementById('search-documento')?.value.trim()|| '';
    const tipo      = document.getElementById('search-tipo')?.value            || '';

    const params = new URLSearchParams({ nombre, documento, tipo, page });
    const tbody  = document.getElementById('clientes-tbody');
    tbody.innerHTML = '<tr><td colspan="5" class="loading-overlay"><div class="spinner"></div></td></tr>';

    try {
        const data = await apiJSON(`/api/clientes?${params}`);
        if (!data) return;
        renderTablaClientes(data);
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--danger)">Error al cargar datos.</td></tr>';
        showToast('Error al cargar clientes', 'error');
    }
}

function renderTablaClientes(data) {
    const tbody = document.getElementById('clientes-tbody');
    const { clientes = [], total = 0, page = 1, per_page = 20 } = data;

    if (!clientes.length) {
        tbody.innerHTML = `
            <tr><td colspan="5" class="empty-state" style="padding:32px;">
                <div class="empty-state-icon">👥</div>
                No se encontraron clientes con los criterios de búsqueda.
            </td></tr>`;
        document.getElementById('pagination-clientes').style.display = 'none';
        return;
    }

    // ✅ escapeHtml() en cada campo de datos del servidor
    tbody.innerHTML = clientes.map(c => `
        <tr>
            <td><strong>${escapeHtml(c.nombre_razon_social)}</strong></td>
            <td>${escapeHtml(c.documento_identificacion)}</td>
            <td><span class="badge badge-${c.tipo === 'Cliente' ? 'cliente' : 'prospecto'}">${escapeHtml(c.tipo)}</span></td>
            <td><span class="badge badge-${c.estado === 'Activo' ? 'active' : 'inactive'}">${escapeHtml(c.estado)}</span></td>
            <td>
                <div class="td-actions">
                    <a href="/form_cliente.html?id=${encodeURIComponent(c.id_cliente)}"
                       class="btn btn-ghost btn-sm btn-icon" title="Editar">✏️</a>
                    ${c.estado === 'Activo'
                        ? `<button class="btn btn-danger btn-sm btn-icon"
                                   data-id="${encodeURIComponent(c.id_cliente)}"
                                   onclick="inactivarCliente(this.dataset.id)"
                                   title="Inactivar">🚫</button>`
                        : `<span style="font-size:0.75rem;color:var(--text2)">Inactivo</span>`
                    }
                </div>
            </td>
        </tr>
    `).join('');

    renderPaginacion(total, page, per_page, 'pagination-clientes', 'pag-info', 'pag-controls', cargarClientes);
}

function renderPaginacion(total, page, per_page, wrapId, infoId, ctrlId, fn) {
    const totalPages = Math.ceil(total / per_page) || 1;
    const wrap = document.getElementById(wrapId);
    if (!wrap) return;
    wrap.style.display = 'flex';

    const desde = (page - 1) * per_page + 1;
    const hasta = Math.min(page * per_page, total);
    // textContent en vez de innerHTML → seguro
    const infoEl = document.getElementById(infoId);
    if (infoEl) infoEl.textContent = `Mostrando ${desde}–${hasta} de ${total} registros`;

    const ctrl = document.getElementById(ctrlId);
    if (!ctrl) return;
    ctrl.innerHTML = '';

    const addBtn = (label, pg, disabled = false, active = false) => {
        const b = document.createElement('button');
        b.className = `page-btn${active ? ' active' : ''}`;
        b.textContent = label;
        b.disabled = disabled;
        if (!disabled) b.addEventListener('click', () => fn(pg));
        ctrl.appendChild(b);
    };

    addBtn('‹', page - 1, page === 1);
    const start = Math.max(1, page - 2);
    const end   = Math.min(totalPages, page + 2);
    for (let i = start; i <= end; i++) addBtn(i, i, false, i === page);
    addBtn('›', page + 1, page === totalPages);
}

function buscarClientes()  { cargarClientes(1); }

function limpiarBusqueda() {
    ['search-nombre', 'search-documento'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    const tipoEl = document.getElementById('search-tipo');
    if (tipoEl) tipoEl.value = '';
    cargarClientes(1);
}

function inactivarCliente(id) {
    pendingInactivarId = id;
    abrirModal('modal-inactivar');
}

async function confirmarInactivar() {
    if (!pendingInactivarId) return;
    try {
        const data = await apiJSON(`/api/clientes/${pendingInactivarId}/inactivar`, { method: 'PATCH' });
        if (!data) return;
        showToast(data.mensaje || 'Cliente inactivado.', 'success');
        cerrarModal('modal-inactivar');
        cargarClientes(currentPage);
    } catch (e) {
        showToast(e.message || 'Error al inactivar el cliente.', 'error');
    }
    pendingInactivarId = null;
}
