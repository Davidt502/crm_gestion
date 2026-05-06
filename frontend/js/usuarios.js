// usuarios.js — CRM Ing Software v3
// Módulo de Gestión de Usuarios (solo admins)

function cerrarModal(id) { document.getElementById(id)?.classList.remove('open'); }
function abrirModal(id)  { document.getElementById(id)?.classList.add('open'); }

function getHeaders(includeContentType = true) {
  const headers = { 'Authorization': `Bearer ${getToken()}` };
  if (includeContentType) headers['Content-Type'] = 'application/json';
  return headers;
}

/* ═══════════════════════════════════════════
   LISTA DE USUARIOS
═══════════════════════════════════════════ */
const isLista = !!document.getElementById('usuarios-tbody');
const isForm  = !!document.getElementById('campo-nombre') && !document.getElementById('usuarios-tbody');

let pendingDesactivarId = null;
let pendingReactivarId  = null;

if (isLista) {
  document.addEventListener('DOMContentLoaded', () => {
    if (!requireAuth()) return;
    verificarAdmin();
    cargar();
  });
}

// Redirigir si no es admin
function verificarAdmin() {
  const user = getUser();
  if (!user || user.rol !== 'admin') {
    showToast('Acceso denegado. Solo administradores pueden gestionar usuarios.', 'error');
    setTimeout(() => { window.location.href = '/dashboard.html'; }, 1800);
  }
}

async function cargar(page = 1) {
  const busqueda = document.getElementById('search-nombre')?.value.trim() || '';
  const estado   = document.getElementById('search-estado')?.value || '';
  const tbody    = document.getElementById('usuarios-tbody');
  tbody.innerHTML = '<tr><td colspan="6" class="loading-overlay"><div class="spinner"></div></td></tr>';

  try {
    const p = new URLSearchParams({ page });
    if (busqueda) p.set('nombre', busqueda);
    if (estado)   p.set('estado', estado);

    const res = await fetch(`${CONFIG.API_BASE_URL}/api/usuarios?${p}`, {
      headers: getHeaders(false)
    });

    if (res.status === 403) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--danger);padding:24px;">Acceso denegado. Se requiere rol de administrador.</td></tr>';
      return;
    }

    const data = await res.json();
    if (data.error) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--danger);padding:24px;">${escapeHtml(data.error)}</td></tr>`;
      return;
    }
    renderTabla(data.usuarios || [], data.total || 0, page, data.per_page || 20);

  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--danger);padding:24px;">Error al conectar con el servidor.</td></tr>';
  }
}

