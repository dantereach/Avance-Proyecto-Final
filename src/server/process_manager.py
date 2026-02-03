"""
Gestión y monitoreo de procesos del sistema usando psutil.
"""

import psutil
import subprocess
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ProcessManager:
    """Clase para gestionar procesos del sistema operativo."""

    def __init__(self):
        """Inicializa el gestor de procesos."""
        logger.info("ProcessManager inicializado")

    def list_processes(self) -> List[Dict[str, Any]]:
        """
        Lista todos los procesos activos en el sistema.

        Returns:
            Lista de diccionarios con información de cada proceso
        """
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'status', 'username', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                processes.append({
                    'pid': pinfo['pid'],
                    'name': pinfo['name'],
                    'status': pinfo['status'],
                    'username': pinfo['username'],
                    'cpu_percent': round(pinfo['cpu_percent'] or 0.0, 2),
                    'memory_percent': round(pinfo['memory_percent'] or 0.0, 2)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        logger.info(f"Listados {len(processes)} procesos")
        return processes

    def get_process_info(self, pid: int) -> Dict[str, Any]:
        """
        Obtiene información detallada de un proceso específico.

        Args:
            pid: ID del proceso

        Returns:
            Dict con información detallada del proceso

        Raises:
            psutil.NoSuchProcess: Si el proceso no existe
            psutil.AccessDenied: Si no hay permisos para acceder al proceso
        """
        try:
            proc = psutil.Process(pid)
            
            # Obtener información de memoria
            memory_info = proc.memory_info()
            
            # Obtener información de CPU
            cpu_percent = proc.cpu_percent(interval=0.1)
            
            # Obtener estado
            with proc.oneshot():
                info = {
                    'pid': proc.pid,
                    'name': proc.name(),
                    'status': proc.status(),
                    'username': proc.username(),
                    'create_time': datetime.fromtimestamp(proc.create_time()).isoformat(),
                    'cpu_percent': round(cpu_percent, 2),
                    'memory_percent': round(proc.memory_percent(), 2),
                    'memory_rss': memory_info.rss,
                    'memory_vms': memory_info.vms,
                    'num_threads': proc.num_threads(),
                    'cmdline': ' '.join(proc.cmdline()) if proc.cmdline() else ''
                }
            
            logger.info(f"Información obtenida para proceso {pid}")
            return info
            
        except psutil.NoSuchProcess:
            logger.error(f"Proceso {pid} no existe")
            raise
        except psutil.AccessDenied:
            logger.error(f"Acceso denegado al proceso {pid}")
            raise

    def start_process(self, command: str) -> Dict[str, Any]:
        """
        Inicia un nuevo proceso.

        Args:
            command: Comando a ejecutar

        Returns:
            Dict con información del proceso iniciado

        Raises:
            subprocess.SubprocessError: Si hay error al iniciar el proceso
        """
        try:
            # Separar comando y argumentos
            cmd_parts = command.split()
            
            # Iniciar proceso
            process = subprocess.Popen(
                cmd_parts,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Esperar un momento para verificar que el proceso se inició
            time.sleep(0.1)
            
            # Verificar si el proceso está corriendo
            if process.poll() is not None:
                # El proceso terminó inmediatamente
                stdout, stderr = process.communicate()
                raise subprocess.SubprocessError(
                    f"El proceso terminó inmediatamente. Error: {stderr}"
                )
            
            logger.info(f"Proceso iniciado: {command} (PID: {process.pid})")
            
            return {
                'pid': process.pid,
                'command': command,
                'status': 'running',
                'message': f'Proceso iniciado exitosamente con PID {process.pid}'
            }
            
        except FileNotFoundError:
            logger.error(f"Comando no encontrado: {command}")
            raise subprocess.SubprocessError(f"Comando no encontrado: {command}")
        except Exception as e:
            logger.error(f"Error al iniciar proceso: {e}")
            raise subprocess.SubprocessError(f"Error al iniciar proceso: {e}")

    def stop_process(self, pid: int, force: bool = False) -> Dict[str, Any]:
        """
        Detiene un proceso por su PID.

        Args:
            pid: ID del proceso a detener
            force: Si True, usa kill; si False, usa terminate

        Returns:
            Dict con resultado de la operación

        Raises:
            psutil.NoSuchProcess: Si el proceso no existe
            psutil.AccessDenied: Si no hay permisos
        """
        try:
            proc = psutil.Process(pid)
            proc_name = proc.name()
            
            if force:
                proc.kill()
                action = "killed"
                logger.info(f"Proceso {pid} ({proc_name}) killed")
            else:
                proc.terminate()
                action = "terminated"
                logger.info(f"Proceso {pid} ({proc_name}) terminated")
            
            # Esperar a que termine
            try:
                proc.wait(timeout=5)
            except psutil.TimeoutExpired:
                logger.warning(f"Proceso {pid} no terminó después de 5 segundos")
            
            return {
                'pid': pid,
                'name': proc_name,
                'action': action,
                'status': 'success',
                'message': f'Proceso {pid} ({proc_name}) {action} exitosamente'
            }
            
        except psutil.NoSuchProcess:
            logger.error(f"Proceso {pid} no existe")
            raise
        except psutil.AccessDenied:
            logger.error(f"Acceso denegado al proceso {pid}")
            raise

    def monitor_process(self, pid: int) -> Dict[str, Any]:
        """
        Monitorea el uso de CPU y memoria de un proceso.

        Args:
            pid: ID del proceso a monitorear

        Returns:
            Dict con estadísticas de CPU y memoria

        Raises:
            psutil.NoSuchProcess: Si el proceso no existe
        """
        try:
            proc = psutil.Process(pid)
            
            # Obtener métricas
            cpu_percent = proc.cpu_percent(interval=0.5)
            memory_info = proc.memory_info()
            memory_percent = proc.memory_percent()
            
            stats = {
                'pid': pid,
                'name': proc.name(),
                'cpu_percent': round(cpu_percent, 2),
                'memory_percent': round(memory_percent, 2),
                'memory_rss_mb': round(memory_info.rss / (1024 * 1024), 2),
                'memory_vms_mb': round(memory_info.vms / (1024 * 1024), 2),
                'num_threads': proc.num_threads(),
                'status': proc.status(),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.debug(f"Estadísticas de proceso {pid}: CPU={cpu_percent}%, MEM={memory_percent}%")
            return stats
            
        except psutil.NoSuchProcess:
            logger.error(f"Proceso {pid} no existe")
            raise

    def get_system_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales del sistema.

        Returns:
            Dict con estadísticas del sistema
        """
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        # Memoria
        memory = psutil.virtual_memory()
        
        # Disco
        disk = psutil.disk_usage('/')
        
        # Sistema
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        
        stats = {
            'cpu': {
                'percent': round(cpu_percent, 2),
                'count': cpu_count,
                'frequency_mhz': round(cpu_freq.current, 2) if cpu_freq else None
            },
            'memory': {
                'total_gb': round(memory.total / (1024 ** 3), 2),
                'available_gb': round(memory.available / (1024 ** 3), 2),
                'used_gb': round(memory.used / (1024 ** 3), 2),
                'percent': round(memory.percent, 2)
            },
            'disk': {
                'total_gb': round(disk.total / (1024 ** 3), 2),
                'used_gb': round(disk.used / (1024 ** 3), 2),
                'free_gb': round(disk.free / (1024 ** 3), 2),
                'percent': round(disk.percent, 2)
            },
            'system': {
                'boot_time': boot_time.isoformat(),
                'platform': psutil.LINUX if hasattr(psutil, 'LINUX') else 'unknown'
            },
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info("Estadísticas del sistema obtenidas")
        return stats
