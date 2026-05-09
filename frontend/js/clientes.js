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

let currentPage = 1;
let pendingInactivarId = null;

document.addEventListener('DOMContentLoaded', () => {
    if (!requireAuth()) return;
    if (document.getElementById('clientes-tbody')) {
        cargarClientes();
    }
});

/* ══════════════════════════════════════════════════════════════
   LISTADO DE CLIENTES
   ══════════════════════════════════════════════════════════════ */

async function cargarClientes(page = 1) {
    currentPage = page;
    const nombre = document.getElementById('search-nombre')?.value.trim() || '';
    const documento = document.getElementById('search-documento')?.value.trim() || '';
    const tipo = document.getElementById('search-tipo')?.value || '';

    const params = new URLSearchParams({ nombre, documento, tipo, page });
    const tbody = document.getElementById('clientes-tbody');
    tbody.innerHTML = '<tr><td colspan="5" class="loading-overlay"><div class="spinner"></div></td></tr>';

    try {
        const data = await apiJSON(`/api/clientes?${params}`);
        console.log('Datos recibidos:', data); // ⭐ Para depuración
        
        if (!data) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--danger)">Error al cargar datos</td></tr>';
            return;
        }
        
        renderTablaClientes(data);
    } catch (e) {
        console.error('Error:', e);
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--danger)">Error al cargar clientes: ' + e.message + '</td></tr>';
        showToast('Error al cargar clientes', 'error');
    }
}

function renderTablaClientes(data) {
    const tbody = document.getElementById('clientes-tbody');
    
    // ⭐ El backend puede devolver los clientes en 'data', 'clientes', o directamente un array
    let clientes = [];
    let total = 0;
    let page = 1;
    let per_page = 20;
    
    if (Array.isArray(data)) {
        // Si es un array directo
        clientes = data;
        total = data.length;
    } else if (data.data && Array.isArray(data.data)) {
        // Si viene en data.data
        clientes = data.data;
        total = data.meta?.total || data.total || clientes.length;
        page = data.meta?.page || data.page || 1;
        per_page = data.meta?.limit || data.per_page || 20;
    } else if (data.clientes && Array.isArray(data.clientes)) {
        // Si viene en data.clientes
        clientes = data.clientes;
        total = data.total || clientes.length;
        page = data.page || 1;
        per_page = data.per_page || 20;
    } else if (Array.isArray(data.rows)) {
        clientes = data.rows;
        total = data.count || clientes.length;
    } else {
        console.error('Estructura de datos no reconocida:', data);
        tbody.innerHTML = `
            <tr><td colspan="5" style="text-align:center;color:var(--danger);padding:32px;">
                Error: Estructura de datos incorrecta. Contacta al administrador.
                <br><small>${JSON.stringify(data).substring(0, 200)}</small>
            </td></tr>`;
        return;
    }

    if (!clientes.length) {
        tbody.innerHTML = `
            <tr><td colspan="5" class="empty-state" style="padding:32px;">
                <div class="empty-state-icon">👥</div>
                No se encontraron clientes con los criterios de búsqueda.
            </td></tr>`;
        document.getElementById('pagination-clientes').style.display = 'none';
        return;
    }

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
    const end = Math.min(totalPages, page + 2);
    for (let i = start; i <= end; i++) addBtn(i, i, false, i === page);
    addBtn('›', page + 1, page === totalPages);
}

function buscarClientes() { cargarClientes(1); }

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

// ⭐ Resto del código para formulario (se ejecuta solo si existe CLIENTE_ID)
const TIPOS_CLIENTE = ['Cliente', 'Prospecto'];

if (typeof CLIENTE_ID !== 'undefined') {
    document.addEventListener('DOMContentLoaded', async () => {
        if (!requireAuth()) return;
        cargarTipos();
        if (CLIENTE_ID) {
            document.getElementById('form-title').textContent = 'Editar Cliente';
            document.getElementById('form-breadcrumb').textContent = 'Editar';
            await cargarDatosCliente(CLIENTE_ID);
        }
    });
}

function cargarTipos() {
    const sel = document.getElementById('tipo');
    if (!sel) return;
    sel.innerHTML = '<option value="">Seleccione un tipo</option>';
    TIPOS_CLIENTE.forEach(t => {
        const o = document.createElement('option');
        o.value = t;
        o.textContent = t;
        sel.appendChild(o);
    });
}

async function cargarDatosCliente(id) {
    try {
        const resp = await apiJSON(`/api/clientes/${id}`);
        if (!resp) return;

        const c = resp.id_cliente ? resp : (resp.cliente || resp);

        const setVal = (elId, val) => {
            const el = document.getElementById(elId);
            if (el) el.value = val ?? '';
        };

        setVal('nombre_razon_social', c.nombre_razon_social);
        setVal('documento_identificacion', c.documento_identificacion);
        setVal('fecha_nacimiento', c.fecha_nacimiento);
        setVal('correo', c.correo);
        setVal('tipo', c.tipo);

        if (Array.isArray(c.contactos) && c.contactos.length) {
            c.contactos.forEach(ct => agregarContacto(ct));
        }
    } catch (e) {
        showToast('Error al cargar los datos del cliente.', 'error');
    }
}

