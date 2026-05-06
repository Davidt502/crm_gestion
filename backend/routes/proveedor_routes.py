"""
proveedor_routes.py - Capa de presentación/API para Proveedores
v3: añadido filtro ?estado= y ?busqueda= (OR nombre|NIT)
"""
from flask import Blueprint, request, jsonify
from services import proveedor_service as service
from middleware.auth_middleware import token_required, get_usuario

proveedor_bp = Blueprint("proveedores", __name__, url_prefix="/api/proveedores")

_ESTADOS_VALIDOS = {"Activo", "Inactivo"}


@proveedor_bp.route("/categorias", methods=["GET"])
@token_required
def get_categorias():
    return jsonify(service.get_categorias())


@proveedor_bp.route("", methods=["GET"])
@token_required
def get_proveedores():
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    estado_raw = request.args.get("estado") or None
    estado     = estado_raw if estado_raw in _ESTADOS_VALIDOS else None

    result = service.get_all_proveedores(
        nombre=request.args.get("nombre")   or None,
        nit=request.args.get("nit")         or None,
        categoria=request.args.get("categoria") or None,
        estado=estado,
        busqueda=request.args.get("busqueda") or None,
        page=page,
    )
    return jsonify(result)


@proveedor_bp.route("/<int:id>", methods=["GET"])
@token_required
def get_proveedor(id):
    proveedor = service.get_proveedor_by_id(id)
    if proveedor:
        return jsonify(proveedor)
    return jsonify({"error": "Proveedor no encontrado"}), 404


@proveedor_bp.route("", methods=["POST"])
@token_required
def create_proveedor():
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 400
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Body JSON inválido o vacío"}), 400
    data["usuario"] = get_usuario()
    result = service.create_proveedor(data)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result), 201


@proveedor_bp.route("/<int:id>", methods=["PUT"])
@token_required
def update_proveedor(id):
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 400
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Body JSON inválido o vacío"}), 400
    data["usuario"] = get_usuario()
    result = service.update_proveedor(id, data)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@proveedor_bp.route("/<int:id>/inactivar", methods=["PATCH"])
@token_required
def inactivar_proveedor(id):
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 400
    body = request.get_json(silent=True) or {}
    result = service.inactivar_proveedor(id, body.get("motivo", ""), get_usuario())
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@proveedor_bp.route("/<int:id>/activar", methods=["PATCH"])
@token_required
def activar_proveedor(id):
    result = service.activar_proveedor(id, get_usuario())
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@proveedor_bp.route("/<int:id>", methods=["DELETE"])
@token_required
def eliminar_proveedor(id):
    result = service.eliminar_proveedor(id, get_usuario())
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)
