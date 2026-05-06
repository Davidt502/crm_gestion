/**
 * sidebar.js — CRM Ing Software v3
 * Cambios v3:
 *   - Enlace "Usuarios" visible solo para rol admin
 *   - Sección "Administración" separada visualmente
 *   - Versión actualizada a v3.0.0
 */

function renderSidebar() {
    const user        = getUser() || { nombre: 'Usuario', rol: 'usuario' };
    const currentPath = window.location.pathname;
    const isActive    = (segment) => currentPath.includes(segment) ? 'active' : '';
    const isAdmin     = user.rol === 'admin';

    const sidebarHTML = `
    <button class="sidebar-toggle" id="sidebar-toggle" aria-label="Abrir menú">☰</button>
    <div class="sidebar-overlay" id="sidebar-overlay"></div>
    <aside class="sidebar" id="sidebar">
      <div class="sidebar-header">
        <div class="sidebar-logo">
          <div class="logo-icon">⚙️</div>
          <div class="logo-text">CRM Ing Software<span>Gestión Empresarial</span></div>
        </div>
        <div class="sidebar-user">
          <div class="sidebar-user-avatar" id="sb-avatar"></div>
          <div>
            <div class="sidebar-user-name" id="sb-user-name"></div>
            <div class="sidebar-user-role" id="sb-user-role"></div>
          </div>
        </div>
      </div>
      <nav class="sidebar-nav">
        <div class="nav-section-title">Principal</div>
        <a href="/dashboard.html"  class="nav-link ${isActive('dashboard')}"><span class="nav-icon">📊</span> Dashboard</a>

        <div class="nav-section-title">Módulos</div>
        <a href="/clientes.html"    class="nav-link ${isActive('clientes')}"><span class="nav-icon">👥</span> Clientes</a>
        <a href="/proveedores.html" class="nav-link ${isActive('proveedores')}"><span class="nav-icon">🏢</span> Proveedores</a>
        <a href="/compras.html"     class="nav-link ${isActive('compras')}"><span class="nav-icon">🛒</span> Compras</a>
        <a href="/empleados.html"   class="nav-link ${isActive('empleados')}"><span class="nav-icon">👔</span> Empleados</a>

        ${isAdmin ? `
        <div class="nav-section-title">Administración</div>
        <a href="/usuarios.html" class="nav-link ${isActive('usuario')}"><span class="nav-icon">🔐</span> Usuarios</a>
        ` : ''}
      </nav>
      <div class="sidebar-footer">
        <span class="sidebar-version">v3.0.0</span>
        <button class="logout-btn" id="logout-btn">⏻ Salir</button>
      </div>
    </aside>`;

    document.body.insertAdjacentHTML('afterbegin', sidebarHTML);

    // Usar textContent (no innerHTML) para evitar XSS
    document.getElementById('sb-avatar').textContent    = (user.nombre || 'A')[0].toUpperCase();
    document.getElementById('sb-user-name').textContent = user.nombre || 'Administrador';
    document.getElementById('sb-user-role').textContent =
        user.rol ? user.rol.charAt(0).toUpperCase() + user.rol.slice(1) : 'Usuario';

    document.getElementById('logout-btn').addEventListener('click', logout);

    // Comportamiento móvil
    const toggle  = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    function closeSidebar() {
        sidebar.classList.remove('sidebar-open');
        overlay.classList.remove('overlay-visible');
    }

    toggle?.addEventListener('click', () => {
        const isOpen = sidebar.classList.toggle('sidebar-open');
        overlay.classList.toggle('overlay-visible', isOpen);
    });
    overlay?.addEventListener('click', closeSidebar);
    sidebar.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth < 768) closeSidebar();
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    if (!requireAuth()) return;
    renderSidebar();
    // Mostrar enlace de Auditoría solo para admins
    const u = getUser();
    if (u && u.rol === 'admin') {
        const navAudit = document.getElementById('nav-auditoria');
        if (navAudit) navAudit.style.display = '';
    }
});
