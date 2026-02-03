"""
Tests para el TCPServer y TCPClient.
"""

import pytest
import threading
import time

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.server.tcp_server import TCPServer
from src.client.tcp_client import TCPClient


class TestTCPServerClient:
    """Tests de integración para servidor y cliente TCP."""

    def setup_method(self):
        """Setup para cada test."""
        # Usar puerto diferente para tests
        self.host = 'localhost'
        self.port = 19000
        self.server = None
        self.client = None
        self.server_thread = None

    def teardown_method(self):
        """Cleanup después de cada test."""
        if self.client:
            self.client.disconnect()
        
        if self.server:
            self.server.shutdown()
        
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=2)

    def _start_server(self):
        """Inicia el servidor en un thread."""
        self.server = TCPServer(self.host, self.port, buffer_size=4096)
        self.server_thread = threading.Thread(target=self.server.start, daemon=True)
        self.server_thread.start()
        time.sleep(0.5)  # Dar tiempo para que inicie

    def test_server_start(self):
        """Test de inicio del servidor."""
        self._start_server()
        assert self.server.running is True

    def test_client_connect(self):
        """Test de conexión del cliente."""
        self._start_server()
        
        self.client = TCPClient(self.host, self.port)
        connected = self.client.connect()
        
        assert connected is True
        assert self.client.is_connected() is True

    def test_ping_command(self):
        """Test del comando ping."""
        self._start_server()
        
        self.client = TCPClient(self.host, self.port)
        self.client.connect()
        
        response = self.client.ping()
        
        assert response['status'] == 'success'
        assert 'data' in response

    def test_list_processes_command(self):
        """Test del comando list_processes."""
        self._start_server()
        
        self.client = TCPClient(self.host, self.port)
        self.client.connect()
        
        response = self.client.list_processes()
        
        assert response['status'] == 'success'
        assert 'data' in response
        assert isinstance(response['data'], list)

    def test_get_system_stats_command(self):
        """Test del comando get_system_stats."""
        self._start_server()
        
        self.client = TCPClient(self.host, self.port)
        self.client.connect()
        
        response = self.client.get_system_stats()
        
        assert response['status'] == 'success'
        assert 'data' in response
        assert 'cpu' in response['data']
        assert 'memory' in response['data']

    def test_get_process_info_command(self):
        """Test del comando get_process_info."""
        self._start_server()
        
        self.client = TCPClient(self.host, self.port)
        self.client.connect()
        
        # Obtener PID del proceso actual
        current_pid = os.getpid()
        response = self.client.get_process_info(current_pid)
        
        assert response['status'] == 'success'
        assert 'data' in response
        assert response['data']['pid'] == current_pid

    def test_invalid_command(self):
        """Test de comando inválido."""
        self._start_server()
        
        self.client = TCPClient(self.host, self.port)
        self.client.connect()
        
        response = self.client.send_command('invalid_command_xyz')
        
        assert response['status'] == 'error'

    def test_multiple_clients(self):
        """Test de múltiples clientes conectados."""
        self._start_server()
        
        # Conectar múltiples clientes
        clients = []
        for i in range(3):
            client = TCPClient(self.host, self.port)
            client.connect()
            clients.append(client)
        
        # Todos deben poder hacer ping
        for client in clients:
            response = client.ping()
            assert response['status'] == 'success'
        
        # Desconectar todos
        for client in clients:
            client.disconnect()
