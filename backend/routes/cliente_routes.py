"""
cliente_routes.py - Capa de presentación/API para Clientes
Correcciones:
  - Validación Content-Type en métodos que reciben body
  - get_json(silent=True) para no lanzar excepciones ante JSON malformado
  - Manejo de caso data=None cuando el body está vacío
"""
from flask import Blueprint, request, jsonify
from services import cliente_service as service
from middleware.auth_middleware import token_required, get_usuario

cliente_bp = Blueprint("clientes", __name__, url_prefix="/api/clientes")


@cliente_bp.route("", methods=["GET"])
@token_required
def get_clientes():
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = max(1, int(request.args.get("limit", 20)))
    except (ValueError, TypeError):
        page, per_page = 1, 20

    result = service.get_all_clientes(
        nombre=request.args.get("nombre") or None,
        documento=request.args.get("documento") or None,
        tipo=request.args.get("tipo") or None,
        page=page,
        per_page=per_page,
        search=request.args.get("search") or None,
    )
    return jsonify(result)


@cliente_bp.route("/<int:id>", methods=["GET"])
@token_required
def get_cliente(id):
    cliente = service.get_cliente_by_id(id)
    if cliente:
        return jsonify(cliente)
    return jsonify({"error": "Cliente no encontrado"}), 404


@cliente_bp.route("", methods=["POST"])
@token_required
def create_cliente():
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 400
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Body JSON inválido o vacío"}), 400
    data["usuario"] = get_usuario()
    result = service.create_cliente(data)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result), 201


@cliente_bp.route("/<int:id>", methods=["PUT"])
@token_required
def update_cliente(id):
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 400
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Body JSON inválido o vacío"}), 400
    data["usuario"] = get_usuario()
    result = service.update_cliente(id, data)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@cliente_bp.route("/<int:id>/inactivar", methods=["PATCH"])
@token_required
def inactivar_cliente(id):
    return jsonify(service.inactivar_cliente(id, get_usuario()))


@cliente_bp.route("/tipos-cliente", methods=["GET"])
@token_required
def get_tipos_cliente():
    return jsonify(service.get_tipos_cliente())


@cliente_bp.route("/tipos-contacto", methods=["GET"])
@token_required
def get_tipos_contacto():
    return jsonify(service.get_tipos_contacto())


@cliente_bp.route("/stats", methods=["GET"])
@token_required
def get_stats_clientes():
    return jsonify(service.get_stats_clientes())
