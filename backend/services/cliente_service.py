"""
cliente_service.py - Capa de lógica de negocio para Clientes
"""
import logging
import re
from flask import g
from repositories import cliente_repository as repo

logger = logging.getLogger(__name__)

_MAX_PER_PAGE = 100
_DEFAULT_PER_PAGE = 20

TIPOS_CLIENTE_VALIDOS = {"Cliente", "Prospecto"}
ESTADOS_VALIDOS = {"Activo", "Inactivo"}


def _sanitize(value, max_len=500) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()[:max_len]


def _valid_email(email: str) -> bool:
    if not email:
        return True
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def get_all_clientes(nombre=None, documento=None, tipo=None, page=1, per_page=_DEFAULT_PER_PAGE, search=None):
    """
    Obtiene todos los clientes con paginación y filtros.
    - Si el usuario es ADMIN: ve TODOS los clientes
    - Si el usuario es NORMAL: ve SOLO los clientes que él creó (usuario_creacion = su username)

    CORRECCIÓN: se usa g.current_user con fallback seguro; el filtro por
    usuario_creacion solo se aplica si el rol NO es 'admin'.
    """
    try:
        page = max(1, int(page))
        per_page = min(max(1, int(per_page)), _MAX_PER_PAGE)
    except (ValueError, TypeError):
        page, per_page = 1, _DEFAULT_PER_PAGE

    where_clauses = ["1=1"]
    params = []

    # Leer rol y username del token JWT (almacenado en flask.g por token_required)
    current_user = getattr(g, 'current_user', None) or {}
    user_rol      = current_user.get('rol', 'usuario')
    user_username = current_user.get('username', 'sistema')

    # Filtro por propietario: solo para usuarios no-admin
    if user_rol != 'admin':
        where_clauses.append("usuario_creacion = %s")
        params.append(_sanitize(user_username, 80))
        logger.debug(f"Usuario normal '{user_username}' — filtrando por sus clientes")
    else:
        logger.debug(f"Administrador '{user_username}' — viendo TODOS los clientes")

    # Filtros de búsqueda
    if search:
        where_clauses.append("(nombre_razon_social ILIKE %s OR documento_identificacion ILIKE %s)")
        s = _sanitize(search)
        params.extend([f"%{s}%", f"%{s}%"])
    else:
        if nombre:
            where_clauses.append("nombre_razon_social ILIKE %s")
            params.append(f"%{_sanitize(nombre)}%")
        if documento:
            where_clauses.append("documento_identificacion ILIKE %s")
            params.append(f"%{_sanitize(documento, 50)}%")

    if tipo and tipo in TIPOS_CLIENTE_VALIDOS:
        where_clauses.append("tipo = %s")
        params.append(tipo)

    offset = (page - 1) * per_page
    clientes, total = repo.find_all(where_clauses, params, offset, per_page)

    total_pages = max(1, (total + per_page - 1) // per_page)
    return {
        "data": clientes,
        "meta": {
            "total": total,
            "page": page,
            "limit": per_page,
            "total_pages": total_pages,
            "has_next_page": page < total_pages,
            "has_previous_page": page > 1,
        },
        "clientes": clientes,
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def get_cliente_by_id(id_cliente):
    """Obtiene un cliente por ID (sin restricciones adicionales)"""
    return repo.find_by_id(id_cliente)


def create_cliente(data: dict):
    """Crea un nuevo cliente con el usuario_creacion del token"""
    nombre = _sanitize(data.get("nombre_razon_social", ""))
    documento = _sanitize(data.get("documento_identificacion", ""), 50)
    correo = _sanitize(data.get("correo", ""), 200) or None
    tipo = _sanitize(data.get("tipo", "Cliente"), 20)
    estado = _sanitize(data.get("estado", "Activo"), 20)

    errors = []
    if not nombre:
        errors.append("El nombre o razón social es obligatorio.")
    if not documento:
        errors.append("El documento de identificación es obligatorio.")
    if tipo not in TIPOS_CLIENTE_VALIDOS:
        errors.append(f"Tipo inválido. Valores permitidos: {', '.join(TIPOS_CLIENTE_VALIDOS)}")
    if estado not in ESTADOS_VALIDOS:
        estado = "Activo"
    if correo and not _valid_email(correo):
        errors.append("El correo electrónico no tiene un formato válido.")

    if errors:
        return {"error": " ".join(errors)}

    #  OBTENER USUARIO DEL TOKEN 
    usuario_creador = getattr(g, 'current_user', {}).get('username', 'sistema')

    clean_data = {
        **data,
        "nombre_razon_social": nombre,
        "documento_identificacion": documento,
        "tipo": tipo,
        "estado": estado,
        "correo": correo,
        "usuario": usuario_creador,  # ← Usuario del token
    }

    id_cliente, mensaje = repo.insert(clean_data)

    if id_cliente:
        for contacto in data.get("contactos", []):
            tiene_contenido = (
                _sanitize(contacto.get("nombre_contacto", "")) or
                _sanitize(contacto.get("telefono", ""), 20) or
                _sanitize(contacto.get("correo", ""), 200)
            )
            if tiene_contenido:
                repo.insert_contacto(id_cliente, contacto, usuario_creador)
        return {"id_cliente": id_cliente, "mensaje": mensaje}

    return {"error": mensaje or "Error desconocido"}


def update_cliente(id_cliente, data: dict):
    """Actualiza un cliente existente"""
    nombre = _sanitize(data.get("nombre_razon_social", ""))
    correo = _sanitize(data.get("correo", ""), 200) or None

    if not nombre:
        return {"error": "El nombre o razón social es obligatorio."}
    if correo and not _valid_email(correo):
        return {"error": "El correo electrónico no tiene un formato válido."}

    usuario_editor = getattr(g, 'current_user', {}).get('username', 'sistema')

    clean_data = {**data, "nombre_razon_social": nombre, "correo": correo, "usuario": usuario_editor}
    id_result, mensaje = repo.update(id_cliente, clean_data)

    if id_result:
        for contacto in data.get("contactos", []):
            tiene_contenido = (
                _sanitize(contacto.get("nombre_contacto", "")) or
                _sanitize(contacto.get("telefono", ""), 20) or
                _sanitize(contacto.get("correo", ""), 200)
            )
            if contacto.get("id_contacto"):
                if tiene_contenido:
                    repo.update_contacto(contacto, usuario_editor)
            elif tiene_contenido:
                repo.insert_contacto(id_cliente, contacto, usuario_editor)
        return {"id_cliente": id_result, "mensaje": mensaje}

    return {"error": mensaje or "Error desconocido"}


def inactivar_cliente(id_cliente, usuario="sistema"):
    """Inactiva un cliente"""
    id_result, mensaje = repo.set_inactive(id_cliente, _sanitize(usuario))
    if id_result:
        return {"mensaje": mensaje}
    return {"error": mensaje or "Error al inactivar"}


def get_cumpleaneros_mes():
    """Obtiene los cumpleañeros del mes (sin restricción de usuario)"""
    return repo.find_cumpleaneros_mes()


def get_stats():
    """Obtiene estadísticas completas para el dashboard"""
    return repo.get_stats()


def get_stats_clientes():
    """Obtiene estadísticas específicas de clientes"""
    return repo.get_stats_clientes()


def get_tipos_cliente():
    return [{"id": 1, "descripcion": "Cliente"}, {"id": 2, "descripcion": "Prospecto"}]


def get_tipos_contacto():
    return [
        {"id": 1, "descripcion": "Teléfono"},
        {"id": 2, "descripcion": "Celular"},
        {"id": 3, "descripcion": "Email"},
        {"id": 4, "descripcion": "Dirección"},
        {"id": 5, "descripcion": "Fax"},
    ]