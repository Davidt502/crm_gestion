"""
test_cliente_routes.py - Unit tests para endpoints de clientes
"""
import pytest
import json
from unittest.mock import patch, MagicMock


class TestGetClientes:
    """Tests para GET /api/clientes"""
    
    def test_get_clientes_success(self, client, valid_token, sample_clientes_list):
        """Debe retornar lista de clientes con código 200"""
        with patch('services.cliente_service.get_all_clientes', return_value=sample_clientes_list):
            response = client.get('/api/clientes',
                                  headers={'Authorization': f'Bearer {valid_token}'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'clientes' in data
            assert 'total' in data
    
    def test_get_clientes_with_filters(self, client, valid_token, sample_clientes_list):
        """Debe aceptar parámetros de filtro"""
        with patch('services.cliente_service.get_all_clientes', return_value=sample_clientes_list) as mock_service:
            response = client.get('/api/clientes?nombre=Test&tipo=Cliente&page=1',
                                  headers={'Authorization': f'Bearer {valid_token}'})
            
            assert response.status_code == 200
            mock_service.assert_called_once()
    
    def test_get_clientes_empty_list(self, client, valid_token):
        """Debe manejar lista vacía correctamente"""
        empty_response = {"clientes": [], "total": 0, "page": 1, "per_page": 20}
        with patch('services.cliente_service.get_all_clientes', return_value=empty_response):
            response = client.get('/api/clientes',
                                  headers={'Authorization': f'Bearer {valid_token}'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['clientes'] == []
    
    def test_get_clientes_without_auth(self, client):
        """Debe requerir autenticación"""
        response = client.get('/api/clientes')
        assert response.status_code == 401


class TestGetClienteById:
    """Tests para GET /api/clientes/:id"""
    
    def test_get_cliente_by_id_success(self, client, valid_token, sample_cliente):
        """Debe retornar cliente cuando existe"""
        with patch('services.cliente_service.get_cliente_by_id', return_value=sample_cliente):
            response = client.get('/api/clientes/1',
                                  headers={'Authorization': f'Bearer {valid_token}'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['id_cliente'] == 1
    
    def test_get_cliente_by_id_not_found(self, client, valid_token):
        """Debe retornar 404 cuando no existe"""
        with patch('services.cliente_service.get_cliente_by_id', return_value=None):
            response = client.get('/api/clientes/999',
                                  headers={'Authorization': f'Bearer {valid_token}'})
            
            assert response.status_code == 404
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_get_cliente_with_contactos(self, client, valid_token, sample_cliente):
        """Debe incluir contactos del cliente"""
        with patch('services.cliente_service.get_cliente_by_id', return_value=sample_cliente):
            response = client.get('/api/clientes/1',
                                  headers={'Authorization': f'Bearer {valid_token}'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'contactos' in data


class TestCreateCliente:
    """Tests para POST /api/clientes"""
    
    def test_create_cliente_success(self, client, valid_token):
        """Debe crear cliente y retornar 201"""
        new_cliente = {
            "nombre_razon_social": "Nueva Empresa",
            "documento_identificacion": "98765432-1",
            "tipo": "Cliente"
        }
        success_response = {"id_cliente": 2, "mensaje": "Cliente registrado exitosamente"}
        
        with patch('services.cliente_service.create_cliente', return_value=success_response):
            response = client.post('/api/clientes',
                                   data=json.dumps(new_cliente),
                                   content_type='application/json',
                                   headers={'Authorization': f'Bearer {valid_token}'})
            
            assert response.status_code == 201
            data = json.loads(response.data)
            assert 'id_cliente' in data
    
    def test_create_cliente_with_contactos(self, client, valid_token):
        """Debe crear cliente con contactos"""
        new_cliente = {
            "nombre_razon_social": "Nueva Empresa",
            "documento_identificacion": "98765432-1",
            "tipo": "Cliente",
            "contactos": [{"tipo_contacto": "Teléfono", "descripcion": "12345678"}]
        }
        success_response = {"id_cliente": 2, "mensaje": "Cliente registrado exitosamente"}
        
        with patch('services.cliente_service.create_cliente', return_value=success_response) as mock_service:
            response = client.post('/api/clientes',
                                   data=json.dumps(new_cliente),
                                   content_type='application/json',
                                   headers={'Authorization': f'Bearer {valid_token}'})
            
            assert response.status_code == 201
            call_args = mock_service.call_args[0][0]
            assert 'contactos' in call_args
    
    def test_create_cliente_validation_error(self, client, valid_token):
        """Debe retornar 400 cuando hay error de validación"""
        new_cliente = {"nombre_razon_social": "", "documento_identificacion": "", "tipo": "Cliente"}
        error_response = {"error": "El nombre es obligatorio"}
        
        with patch('services.cliente_service.create_cliente', return_value=error_response):
            response = client.post('/api/clientes',
                                   data=json.dumps(new_cliente),
                                   content_type='application/json',
                                   headers={'Authorization': f'Bearer {valid_token}'})
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_create_cliente_duplicate_document(self, client, valid_token):
        """Debe retornar 400 cuando documento ya existe"""
        new_cliente = {
            "nombre_razon_social": "Empresa Duplicada",
            "documento_identificacion": "12345678-9",
            "tipo": "Cliente"
        }
        error_response = {"error": "Ya existe un cliente con ese documento"}
        
        with patch('services.cliente_service.create_cliente', return_value=error_response):
            response = client.post('/api/clientes',
                                   data=json.dumps(new_cliente),
                                   content_type='application/json',
                                   headers={'Authorization': f'Bearer {valid_token}'})
            
            assert response.status_code == 400


class TestUpdateCliente:
    """Tests para PUT /api/clientes/:id"""
    
    def test_update_cliente_success(self, client, valid_token):
        """Debe actualizar cliente correctamente"""
        update_data = {
            "nombre_razon_social": "Empresa Actualizada",
            "documento_identificacion": "12345678-9",
            "tipo": "Cliente"
        }
        success_response = {"id_cliente": 1, "mensaje": "Cliente actualizado"}
        
        with patch('services.cliente_service.update_cliente', return_value=success_response):
            response = client.put('/api/clientes/1',
                                  data=json.dumps(update_data),
                                  content_type='application/json',
                                  headers={'Authorization': f'Bearer {valid_token}'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'mensaje' in data
    
    def test_update_cliente_error(self, client, valid_token):
        """Debe retornar 400 cuando hay error"""
        update_data = {"nombre_razon_social": "", "documento_identificacion": "12345678-9", "tipo": "Cliente"}
        error_response = {"error": "El nombre es obligatorio"}
        
        with patch('services.cliente_service.update_cliente', return_value=error_response):
            response = client.put('/api/clientes/1',
                                  data=json.dumps(update_data),
                                  content_type='application/json',
                                  headers={'Authorization': f'Bearer {valid_token}'})
            
            assert response.status_code == 400


class TestInactivarCliente:
    """Tests para PATCH /api/clientes/:id/inactivar"""
    
    def test_inactivar_cliente_success(self, client, valid_token):
        """Debe inactivar cliente correctamente"""
        success_response = {"mensaje": "Cliente inactivado exitosamente"}
        
        with patch('services.cliente_service.inactivar_cliente', return_value=success_response):
            response = client.patch('/api/clientes/1/inactivar',
                                    headers={'Authorization': f'Bearer {valid_token}'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'mensaje' in data
    
    def test_inactivar_cliente_calls_service(self, client, valid_token):
        """Debe llamar al servicio correctamente"""
        success_response = {"mensaje": "Cliente inactivado"}
        
        with patch('services.cliente_service.inactivar_cliente', return_value=success_response) as mock_service:
            client.patch('/api/clientes/5/inactivar',
                        headers={'Authorization': f'Bearer {valid_token}'})
            
            mock_service.assert_called_once()
            call_args = mock_service.call_args[0]
            assert call_args[0] == 5


class TestGetTiposCliente:
    """Tests para GET /api/clientes/tipos-cliente"""
    
    def test_get_tipos_cliente_success(self, client, valid_token, sample_tipos_cliente):
        """Debe retornar tipos de cliente"""
        with patch('services.cliente_service.get_tipos_cliente', return_value=sample_tipos_cliente):
            response = client.get('/api/clientes/tipos-cliente',
                                  headers={'Authorization': f'Bearer {valid_token}'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) == 2


class TestGetTiposContacto:
    """Tests para GET /api/clientes/tipos-contacto"""
    
    def test_get_tipos_contacto_success(self, client, valid_token, sample_tipos_contacto):
        """Debe retornar tipos de contacto"""
        with patch('services.cliente_service.get_tipos_contacto', return_value=sample_tipos_contacto):
            response = client.get('/api/clientes/tipos-contacto',
                                  headers={'Authorization': f'Bearer {valid_token}'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) == 6


class TestGetStatsClientes:
    """Tests para GET /api/clientes/stats"""
    
    def test_get_stats_success(self, client, valid_token, sample_stats):
        """Debe retornar estadísticas de clientes"""
        with patch('services.cliente_service.get_stats_clientes', return_value=sample_stats):
            response = client.get('/api/clientes/stats',
                                  headers={'Authorization': f'Bearer {valid_token}'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'total_activos' in data


class TestAuthenticationRequired:
    """Tests para verificar que los endpoints requieren autenticación"""
    
    @pytest.mark.parametrize("endpoint,method", [
        ('/api/clientes', 'GET'),
        ('/api/clientes/1', 'GET'),
        ('/api/clientes', 'POST'),
        ('/api/clientes/1', 'PUT'),
        ('/api/clientes/1/inactivar', 'PATCH'),
        ('/api/clientes/tipos-cliente', 'GET'),
        ('/api/clientes/tipos-contacto', 'GET'),
        ('/api/clientes/stats', 'GET'),
    ])
    def test_endpoints_require_auth(self, client, endpoint, method):
        """Todos los endpoints deben requerir autenticación"""
        if method == 'GET':
            response = client.get(endpoint)
        elif method == 'POST':
            response = client.post(endpoint, data='{}', content_type='application/json')
        elif method == 'PUT':
            response = client.put(endpoint, data='{}', content_type='application/json')
        elif method == 'PATCH':
            response = client.patch(endpoint)
        
        assert response.status_code == 401
    
    def test_invalid_token_rejected(self, client):
        """Debe rechazar tokens inválidos"""
        response = client.get('/api/clientes',
                              headers={'Authorization': 'Bearer invalid-token'})
        assert response.status_code == 401
    
    def test_expired_token_rejected(self, client):
        """Debe rechazar tokens expirados"""
        import jwt
        from datetime import datetime, timedelta
        
        expired_payload = {
            'username': 'test',
            'exp': datetime.utcnow() - timedelta(hours=1)
        }
        expired_token = jwt.encode(expired_payload, 'test-secret-key-for-testing', algorithm='HS256')
        
        response = client.get('/api/clientes',
                              headers={'Authorization': f'Bearer {expired_token}'})
        assert response.status_code == 401
