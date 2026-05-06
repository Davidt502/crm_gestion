// compras.js — CRM Ing Software v3


function cerrarModal(id){ document.getElementById(id)?.classList.remove('open'); }
function abrirModal(id){ document.getElementById(id)?.classList.add('open'); }

function getHeaders(includeContentType = true) {
  const headers = { 'Authorization': `Bearer ${getToken()}` };
  if (includeContentType) headers['Content-Type'] = 'application/json';
  return headers;
}

const isLista = !!document.getElementById('tbody');
const isForm  = !!document.getElementById('id_proveedor') && !document.getElementById('tbody');

/* ═══════════════════════ LISTA ═══════════════════════════════ */
if (isLista) {
  document.addEventListener('DOMContentLoaded', () => {
    if (!requireAuth()) return;
    cargarStats();
    cargar();
  });
}

async function cargarStats() {
  try {
    const res = await fetch(`${CONFIG.API_BASE_URL}/api/dashboard/stats`, {
      headers: getHeaders(false)
    });
    const d = await res.json();
    document.getElementById('st-total').textContent = d.total_compras ?? 0;
    document.getElementById('st-monto').textContent = 'Q' + parseFloat(d.monto_total ?? 0).toLocaleString('es-GT', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    document.getElementById('st-pend').textContent  = d.pendientes ?? 0;
    document.getElementById('st-pag').textContent   = d.pagadas ?? 0;
  } catch (e) {
    console.error('Error cargando estadísticas:', e);
  }
}

async function cargar(page = 1) {
  const prov = document.getElementById('search-proveedor')?.value.trim() || '';
  const est  = document.getElementById('search-estado')?.value || '';
  const tbody = document.getElementById('tbody');
  tbody.innerHTML = '<tr><td colspan="6" class="loading-overlay"><div class="spinner"></div></td></tr>';

  try {
    const p = new URLSearchParams({ page });
    if (prov) p.set('proveedor', prov);
    if (est)  p.set('estado_pago', est);

    const res = await fetch(`${CONFIG.API_BASE_URL}/api/compras?${p}`, {
      headers: getHeaders(false)
    });
    const d = await res.json();
    renderTabla(d.compras || [], d.total || 0, page, d.per_page || 20);
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--danger);padding:24px;">Error al conectar con el servidor. Verifica tu conexión.</td></tr>';
  }
}

function badgeClase(estado) {
  if (estado === 'Pagado')   return 'badge-active';
  if (estado === 'Anulado')  return 'badge-inactive';
  return 'badge-prospecto';
}

let pendingEstadoId = null;

