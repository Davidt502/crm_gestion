// empleados.js — CRM Ing Software


function cerrarModal(id){ document.getElementById(id)?.classList.remove('open'); }
function abrirModal(id){ document.getElementById(id)?.classList.add('open'); }

function getHeaders(includeContentType = true) {
  const headers = { 'Authorization': `Bearer ${getToken()}` };
  if (includeContentType) headers['Content-Type'] = 'application/json';
  return headers;
}

/* ═══════════════════════════ LISTA ═══════════════════════════ */
if(document.getElementById('tbody') && !document.getElementById('id_dependencia')){
  document.addEventListener('DOMContentLoaded', () => {
    if (!requireAuth()) return;
    cargarDeps();
    cargar();
  });
}

async function cargarDeps(){
  try{
    const res = await fetch(`${CONFIG.API_BASE_URL}/api/dependencias`, {
      headers: getHeaders(false)
    });
    const data = await res.json();
    const sel = document.getElementById('search-dependencia');
    if(!sel) return;
    sel.innerHTML = '<option value="">Todas las dependencias</option>';
    data.forEach(d => {
      const o = document.createElement('option');
      o.value = d.id_dependencia;
      o.textContent = d.nombre_dependencia;
      sel.appendChild(o);
    });
  }catch(e){ console.error('Error cargando dependencias:', e); }
}

async function cargar(page=1){
  const nombre = document.getElementById('search-nombre')?.value || '';
  const dep = document.getElementById('search-dependencia')?.value || '';
  const estado = document.getElementById('search-estado')?.value || '';
  const tbody = document.getElementById('tbody');
  tbody.innerHTML = '<tr><td colspan="7" class="loading-overlay"><div class="spinner"></div></td></tr>';
  
  try{
    const p = new URLSearchParams({page});
    if(nombre) p.set('nombre', nombre);
    if(dep) p.set('dependencia', dep);
    if(estado) p.set('estado', estado);
    
    const res = await fetch(`${CONFIG.API_BASE_URL}/api/empleados?${p}`, {
      headers: getHeaders(false)
    });
    const d = await res.json();
    renderTabla(d.empleados || [], d.total || 0, page, d.per_page || 10);
  }catch(e){
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--danger);padding:20px;">Error al cargar.</td></tr>';
  }
}

function renderTabla(items, total, page, per_page){
  const tbody = document.getElementById('tbody');
  if(!items.length){
    tbody.innerHTML = '<tr><td colspan="7"><div class="empty-state"><div class="empty-icon">👔</div><p>No se encontraron empleados.</p></div></td></tr>';
    document.getElementById('paginacion').style.display = 'none';
    return;
  }
  
  tbody.innerHTML = items.map(e => `
    <tr>
      <td><strong>${escapeHtml(e.numero_empleado || "")}</strong></td>
      <td><strong>${escapeHtml(e.nombre_completo)}</strong></td>
      <td>${escapeHtml(e.cargo || '—')}</td>
      <td>${escapeHtml(e.dependencia || 'Sin asignar')}</td>
      <td><span class="badge ${e.estado==='Activo' ? 'badge-active' : 'badge-inactive'}">${escapeHtml(e.estado)}</span></td>
      <td style="font-size:0.78rem;">${escapeHtml(e.correo || e.correo_empresarial || '—')}</td>
      <td class="td-actions">
        <a href="/form_empleado.html?id=${e.id_empleado}" class="btn btn-ghost btn-sm btn-icon" title="Editar">✏️</a>
        <button class="btn btn-ghost btn-sm btn-icon" title="Reasignar dependencia"
          onclick="abrirReasignar(${e.id_empleado},this.dataset.nombre" data-nombre="${escapeHtml(e.nombre_completo)})">🔄</button>
      </td>
    </tr>`).join('');

  const pag = document.getElementById('paginacion');
  pag.style.display = 'flex';
  const desde = (page-1)*per_page + 1;
  const hasta = Math.min(page*per_page, total);
  document.getElementById('pag-info').textContent = `Mostrando ${desde}–${hasta} de ${total}`;
  
  const ctrl = document.getElementById('pag-controls');
  ctrl.innerHTML = '';
  const pages = Math.ceil(total / per_page);
  
  const btn = (label, p, active, disabled) => {
    const b = document.createElement('button');
    b.className = 'page-btn' + (active ? ' active' : '');
    b.textContent = label;
    b.disabled = disabled;
    if(!disabled) b.onclick = () => cargar(p);
    return b;
  };
  
  ctrl.appendChild(btn('‹', page-1, false, page<=1));
  for(let i = Math.max(1, page-2); i <= Math.min(pages, page+2); i++)
    ctrl.appendChild(btn(i, i, i===page, false));
  ctrl.appendChild(btn('›', page+1, false, page>=pages));
}