function renderTabla(items, total, page, per_page) {
  const tbody = document.getElementById('usuarios-tbody');
  const pag   = document.getElementById('paginacion');

  if (!items.length) {
    tbody.innerHTML = `
      <tr><td colspan="6">
        <div style="text-align:center;padding:60px 24px;">
          <div style="font-size:3.5rem;margin-bottom:14px;">👤</div>
          <div style="font-weight:700;font-size:1rem;color:#1e293b;margin-bottom:8px;">Sin usuarios registrados</div>
          <div style="font-size:.85rem;color:#64748b;">Haz clic en <strong>＋ Nuevo Usuario</strong> para agregar uno.</div>
        </div>
      </td></tr>`;
    pag.style.display = 'none';
    return;
  }

  const currentUser = getUser();

  tbody.innerHTML = items.map(u => {
    const esMismo = currentUser && currentUser.username === u.username;
    const badgeRol = u.rol === 'admin'
      ? '<span class="badge badge-cliente">Admin</span>'
      : '<span class="badge" style="background:rgba(100,116,139,.12);color:#475569;border:1px solid rgba(100,116,139,.25);">Usuario</span>';
    const badgeEstado = u.estado === 'Activo'
      ? '<span class="badge badge-active">Activo</span>'
      : '<span class="badge badge-inactive">Inactivo</span>';

    const btnDesactivar = u.estado === 'Activo' && !esMismo
      ? `<button class="btn btn-warning btn-sm" data-id="${u.id_usuario}" onclick="abrirDesactivar(this.dataset.id)" title="Desactivar">🚫</button>`
      : '';
    const btnReactivar = u.estado === 'Inactivo'
      ? `<button class="btn btn-ghost btn-sm" data-id="${u.id_usuario}" onclick="abrirReactivar(this.dataset.id)" title="Reactivar">✅</button>`
      : '';

    return `
      <tr>
        <td><strong>${escapeHtml(u.nombre)}</strong></td>
        <td><code style="font-size:.82rem;">${escapeHtml(u.username)}</code></td>
        <td>${escapeHtml(u.email || '—')}</td>
        <td>${badgeRol}</td>
        <td>${badgeEstado}</td>
        <td class="td-actions">
          <a href="/form_usuario.html?id=${u.id_usuario}" class="btn btn-ghost btn-sm btn-icon" title="Editar">✏️</a>
          ${btnDesactivar}
          ${btnReactivar}
        </td>
      </tr>`;
  }).join('');

  pag.style.display = 'flex';
  const desde = (page - 1) * per_page + 1;
  const hasta = Math.min(page * per_page, total);
  document.getElementById('pag-info').textContent = `Mostrando ${desde}–${hasta} de ${total}`;

  const ctrl  = document.getElementById('pag-controls');
  ctrl.innerHTML = '';
  const pages = Math.ceil(total / per_page);
  const mkBtn = (lbl, p, active, disabled) => {
    const b = document.createElement('button');
    b.className = 'page-btn' + (active ? ' active' : '');
    b.textContent = lbl;
    b.disabled = disabled;
    if (!disabled) b.onclick = () => cargar(p);
    return b;
  };
  ctrl.appendChild(mkBtn('‹', page - 1, false, page <= 1));
  for (let i = Math.max(1, page - 2); i <= Math.min(pages, page + 2); i++)
    ctrl.appendChild(mkBtn(i, i, i === page, false));
  ctrl.appendChild(mkBtn('›', page + 1, false, page >= pages));
}

function buscar() { cargar(1); }
function limpiar() {
  document.getElementById('search-nombre').value = '';
  document.getElementById('search-estado').value = '';
  cargar(1);
}

/* ── Desactivar ─────────────────────────────────────────────── */
function abrirDesactivar(id) {
  pendingDesactivarId = id;
  abrirModal('modal-desactivar');
}

