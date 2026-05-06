"""
test_cliente_service.py - Unit tests para cliente_service
"""
import pytest
from unittest.mock import patch, MagicMock


class TestGetAllClientes:
    """Tests para get_all_clientes"""
    
    def test_get_all_clientes_returns_paginated_data(self):
        """Debe retornar datos paginados correctamente"""
        mock_clientes = [
            {"id_cliente": 1, "nombre_razon_social": "Test 1"},
            {"id_cliente": 2, "nombre_razon_social": "Test 2"}
        ]
        
        with patch('services.cliente_service.repo.find_all', return_value=(mock_clientes, 2)):
            from services import cliente_service
            
            result = cliente_service.get_all_clientes(page=1, per_page=20)
            
            assert 'clientes' in result
            assert 'total' in result
            assert 'meta' in result
            assert result['total'] == 2
            assert len(result['clientes']) == 2
    
    def test_get_all_clientes_with_nombre_filter(self):
        """Debe filtrar por nombre correctamente"""
        with patch('services.cliente_service.repo.find_all', return_value=([], 0)) as mock_find:
            from services import cliente_service
            
            cliente_service.get_all_clientes(nombre="Test", page=1, per_page=20)
            
            call_args = mock_find.call_args
            where_clauses = call_args[0][0]
            params = call_args[0][1]
            
            assert any('nombre_razon_social LIKE' in clause for clause in where_clauses)
            assert '%Test%' in params
    
    def test_get_all_clientes_with_tipo_filter(self):
        """Debe filtrar por tipo correctamente"""
        with patch('services.cliente_service.repo.find_all', return_value=([], 0)) as mock_find:
            from services import cliente_service
            
            cliente_service.get_all_clientes(tipo="Cliente", page=1, per_page=20)
            
            call_args = mock_find.call_args
            where_clauses = call_args[0][0]
            params = call_args[0][1]
            
            assert any('tipo = %s' in clause for clause in where_clauses)
            assert 'Cliente' in params
    
    def test_get_all_clientes_pagination_calculation(self):
        """Debe calcular paginación correctamente"""
        with patch('services.cliente_service.repo.find_all', return_value=([], 50)):
            from services import cliente_service
            
            result = cliente_service.get_all_clientes(page=2, per_page=20)
            
            assert result['meta']['total'] == 50
            assert result['meta']['page'] == 2
            assert result['meta']['total_pages'] == 3
            assert result['meta']['has_next_page'] == True
            assert result['meta']['has_previous_page'] == True


class TestGetClienteById:
    """Tests para get_cliente_by_id"""
    
    def test_get_cliente_by_id_found(self):
        """Debe retornar cliente cuando existe"""
        mock_cliente = {"id_cliente": 1, "nombre_razon_social": "Test"}
        
        with patch('services.cliente_service.repo.find_by_id', return_value=mock_cliente):
            from services import cliente_service
            
            result = cliente_service.get_cliente_by_id(1)
            
            assert result is not None
            assert result['id_cliente'] == 1
    
    def test_get_cliente_by_id_not_found(self):
        """Debe retornar None cuando no existe"""
        with patch('services.cliente_service.repo.find_by_id', return_value=None):
            from services import cliente_service
            
            result = cliente_service.get_cliente_by_id(999)
            
            assert result is None


class TestCreateCliente:
    """Tests para create_cliente"""
    
    def test_create_cliente_success(self):
        """Debe crear cliente exitosamente"""
        with patch('services.cliente_service.repo.insert', return_value=(1, "Cliente creado")):
            from services import cliente_service
            
            data = {
                "nombre_razon_social": "Nueva Empresa",
                "documento_identificacion": "12345678"
            }
            result = cliente_service.create_cliente(data)
            
            assert 'id_cliente' in result
            assert result['id_cliente'] == 1
    
    def test_create_cliente_with_contactos(self):
        """Debe crear cliente con contactos"""
        with patch('services.cliente_service.repo.insert', return_value=(1, "Cliente creado")), \
             patch('services.cliente_service.repo.insert_contacto') as mock_insert_contacto:
            from services import cliente_service
            
            data = {
                "nombre_razon_social": "Nueva Empresa",
                "documento_identificacion": "12345678",
                "contactos": [
                    {"tipo_contacto": "Teléfono", "descripcion": "12345678"}
                ],
                "usuario": "test_user"
            }
            cliente_service.create_cliente(data)
            
            mock_insert_contacto.assert_called_once()
    
    def test_create_cliente_error(self):
        """Debe manejar errores de creación"""
        with patch('services.cliente_service.repo.insert', return_value=(None, "Error de base de datos")):
            from services import cliente_service
            
            data = {"nombre_razon_social": "Test"}
            result = cliente_service.create_cliente(data)
            
            assert 'error' in result


