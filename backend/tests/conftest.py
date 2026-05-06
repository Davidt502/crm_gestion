"""
conftest.py - Configuración de fixtures para pytest
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
import jwt
from datetime import datetime, timedelta

TEST_SECRET_KEY = 'test-secret-key-for-testing'


@pytest.fixture
def app():
    """Crea una instancia de la aplicación Flask para testing"""
    with patch('config.SECRET_KEY', TEST_SECRET_KEY):
        with patch('middleware.auth_middleware.SECRET_KEY', TEST_SECRET_KEY):
            from routes.cliente_routes import cliente_bp
            
            app = Flask(__name__)
            app.config['TESTING'] = True
            app.config['SECRET_KEY'] = TEST_SECRET_KEY
            app.register_blueprint(cliente_bp)
            return app


@pytest.fixture
def client(app):
    """Crea un cliente de testing"""
    return app.test_client()


@pytest.fixture
def valid_token():
    """Genera un token JWT válido para testing"""
    payload = {
        'username': 'test_user',
        'nombre': 'Test User',
        'rol': 'admin',
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, TEST_SECRET_KEY, algorithm='HS256')


@pytest.fixture
def auth_headers():
    """Headers de autenticación para las peticiones"""
    return {'Authorization': 'Bearer test-token-valid'}


@pytest.fixture
def mock_token_required():
    """Mock del decorator token_required para bypasear autenticación"""
    with patch('routes.cliente_routes.token_required', lambda f: f):
        yield


@pytest.fixture
def mock_get_usuario():
    """Mock de get_usuario para retornar un usuario de prueba"""
    with patch('routes.cliente_routes.get_usuario', return_value='test_user'):
        yield


@pytest.fixture
def sample_cliente():
    """Datos de ejemplo de un cliente"""
    return {
        "id_cliente": 1,
        "nombre_razon_social": "Empresa Test S.A.",
        "documento_identificacion": "12345678-9",
        "tipo": "Cliente",
        "estado": "Activo",
        "fecha_nacimiento": "1990-01-15",
        "correo": "test@empresa.com",
        "notificacion_email": True,
        "notificacion_sms": False,
        "fecha_creacion": "2024-01-01 10:00:00",
        "contactos": [
            {
                "id_contacto": 1,
                "nombre_contacto": "Contacto Principal",
                "tipo_contacto": "Teléfono",
                "descripcion": "12345678",
                "correo": None,
                "telefono": "12345678",
                "estado": "Activo"
            }
        ]
    }


@pytest.fixture
def sample_clientes_list(sample_cliente):
    """Lista de clientes para testing de paginación"""
    return {
        "data": [sample_cliente],
        "meta": {
            "total": 1,
            "page": 1,
            "limit": 20,
            "total_pages": 1,
            "has_next_page": False,
            "has_previous_page": False
        },
        "clientes": [sample_cliente],
        "total": 1,
        "page": 1,
        "per_page": 20
    }


@pytest.fixture
def sample_tipos_cliente():
    """Tipos de cliente disponibles"""
    return [
        {"id": 1, "descripcion": "Cliente"},
        {"id": 2, "descripcion": "Prospecto"}
    ]


@pytest.fixture
def sample_tipos_contacto():
    """Tipos de contacto disponibles"""
    return [
        {"id": 1, "descripcion": "Teléfono"},
        {"id": 2, "descripcion": "Celular"},
        {"id": 3, "descripcion": "Email"},
        {"id": 4, "descripcion": "Dirección"},
        {"id": 5, "descripcion": "Fax"},
        {"id": 6, "descripcion": "Página web"}
    ]


@pytest.fixture
def sample_stats():
    """Estadísticas de clientes"""
    return {
        "total_activos": 10,
        "total_inactivos": 2,
        "total_prospectos": 5
    }
