"""
proveedor_service.py - Capa de lógica de negocio para Proveedores
v3:
  - Filtro por estado (Activo/Inactivo)
  - Nuevo parámetro 'busqueda': busca OR en nombre_empresa y nit
  - Mensajes de error descriptivos
"""
import logging
from database import to_int, sp_result
from repositories import proveedor_repository as repo

logger = logging.getLogger(__name__)

_MAX_PER_PAGE     = 100
_DEFAULT_PER_PAGE = 20


def _sanitize(value, max_len=500) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()[:max_len]


def get_all_proveedores(nombre=None, nit=None, categoria=None, estado=None,
                        busqueda=None, page=1, per_page=_DEFAULT_PER_PAGE):
    try:
        page     = max(1, int(page))
        per_page = min(max(1, int(per_page)), _MAX_PER_PAGE)
    except (ValueError, TypeError):
        page, per_page = 1, _DEFAULT_PER_PAGE

    where_clauses = ["1=1"]
    params = []

    # INCONSISTENCIA #2 CORREGIDA:
    # 'busqueda' hace OR entre nombre_empresa y nit en un solo campo
    if busqueda:
        term = f"%{_sanitize(busqueda)}%"
        where_clauses.append("(p.nombre_empresa LIKE %s OR p.nit LIKE %s)")
        params.extend([term, term])
    else:
        if nombre:
            where_clauses.append("p.nombre_empresa LIKE %s")
            params.append(f"%{_sanitize(nombre)}%")
        if nit:
            where_clauses.append("p.nit LIKE %s")
            params.append(f"%{_sanitize(nit, 30)}%")

    if categoria:
        where_clauses.append("c.nombre_categoria = %s")
        params.append(_sanitize(categoria, 100))
    if estado in ("Activo", "Inactivo"):
        where_clauses.append("p.estado = %s")
        params.append(estado)

    offset = (page - 1) * per_page
    proveedores, total = repo.find_all(where_clauses, params, offset, per_page)

    total_pages = max(1, (total + per_page - 1) // per_page)
    return {
        "proveedores":       proveedores,
        "total":             total,
        "page":              page,
        "per_page":          per_page,
        "total_pages":       total_pages,
        "has_next_page":     page < total_pages,
        "has_previous_page": page > 1,
    }


def get_proveedor_by_id(id_proveedor):
    return repo.find_by_id(id_proveedor)


def get_categorias():
    return repo.find_all_categorias()


def create_proveedor(data: dict):
    nombre   = _sanitize(data.get("nombre_empresa", ""))
    nit      = _sanitize(data.get("nit", ""), 30)
    telefono = _sanitize(data.get("telefono", ""), 20)

    errors = []
    if not nombre:
        errors.append("El nombre de la empresa es obligatorio.")
    if not nit:
        errors.append("El NIT es obligatorio.")
    if not data.get("id_categoria"):
        errors.append("La categoría es obligatoria.")
    if not telefono:
        errors.append("El teléfono es obligatorio.")

    if errors:
        return {"error": errors[0], "errores": errors}

    clean_data = {**data, "nombre_empresa": nombre, "nit": nit, "telefono": telefono}
    row = repo.insert(clean_data)
    id_prov, mensaje, is_error = sp_result(row)
    if is_error:
        return {"error": mensaje or "Error al registrar el proveedor."}
    return {"id_proveedor": id_prov, "mensaje": mensaje}


def update_proveedor(id_proveedor, data: dict):
    nombre = _sanitize(data.get("nombre_empresa", ""))
    if not nombre:
        return {"error": "El nombre de la empresa es obligatorio."}

    clean_data = {**data, "nombre_empresa": nombre}
    row = repo.update(id_proveedor, clean_data)
    id_prov, mensaje, is_error = sp_result(row)
    if is_error:
        return {"error": mensaje or "Error al actualizar el proveedor."}
    return {"id_proveedor": id_prov, "mensaje": mensaje}


def inactivar_proveedor(id_proveedor, motivo, usuario="sistema"):
    motivo = _sanitize(motivo, 500)
    if not motivo:
        return {"error": "El motivo de inactivación es obligatorio."}

    row = repo.set_inactive(id_proveedor, motivo, _sanitize(usuario))
    id_res, mensaje, is_error = sp_result(row)
    if is_error:
        return {"error": mensaje or "Error al inactivar el proveedor."}
    return {"mensaje": mensaje}


def activar_proveedor(id_proveedor, usuario="sistema"):
    row = repo.set_active(id_proveedor, _sanitize(usuario))
    id_res, mensaje, is_error = sp_result(row)
    if is_error:
        return {"error": mensaje or "Error al activar el proveedor."}
    return {"mensaje": mensaje}


def eliminar_proveedor(id_proveedor, usuario="sistema"):
    row = repo.delete(id_proveedor, _sanitize(usuario))
    id_res, mensaje, is_error = sp_result(row)
    if is_error:
        return {"error": mensaje or "Error al eliminar el proveedor."}
    return {"mensaje": mensaje}