class TestUpdateCliente:
    """Tests para update_cliente"""
    
    def test_update_cliente_success(self):
        """Debe actualizar cliente exitosamente"""
        with patch('services.cliente_service.repo.update', return_value=(1, "Cliente actualizado")):
            from services import cliente_service
            
            data = {"nombre_razon_social": "Empresa Actualizada"}
            result = cliente_service.update_cliente(1, data)
            
            assert 'id_cliente' in result
            assert result['id_cliente'] == 1
    
    def test_update_cliente_with_new_contactos(self):
        """Debe agregar nuevos contactos al actualizar"""
        with patch('services.cliente_service.repo.update', return_value=(1, "Actualizado")), \
             patch('services.cliente_service.repo.insert_contacto') as mock_insert:
            from services import cliente_service
            
            data = {
                "nombre_razon_social": "Empresa",
                "contactos": [
                    {"descripcion": "nuevo@email.com"}
                ],
                "usuario": "test"
            }
            cliente_service.update_cliente(1, data)
            
            mock_insert.assert_called_once()
    
    def test_update_cliente_with_existing_contactos(self):
        """Debe actualizar contactos existentes"""
        with patch('services.cliente_service.repo.update', return_value=(1, "Actualizado")), \
             patch('services.cliente_service.repo.update_contacto') as mock_update:
            from services import cliente_service
            
            data = {
                "nombre_razon_social": "Empresa",
                "contactos": [
                    {"id_contacto": 5, "descripcion": "actualizado@email.com"}
                ],
                "usuario": "test"
            }
            cliente_service.update_cliente(1, data)
            
            mock_update.assert_called_once()


class TestInactivarCliente:
    """Tests para inactivar_cliente"""
    
    def test_inactivar_cliente_success(self):
        """Debe inactivar cliente exitosamente"""
        with patch('services.cliente_service.repo.set_inactive', return_value=(1, "Inactivado")):
            from services import cliente_service
            
            result = cliente_service.inactivar_cliente(1, "test_user")
            
            assert 'mensaje' in result
    
    def test_inactivar_cliente_error(self):
        """Debe manejar error al inactivar"""
        with patch('services.cliente_service.repo.set_inactive', return_value=None):
            from services import cliente_service
            
            result = cliente_service.inactivar_cliente(999, "test_user")
            
            assert 'error' in result


class TestGetTiposCliente:
    """Tests para get_tipos_cliente"""
    
    def test_get_tipos_cliente_returns_list(self):
        """Debe retornar lista de tipos"""
        from services import cliente_service
        
        result = cliente_service.get_tipos_cliente()
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert any(t['descripcion'] == 'Cliente' for t in result)
        assert any(t['descripcion'] == 'Prospecto' for t in result)


class TestGetTiposContacto:
    """Tests para get_tipos_contacto"""
    
    def test_get_tipos_contacto_returns_list(self):
        """Debe retornar lista de tipos de contacto"""
        from services import cliente_service
        
        result = cliente_service.get_tipos_contacto()
        
        assert isinstance(result, list)
        assert len(result) == 6
        descriptions = [t['descripcion'] for t in result]
        assert 'Teléfono' in descriptions
        assert 'Email' in descriptions
        assert 'Página web' in descriptions


class TestGetStatsClientes:
    """Tests para get_stats_clientes"""
    
    def test_get_stats_returns_counts(self):
        """Debe retornar conteos de clientes"""
        mock_stats = {
            "total_activos": 10,
            "total_inactivos": 2,
            "total_prospectos": 5
        }
        
        with patch('services.cliente_service.repo.get_stats_clientes', return_value=mock_stats):
            from services import cliente_service
            
            result = cliente_service.get_stats_clientes()
            
            assert result['total_activos'] == 10
            assert result['total_inactivos'] == 2
            assert result['total_prospectos'] == 5
