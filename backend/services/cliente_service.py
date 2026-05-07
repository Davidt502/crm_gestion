""""
cliente_service.py - Capa de lógica de negocio para Clientes
Correcciones:
  - Validación y sanitización de inputs
  - Paginación segura con límites
  - Manejo de errores explícito
"""
import logging
import re
from repositories import cliente_repository as repo

logger = logging.getLogger(__name__)

_MAX_PER_PAGE = 100
_DEFAULT_PER_PAGE = 20

TIPOS_CLIENTE_VALIDOS = {"Cliente", "Prospecto"}
ESTADOS_VALIDOS = {"Activo", "Inactivo"}
TIPOS_CONTACTO_VALIDOS = {"Teléfono", "Celular", "Email", "Dirección", "Fax"}


def _sanitize(value, max_len=500) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()[:max_len]


def _valid_email(email: str) -> bool:
    if not email:
        return True  # email es opcional
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def get_all_clientes(nombre=None, documento=None, tipo=None, page=1, per_page=_DEFAULT_PER_PAGE, search=None):
    try:
        page = max(1, int(page))
        per_page = min(max(1, int(per_page)), _MAX_PER_PAGE)
    except (ValueError, TypeError):
        page, per_page = 1, _DEFAULT_PER_PAGE

    where_clauses = ["1=1"]
    params = []

    if search:
        where_clauses.append("(nombre_razon_social LIKE %s OR documento_identificacion LIKE %s)")
        s = _sanitize(search)
        params.extend([f"%{s}%", f"%{s}%"])
    else:
        if nombre:
            where_clauses.append("nombre_razon_social LIKE %s")
            params.append(f"%{_sanitize(nombre)}%")
        if documento:
            where_clauses.append("documento_identificacion LIKE %s")
            params.append(f"%{_sanitize(documento, 50)}%")

    if tipo and tipo in TIPOS_CLIENTE_VALIDOS:
        where_clauses.append("tipo = %s")
        params.append(tipo)

    offset = (page - 1) * per_page
    clientes, total = repo.find_all(where_clauses, params, offset, per_page)

    total_pages = max(1, (total + per_page - 1) // per_page)
    return {
        "data":   clientes,
        "meta": {
            "total":             total,
            "page":              page,
            "limit":             per_page,
            "total_pages":       total_pages,
            "has_next_page":     page < total_pages,
            "has_previous_page": page > 1,
        },
        # Mantener compatibilidad con código legacy
        "clientes":  clientes,
        "total":     total,
        "page":      page,
        "per_page":  per_page,
    }


def get_cliente_by_id(id_cliente):
    return repo.find_by_id(id_cliente)


def create_cliente(data: dict):
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

    clean_data = {
        **data,
        "nombre_razon_social":      nombre,
        "documento_identificacion": documento,
        "tipo":                     tipo,
        "estado":                   estado,
        "correo":                   correo,
    }

    id_cliente, mensaje = repo.insert(clean_data)

    if id_cliente:
        usuario = _sanitize(data.get("usuario", "sistema"))
        for contacto in data.get("contactos", []):
            if _sanitize(contacto.get("descripcion", "")):
                repo.insert_contacto(id_cliente, contacto, usuario)
        return {"id_cliente": id_cliente, "mensaje": mensaje}

    return {"error": mensaje or "Error desconocido"}


def update_cliente(id_cliente, data: dict):
    nombre = _sanitize(data.get("nombre_razon_social", ""))
    correo = _sanitize(data.get("correo", ""), 200) or None

    if not nombre:
        return {"error": "El nombre o razón social es obligatorio."}
    if correo and not _valid_email(correo):
        return {"error": "El correo electrónico no tiene un formato válido."}

    clean_data = {**data, "nombre_razon_social": nombre, "correo": correo}
    id_result, mensaje = repo.update(id_cliente, clean_data)

    if id_result:
        usuario = _sanitize(data.get("usuario", "sistema"))
        for contacto in data.get("contactos", []):
            if contacto.get("id_contacto"):
                repo.update_contacto(contacto, usuario)
            elif _sanitize(contacto.get("descripcion", "")):
                repo.insert_contacto(id_cliente, contacto, usuario)
        return {"id_cliente": id_result, "mensaje": mensaje}

    return {"error": mensaje or "Error desconocido"}


def inactivar_cliente(id_cliente, usuario="sistema"):
    id_result, mensaje = repo.set_inactive(id_cliente, _sanitize(usuario))
    if id_result:
        return {"mensaje": mensaje}
    return {"error": mensaje or "Error al inactivar"}


def get_cumpleaneros_mes():
    return repo.find_cumpleaneros_mes()


def get_stats():
    return repo.get_stats()


def get_stats_clientes():
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