function buscar(){ cargar(1); }
function limpiar(){
  document.getElementById('search-nombre').value = '';
  document.getElementById('search-dependencia').value = '';
  document.getElementById('search-estado').value = '';
  cargar(1);
}

/* ═══════════════════ MODAL NUEVA DEPENDENCIA ═════════════════ */
function abrirCrearDep(){
  document.getElementById('dep-input').value = '';
  abrirModal('modal-dependencia');
}

async function crearDependencia(){
  const nombre = document.getElementById('dep-input').value.trim();
  if(!nombre){ showToast('El nombre es obligatorio.', 'error'); return; }
  
  try{
    const res = await fetch(`${CONFIG.API_BASE_URL}/api/dependencias`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({nombre_dependencia: nombre})
    });
    const d = await res.json();
    if(d.error){ showToast(d.error, 'error'); return; }
    showToast(d.mensaje || 'Dependencia creada.', 'success');
    cerrarModal('modal-dependencia');
    cargarDeps();
  }catch(e){ showToast('Error al crear.', 'error'); }
}

/* ══════════════════════════ FORMULARIO ══════════════════════════ */
if(typeof EMPLEADO_ID !== 'undefined'){
  document.addEventListener('DOMContentLoaded', async () => {
    if (!requireAuth()) return;
    await cargarDepsForm();
    if(EMPLEADO_ID) cargarDatos(EMPLEADO_ID);
  });
}

async function cargarDepsForm(){
  try{
    const res = await fetch(`${CONFIG.API_BASE_URL}/api/dependencias`, {
      headers: getHeaders(false)
    });
    const data = await res.json();
    const sel = document.getElementById('id_dependencia');
    if(!sel) return;
    sel.innerHTML = '<option value="">Sin asignar</option>';
    data.forEach(d => {
      const o = document.createElement('option');
      o.value = d.id_dependencia;
      o.textContent = d.nombre_dependencia;
      sel.appendChild(o);
    });
  }catch(e){ console.error('Error cargando dependencias:', e); }
}

async function cargarDatos(id){
  try{
    const res = await fetch(`${CONFIG.API_BASE_URL}/api/empleados/${id}`, {
      headers: getHeaders(false)
    });
    const d = await res.json();
    if(d.error){ showToast(d.error, 'error'); return; }
    
    document.getElementById('form-title').textContent = 'Editar Empleado';
    document.getElementById('form-breadcrumb').textContent = 'Editar';
    document.getElementById('numero_empleado').value = d.numero_empleado || '';
    document.getElementById('numero_empleado').disabled = true;
    document.getElementById('dpi').value = d.dpi || '';
    document.getElementById('dpi').disabled = true;
    document.getElementById('nombre_completo').value = d.nombre_completo || '';
    document.getElementById('cargo').value = d.cargo || '';
    document.getElementById('id_dependencia').value = d.id_dependencia || '';
    document.getElementById('estado').value = d.estado || 'Activo';
    document.getElementById('fecha_nacimiento').value = d.fecha_nacimiento || '';
    document.getElementById('telefono').value = d.telefono || '';
    document.getElementById('correo').value = d.correo || '';
    document.getElementById('correo_empresarial').value = d.correo_empresarial || '';
    document.getElementById('correo_personal').value = d.correo_personal || '';
    document.getElementById('red_social').value = d.red_social || '';
    document.getElementById('direccion').value = d.direccion || '';
  }catch(e){ showToast('Error al cargar datos.', 'error'); }
}