// Gestión de contactos
let contactoIndex = 0;
const contactos = [];

function agregarContacto(datos = {}) {
    const idx = contactoIndex++;
    const wrap = document.getElementById('contactos-container');
    const empty = document.getElementById('contactos-empty');
    if (empty) empty.style.display = 'none';

    const nombre = datos.nombre_contacto || datos.nombre || '';
    const telefono = datos.telefono || '';
    const email = datos.correo || datos.email || '';
    const idContacto = datos.id_contacto || '';

    const card = document.createElement('div');
    card.className = 'contacto-card';
    card.id = `contacto-${idx}`;
    card.innerHTML = `
        <div class="form-group">
            <label>Nombre</label>
            <input type="text" id="ct-nombre-${idx}"
                   value="${escapeHtml(nombre)}"
                   placeholder="Nombre del contacto"
                   data-id="${escapeHtml(String(idContacto))}">
        </div>
        <div class="form-group">
            <label>Teléfono</label>
            <input type="text" id="ct-telefono-${idx}"
                   value="${escapeHtml(telefono)}"
                   placeholder="Teléfono">
        </div>
        <div class="form-group">
            <label>Email</label>
            <input type="email" id="ct-email-${idx}"
                   value="${escapeHtml(email)}"
                   placeholder="correo@ejemplo.com">
        </div>
        <button type="button" class="btn btn-danger btn-sm btn-icon btn-remove"
                title="Eliminar" onclick="eliminarContacto(${idx})">✕</button>
    `;
    wrap.appendChild(card);
    contactos.push(idx);
}

function eliminarContacto(idx) {
    document.getElementById(`contacto-${idx}`)?.remove();
    const i = contactos.indexOf(idx);
    if (i !== -1) contactos.splice(i, 1);
    if (!contactos.length) {
        const empty = document.getElementById('contactos-empty');
        if (empty) empty.style.display = '';
    }
}

function recopilarContactos() {
    return contactos.map(idx => {
        const nombreEl = document.getElementById(`ct-nombre-${idx}`);
        const nombre = nombreEl?.value.trim() || '';
        const telefono = document.getElementById(`ct-telefono-${idx}`)?.value.trim() || '';
        const correo = document.getElementById(`ct-email-${idx}`)?.value.trim() || '';
        const idContacto = nombreEl?.dataset.id ? parseInt(nombreEl.dataset.id) : null;

        return {
            ...(idContacto ? { id_contacto: idContacto } : {}),
            nombre_contacto: nombre,
            tipo_contacto: 'Teléfono',
            descripcion: nombre,
            telefono,
            correo,
        };
    }).filter(c => c.nombre_contacto || c.telefono || c.correo);
}

function cambiarTab(tab) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.form-tab').forEach(el => el.classList.remove('active'));
    document.getElementById(`tab-${tab}`)?.classList.add('active');
    document.querySelector(`[data-tab="${tab}"]`)?.classList.add('active');
}

function mostrarError(id, msg) {
    const el = document.getElementById(`error-${id}`);
    if (!el) return;
    el.textContent = msg;
    el.style.display = msg ? '' : 'none';
    const input = document.getElementById(id) || document.getElementById(`${id}_razon_social`);
    if (input) input.classList.toggle('input-error', !!msg);
}

async function guardarCliente() {
    const nombre = document.getElementById('nombre_razon_social')?.value.trim();
    const doc = document.getElementById('documento_identificacion')?.value.trim();
    const tipo = document.getElementById('tipo')?.value;
    const correo = document.getElementById('correo')?.value.trim() || null;

    mostrarError('nombre', nombre ? '' : 'El nombre es obligatorio.');
    mostrarError('documento', doc ? '' : 'El documento es obligatorio.');
    mostrarError('tipo', tipo ? '' : 'Selecciona un tipo.');

    if (!nombre || !doc || !tipo) return;

    const payload = {
        nombre_razon_social: nombre,
        documento_identificacion: doc,
        fecha_nacimiento: document.getElementById('fecha_nacimiento')?.value || null,
        correo,
        tipo,
        contactos: recopilarContactos(),
    };

    const btn = document.getElementById('btn-guardar');
    btn.disabled = true;
    btn.textContent = 'Guardando...';

    try {
        const isEdit = typeof CLIENTE_ID !== 'undefined' && CLIENTE_ID;
        const url = isEdit ? `/api/clientes/${CLIENTE_ID}` : '/api/clientes';
        const method = isEdit ? 'PUT' : 'POST';
        const data = await apiJSON(url, { method, body: JSON.stringify(payload) });
        if (!data) return;

        showToast(data.mensaje || 'Cliente guardado exitosamente.', 'success');
        setTimeout(() => { window.location.href = '/clientes.html'; }, 1200);
    } catch (e) {
        showToast(e.message || 'Error al guardar el cliente.', 'error');
        btn.disabled = false;
        btn.textContent = '💾 Guardar';
    }
}
