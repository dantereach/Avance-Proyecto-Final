"""
Tests para el LoadBalancer.
"""

import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.middleware.load_balancer import LoadBalancer


class TestLoadBalancer:
    """Tests para la clase LoadBalancer."""

    def setup_method(self):
        """Setup para cada test."""
        self.lb = LoadBalancer(strategy='round_robin')

    def test_init_round_robin(self):
        """Test de inicialización con round-robin."""
        lb = LoadBalancer(strategy='round_robin')
        assert lb.strategy == 'round_robin'
        assert len(lb.servers) == 0

    def test_init_least_loaded(self):
        """Test de inicialización con least-loaded."""
        lb = LoadBalancer(strategy='least_loaded')
        assert lb.strategy == 'least_loaded'

    def test_add_server(self):
        """Test de agregar servidor."""
        self.lb.add_server('srv1', 'localhost', 9000)
        
        assert len(self.lb.servers) == 1
        assert self.lb.servers[0]['server_id'] == 'srv1'
        assert self.lb.servers[0]['host'] == 'localhost'
        assert self.lb.servers[0]['port'] == 9000

    def test_add_multiple_servers(self):
        """Test de agregar múltiples servidores."""
        self.lb.add_server('srv1', 'localhost', 9000)
        self.lb.add_server('srv2', 'localhost', 9001)
        self.lb.add_server('srv3', 'localhost', 9002)
        
        assert len(self.lb.servers) == 3

    def test_remove_server(self):
        """Test de eliminar servidor."""
        self.lb.add_server('srv1', 'localhost', 9000)
        self.lb.add_server('srv2', 'localhost', 9001)
        
        self.lb.remove_server('srv1')
        
        assert len(self.lb.servers) == 1
        assert self.lb.servers[0]['server_id'] == 'srv2'

    def test_get_next_server_empty(self):
        """Test de obtener servidor cuando no hay ninguno."""
        server = self.lb.get_next_server()
        assert server is None

    def test_get_next_server_round_robin(self):
        """Test de round-robin."""
        self.lb.add_server('srv1', 'localhost', 9000)
        self.lb.add_server('srv2', 'localhost', 9001)
        self.lb.add_server('srv3', 'localhost', 9002)
        
        # Debe rotar entre servidores
        s1 = self.lb.get_next_server()
        s2 = self.lb.get_next_server()
        s3 = self.lb.get_next_server()
        s4 = self.lb.get_next_server()
        
        # El cuarto debe ser igual al primero (ciclo completo)
        assert s1['server_id'] == s4['server_id']

    def test_get_next_server_least_loaded(self):
        """Test de least-loaded."""
        lb = LoadBalancer(strategy='least_loaded')
        
        lb.add_server('srv1', 'localhost', 9000)
        lb.add_server('srv2', 'localhost', 9001)
        
        # Registrar requests
        lb.record_request('srv1')
        lb.record_request('srv1')
        lb.record_request('srv2')
        
        # Debe retornar srv2 (menos cargado)
        server = lb.get_next_server()
        assert server['server_id'] == 'srv2'

    def test_record_request_success(self):
        """Test de registrar request exitoso."""
        self.lb.add_server('srv1', 'localhost', 9000)
        
        self.lb.record_request('srv1', success=True)
        
        stats = self.lb.get_stats()
        assert stats['srv1']['requests'] == 1
        assert stats['srv1']['errors'] == 0

    def test_record_request_error(self):
        """Test de registrar request con error."""
        self.lb.add_server('srv1', 'localhost', 9000)
        
        self.lb.record_request('srv1', success=False)
        
        stats = self.lb.get_stats()
        assert stats['srv1']['requests'] == 1
        assert stats['srv1']['errors'] == 1

    def test_mark_server_inactive(self):
        """Test de marcar servidor como inactivo."""
        self.lb.add_server('srv1', 'localhost', 9000)
        
        self.lb.mark_server_inactive('srv1')
        
        assert self.lb.servers[0]['active'] is False

    def test_mark_server_active(self):
        """Test de marcar servidor como activo."""
        self.lb.add_server('srv1', 'localhost', 9000)
        self.lb.mark_server_inactive('srv1')
        
        self.lb.mark_server_active('srv1')
        
        assert self.lb.servers[0]['active'] is True

    def test_get_servers_active_only(self):
        """Test de obtener solo servidores activos."""
        self.lb.add_server('srv1', 'localhost', 9000)
        self.lb.add_server('srv2', 'localhost', 9001)
        
        self.lb.mark_server_inactive('srv1')
        
        active = self.lb.get_servers()
        assert len(active) == 1
        assert active[0]['server_id'] == 'srv2'

    def test_update_servers(self):
        """Test de actualizar servidores desde diccionario."""
        servers_dict = {
            'srv1': {'host': 'localhost', 'port': 9000, 'active': True},
            'srv2': {'host': 'localhost', 'port': 9001, 'active': True}
        }
        
        self.lb.update_servers(servers_dict)
        
        assert len(self.lb.servers) == 2