function renderTabla(items, total, page, per_page) {
  const tbody = document.getElementById('tbody');

  if (!items.length) {
    tbody.innerHTML = `
      <tr><td colspan="6">
        <div class="empty-state">
          <div class="empty-icon">🛒</div>
          <p>No hay compras registradas.</p>
          <p style="font-size:.82rem;color:var(--text-muted);">Haz clic en <strong>＋ Nueva Compra</strong> para registrar una.</p>
        </div>
      </td></tr>`;
    document.getElementById('paginacion').style.display = 'none';
    return;
  }

  /* BUG #1 CORREGIDO: onclick usa data-attributes, no interpolación en la cadena */
  tbody.innerHTML = items.map(c => `
    <tr>
      <td>${escapeHtml(c.fecha_compra || '—')}</td>
      <td><strong>${escapeHtml(c.proveedor)}</strong></td>
      <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"
          title="${escapeHtml(c.productos)}">${escapeHtml(c.productos)}</td>
      <td>Q${parseFloat(c.monto_total).toLocaleString('es-GT', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
      <td><span class="badge ${badgeClase(c.estado_pago)}">${escapeHtml(c.estado_pago)}</span></td>
      <td class="td-actions">
        <button class="btn btn-ghost btn-sm"
          data-id="${c.id_compra}"
          data-estado="${escapeHtml(c.estado_pago)}"
          onclick="abrirEstado(this)">🔄 Estado</button>
      </td>
    </tr>`).join('');

  const pag = document.getElementById('paginacion');
  pag.style.display = 'flex';
  const desde = (page - 1) * per_page + 1;
  const hasta = Math.min(page * per_page, total);
  document.getElementById('pag-info').textContent = `Mostrando ${desde}–${hasta} de ${total}`;

  const ctrl = document.getElementById('pag-controls');
  ctrl.innerHTML = '';
  const pages = Math.ceil(total / per_page);

  const mkBtn = (label, p, active, disabled) => {
    const b = document.createElement('button');
    b.className = 'page-btn' + (active ? ' active' : '');
    b.textContent = label;
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
  document.getElementById('search-proveedor').value = '';
  document.getElementById('search-estado').value = '';
  cargar(1);
}

/* ═══════════════ Cambiar estado ══════════════════════════════ */
function abrirEstado(btn) {
  pendingEstadoId = btn.dataset.id;
  const estadoActual = btn.dataset.estado || 'Pendiente';
  document.getElementById('nuevo-estado').value = estadoActual;
  abrirModal('modal-estado');
}

async function confirmarEstado() {
  const est = document.getElementById('nuevo-estado').value;
  const btnConfirmar = document.querySelector('#modal-estado .btn-gold');
  btnConfirmar.disabled = true;
  btnConfirmar.textContent = 'Actualizando...';

  try {
    const res = await fetch(`${CONFIG.API_BASE_URL}/api/compras/${pendingEstadoId}/estado`, {
      method: 'PATCH',
      headers: getHeaders(),
      body: JSON.stringify({ estado_pago: est })
    });
    const d = await res.json();

    cerrarModal('modal-estado');

    if (d.error) {
      showToast(d.error, 'error');
    } else {
      showToast(d.mensaje || `Estado actualizado a: ${est}`, 'success');
      cargar(1);
    }
  } catch (e) {
    showToast('Error al conectar con el servidor. Intenta de nuevo.', 'error');
  } finally {
    btnConfirmar.disabled = false;
    btnConfirmar.textContent = 'Actualizar';
  }
}

/* ═══════════════════════ FORMULARIO ══════════════════════════ */
if (isForm) {
  document.addEventListener('DOMContentLoaded', async () => {
    if (!requireAuth()) return;
    const hoy = new Date().toISOString().split('T')[0];
    const fechaEl = document.getElementById('fecha_compra');
    if (fechaEl && !fechaEl.value) fechaEl.value = hoy;
    await cargarProveedoresActivos();
  });
}

/* BUG #2 CORREGIDO: solo carga proveedores activos */
async function cargarProveedoresActivos() {
  const sel = document.getElementById('id_proveedor');
  if (!sel) return;

  sel.innerHTML = '<option value="">Cargando proveedores...</option>';
  sel.disabled = true;

  try {
    const res = await fetch(
      `${CONFIG.API_BASE_URL}/api/proveedores?per_page=200&estado=Activo`,
      { headers: getHeaders(false) }
    );
    const d = await res.json();
    const proveedores = (d.proveedores || []).filter(p => p.estado === 'Activo');

    sel.innerHTML = '<option value="">Selecciona un proveedor activo...</option>';

    if (proveedores.length === 0) {
      sel.innerHTML += '<option value="" disabled>No hay proveedores activos disponibles</option>';
    } else {
      proveedores.forEach(p => {
        const o = document.createElement('option');
        o.value = p.id_proveedor;
        o.textContent = p.nombre_empresa;
        sel.appendChild(o);
      });
    }
  } catch (e) {
    sel.innerHTML = '<option value="">Error al cargar proveedores</option>';
    showToast('No se pudieron cargar los proveedores. Verifica la conexión.', 'error');
  } finally {
    sel.disabled = false;
  }
}

async function guardar() {
  const id_prov  = document.getElementById('id_proveedor')?.value;
  const prods    = document.getElementById('productos')?.value.trim();
  const montoRaw = document.getElementById('monto_total')?.value;
  const estado   = document.getElementById('estado_pago')?.value || 'Pendiente';

  if (!id_prov) { showToast('Selecciona un proveedor.', 'error'); return; }
  if (!prods)   { showToast('Describe los productos o servicios adquiridos.', 'error'); return; }

  /* INCONSISTENCIA #1 CORREGIDA: monto estrictamente > 0 */
  const monto = parseFloat(montoRaw);
  if (isNaN(monto) || monto <= 0) {
    showToast('El monto debe ser mayor a 0.', 'error');
    return;
  }

  const payload = {
    id_proveedor: parseInt(id_prov),
    productos:    prods,
    monto_total:  monto,
    estado_pago:  estado,
    fecha_compra: document.getElementById('fecha_compra')?.value || null,
    notas:        document.getElementById('notas')?.value.trim() || null,
  };

  const btn = document.querySelector('.btn-gold');
  btn.disabled = true;
  btn.textContent = 'Guardando...';

  try {
    const res = await fetch(`${CONFIG.API_BASE_URL}/api/compras`, {
      method:  'POST',
      headers: getHeaders(),
      body:    JSON.stringify(payload)
    });
    const data = await res.json();

    if (data.error) {
      const msg = data.error.toLowerCase().includes('inactivo')
        ? 'El proveedor seleccionado no está activo. Por favor, elige otro proveedor.'
        : data.error;
      showToast(msg, 'error');
      btn.disabled = false;
      btn.textContent = '💾 Registrar Compra';
      return;
    }

    showToast(data.mensaje || 'Compra registrada exitosamente.', 'success');
    setTimeout(() => { window.location.href = '/compras.html'; }, 1200);

  } catch (e) {
    showToast('Error al conectar con el servidor. Intenta de nuevo.', 'error');
    btn.disabled = false;
    btn.textContent = '💾 Registrar Compra';
  }
}
