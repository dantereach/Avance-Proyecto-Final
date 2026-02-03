"""
Tests para el ProcessManager.
"""

import pytest
import psutil
import subprocess
from unittest.mock import Mock, patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.server.process_manager import ProcessManager


class TestProcessManager:
    """Tests para la clase ProcessManager."""

    def setup_method(self):
        """Setup para cada test."""
        self.pm = ProcessManager()

    def test_init(self):
        """Test de inicialización."""
        assert self.pm is not None

    def test_list_processes(self):
        """Test de listar procesos."""
        processes = self.pm.list_processes()
        
        assert isinstance(processes, list)
        assert len(processes) > 0
        
        # Verificar estructura de proceso
        proc = processes[0]
        assert 'pid' in proc
        assert 'name' in proc
        assert 'status' in proc
        assert 'cpu_percent' in proc
        assert 'memory_percent' in proc

    def test_get_process_info_current(self):
        """Test de obtener info del proceso actual."""
        current_pid = os.getpid()
        info = self.pm.get_process_info(current_pid)
        
        assert info['pid'] == current_pid
        assert 'name' in info
        assert 'status' in info
        assert 'cpu_percent' in info
        assert 'memory_percent' in info
        assert 'memory_rss' in info

    def test_get_process_info_invalid(self):
        """Test de obtener info de proceso inválido."""
        with pytest.raises(psutil.NoSuchProcess):
            self.pm.get_process_info(999999)

    def test_start_process_simple(self):
        """Test de iniciar un proceso simple."""
        # Usar comando multiplataforma
        import platform
        if platform.system() == 'Windows':
            cmd = 'timeout /t 5'
        else:
            cmd = 'sleep 5'
        
        result = self.pm.start_process(cmd)
        
        assert result['status'] == 'running'
        assert 'pid' in result
        assert result['pid'] > 0
        
        # Limpiar: detener el proceso
        try:
            proc = psutil.Process(result['pid'])
            proc.kill()
        except:
            pass

    def test_start_process_invalid(self):
        """Test de iniciar proceso con comando inválido."""
        with pytest.raises(subprocess.SubprocessError):
            self.pm.start_process('comando_que_no_existe_xyz123')

    def test_stop_process(self):
        """Test de detener un proceso."""
        # Iniciar proceso
        import platform
        if platform.system() == 'Windows':
            cmd = 'timeout /t 60'
        else:
            cmd = 'sleep 60'
        
        start_result = self.pm.start_process(cmd)
        pid = start_result['pid']
        
        # Detener proceso
        stop_result = self.pm.stop_process(pid)
        
        assert stop_result['status'] == 'success'
        assert stop_result['pid'] == pid

    def test_monitor_process_current(self):
        """Test de monitorear el proceso actual."""
        current_pid = os.getpid()
        stats = self.pm.monitor_process(current_pid)
        
        assert stats['pid'] == current_pid
        assert 'cpu_percent' in stats
        assert 'memory_percent' in stats
        assert 'memory_rss_mb' in stats
        assert 'num_threads' in stats

    def test_get_system_stats(self):
        """Test de obtener estadísticas del sistema."""
        stats = self.pm.get_system_stats()
        
        assert 'cpu' in stats
        assert 'memory' in stats
        assert 'disk' in stats
        assert 'system' in stats
        
        # Verificar CPU
        assert 'percent' in stats['cpu']
        assert 'count' in stats['cpu']
        
        # Verificar memoria
        assert 'total_gb' in stats['memory']
        assert 'used_gb' in stats['memory']
        assert 'percent' in stats['memory']
        
        # Verificar disco
        assert 'total_gb' in stats['disk']
        assert 'percent' in stats['disk']