async function confirmarDesactivar() {
  const btn = document.querySelector('#modal-desactivar .btn-danger');
  btn.disabled = true;
  btn.textContent = 'Desactivando...';
  try {
    const res = await fetch(`${CONFIG.API_BASE_URL}/api/usuarios/${pendingDesactivarId}/desactivar`, {
      method: 'PATCH',
      headers: getHeaders(false)
    });
    const d = await res.json();
    cerrarModal('modal-desactivar');
    if (d.error) { showToast(d.error, 'error'); return; }
    showToast(d.mensaje || 'Usuario desactivado correctamente.', 'success');
    cargar(1);
  } catch (e) {
    showToast('Error al desactivar el usuario. Intenta de nuevo.', 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Desactivar';
  }
}

/* ── Reactivar ──────────────────────────────────────────────── */
function abrirReactivar(id) {
  pendingReactivarId = id;
  abrirModal('modal-reactivar');
}

async function confirmarReactivar() {
  const btn = document.querySelector('#modal-reactivar .btn-gold');
  btn.disabled = true;
  btn.textContent = 'Reactivando...';
  try {
    const res = await fetch(`${CONFIG.API_BASE_URL}/api/usuarios/${pendingReactivarId}/reactivar`, {
      method: 'PATCH',
      headers: getHeaders(false)
    });
    const d = await res.json();
    cerrarModal('modal-reactivar');
    if (d.error) { showToast(d.error, 'error'); return; }
    showToast(d.mensaje || 'Usuario reactivado correctamente.', 'success');
    cargar(1);
  } catch (e) {
    showToast('Error al reactivar el usuario. Intenta de nuevo.', 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Reactivar';
  }
}

/* ═══════════════════════════════════════════
   FORMULARIO (crear / editar)
═══════════════════════════════════════════ */
let USUARIO_ID = null;

if (isForm) {
  document.addEventListener('DOMContentLoaded', async () => {
    if (!requireAuth()) return;
    verificarAdmin();
    const params = new URLSearchParams(window.location.search);
    USUARIO_ID = params.get('id') ? parseInt(params.get('id')) : null;

    if (USUARIO_ID) {
      cargarDatos(USUARIO_ID);
    } else {
      // Nuevo usuario: mostrar campo de contraseña como obligatorio
      document.getElementById('section-password').style.display = 'block';
      document.getElementById('lbl-password').textContent = 'Contraseña *';
    }
  });
}

async function cargarDatos(id) {
  try {
    const res = await fetch(`${CONFIG.API_BASE_URL}/api/usuarios/${id}`, {
      headers: getHeaders(false)
    });
    const d = await res.json();
    if (d.error) { showToast(d.error, 'error'); return; }

    document.getElementById('form-title').textContent = 'Editar Usuario';
    document.getElementById('form-breadcrumb').textContent = 'Editar';
    document.getElementById('campo-nombre').value    = d.nombre    || '';
    document.getElementById('campo-email').value     = d.email     || '';
    document.getElementById('campo-username').value  = d.username  || '';
    document.getElementById('campo-username').disabled = true; // username no editable
    document.getElementById('campo-rol').value       = d.rol       || 'usuario';

    // En edición: contraseña es opcional
    document.getElementById('section-password').style.display = 'block';
    document.getElementById('lbl-password').textContent = 'Nueva Contraseña (dejar en blanco para no cambiar)';
  } catch (e) {
    showToast('Error al cargar los datos del usuario.', 'error');
  }
}

async function guardar() {
  const nombre   = document.getElementById('campo-nombre').value.trim();
  const email    = document.getElementById('campo-email').value.trim();
  const username = document.getElementById('campo-username').value.trim();
  const rol      = document.getElementById('campo-rol').value;
  const password = document.getElementById('campo-password')?.value || '';

  const isEdit = !!USUARIO_ID;

  // Validaciones
  if (!nombre)          { showToast('El nombre es obligatorio.', 'error'); return; }
  if (!isEdit && !username) { showToast('El nombre de usuario es obligatorio.', 'error'); return; }
  if (!isEdit && !password) { showToast('La contraseña es obligatoria.', 'error'); return; }
  if (password && password.length < 6) {
    showToast('La contraseña debe tener al menos 6 caracteres.', 'error');
    return;
  }

  const btn = document.querySelector('.btn-gold');
  btn.disabled = true;
  btn.textContent = 'Guardando...';

  try {
    let res;
    if (isEdit) {
      // 1. Actualizar datos
      res = await fetch(`${CONFIG.API_BASE_URL}/api/usuarios/${USUARIO_ID}`, {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify({ nombre, email: email || null, rol })
      });
      const d = await res.json();
      if (d.error) { showToast(d.error, 'error'); return; }

      // 2. Cambiar contraseña solo si se ingresó una nueva
      if (password) {
        const resPwd = await fetch(`${CONFIG.API_BASE_URL}/api/usuarios/${USUARIO_ID}/password`, {
          method: 'PATCH',
          headers: getHeaders(),
          body: JSON.stringify({ password })
        });
        const dPwd = await resPwd.json();
        if (dPwd.error) { showToast(dPwd.error, 'error'); return; }
      }

      showToast(d.mensaje || 'Usuario actualizado correctamente.', 'success');

    } else {
      // Crear usuario nuevo
      res = await fetch(`${CONFIG.API_BASE_URL}/api/usuarios`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ nombre, email: email || null, username, password, rol })
      });
      const d = await res.json();
      if (d.error) { showToast(d.error, 'error'); return; }
      showToast(d.mensaje || 'Usuario creado correctamente.', 'success');
    }

    setTimeout(() => { window.location.href = '/usuarios.html'; }, 1200);

  } catch (e) {
    showToast('Error al guardar. Intenta de nuevo.', 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '💾 Guardar';
  }
}