async function guardar(){
  const nombre = document.getElementById('nombre_completo').value.trim();
  const numEmp = document.getElementById('numero_empleado')?.value.trim();
  const dpi = document.getElementById('dpi')?.value.trim();
  const corrEmp = document.getElementById('correo_empresarial')?.value.trim();
  const telefono = document.getElementById('telefono')?.value.trim();
  const isEdit = typeof EMPLEADO_ID !== 'undefined' && EMPLEADO_ID;

  if(!nombre){ showToast('El nombre completo es obligatorio.', 'error'); return; }
  if(!isEdit && !numEmp){ showToast('El número de empleado es obligatorio.', 'error'); return; }
  if(!isEdit && !dpi){ showToast('El DPI es obligatorio.', 'error'); return; }
  if(telefono && !/^\d{7,15}$/.test(telefono.replace(/[\s\-\+\(\)]/g, '')))
    { showToast('Teléfono inválido (7-15 dígitos).', 'error'); return; }
  if(corrEmp && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(corrEmp))
    { showToast('Correo empresarial inválido.', 'error'); return; }

  const payload = {
    numero_empleado: numEmp,
    dpi,
    nombre_completo: nombre,
    cargo: document.getElementById('cargo').value.trim() || null,
    id_dependencia: document.getElementById('id_dependencia').value || null,
    estado: document.getElementById('estado').value,
    fecha_nacimiento: document.getElementById('fecha_nacimiento').value || null,
    correo: document.getElementById('correo')?.value.trim() || null,
    correo_empresarial: corrEmp || null,
    correo_personal: document.getElementById('correo_personal')?.value.trim() || null,
    telefono: telefono || null,
    direccion: document.getElementById('direccion').value.trim() || null,
    red_social: document.getElementById('red_social')?.value.trim() || null,
  };

  const btn = document.querySelector('.btn-gold');
  btn.disabled = true;
  btn.textContent = 'Guardando...';

  try{
    const url = isEdit 
      ? `${CONFIG.API_BASE_URL}/api/empleados/${EMPLEADO_ID}` 
      : `${CONFIG.API_BASE_URL}/api/empleados`;
    const method = isEdit ? 'PUT' : 'POST';
    const res = await fetch(url, {
      method,
      headers: getHeaders(),
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if(data.error){
      showToast(data.error, 'error');
      btn.disabled = false;
      btn.textContent = '💾 Guardar';
      return;
    }
    showToast(data.mensaje || 'Operación exitosa.', 'success');
    setTimeout(() => window.location.href = '/empleados.html', 1200);
  }catch(e){
    showToast('Error al guardar.', 'error');
    btn.disabled = false;
    btn.textContent = '💾 Guardar';
  }
}

/* ═══════════════════ REASIGNAR DEPENDENCIA ══════════════════ */
let pendingReasignarId = null;

async function abrirReasignar(id, nombre){
  pendingReasignarId = id;
  document.getElementById('dep-actual-nombre').textContent = nombre;
  document.getElementById('motivo-reasignar').value = '';
  document.getElementById('fecha-efectiva-reasignar').value = '';

  try{
    const res = await fetch(`${CONFIG.API_BASE_URL}/api/dependencias`, {
      headers: getHeaders(false)
    });
    const data = await res.json();
    const sel = document.getElementById('dep-nueva');
    sel.innerHTML = '<option value="">Selecciona...</option>';
    data.forEach(d => {
      const o = document.createElement('option');
      o.value = d.id_dependencia;
      o.textContent = d.nombre_dependencia;
      sel.appendChild(o);
    });
  }catch(e){ console.error('Error cargando dependencias:', e); }

  abrirModal('modal-reasignar');
}

async function confirmarReasignar(){
  const dep = document.getElementById('dep-nueva').value;
  const motivo = document.getElementById('motivo-reasignar').value.trim();
  const fecha = document.getElementById('fecha-efectiva-reasignar').value;
  
  if(!dep){ showToast('Selecciona la nueva dependencia.', 'error'); return; }
  if(!motivo){ showToast('El motivo es obligatorio.', 'error'); return; }
  
  try{
    const res = await fetch(`${CONFIG.API_BASE_URL}/api/empleados/${pendingReasignarId}/reasignar`, {
      method: 'PATCH',
      headers: getHeaders(),
      body: JSON.stringify({
        id_dependencia_nueva: parseInt(dep),
        motivo,
        fecha_efectiva: fecha || null
      })
    });
    const d = await res.json();
    if(d.error){ showToast(d.error, 'error'); return; }
    showToast(d.mensaje || 'Reasignación exitosa.', 'success');
    cerrarModal('modal-reasignar');
    cargar(1);
  }catch(e){ showToast('Error.', 'error'); }
}
