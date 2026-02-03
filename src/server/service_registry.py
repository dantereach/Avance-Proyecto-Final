"""
Registro centralizado de servicios para descubrimiento distribuido.
"""

import socket
import threading
import time
from typing import Dict, Any
from datetime import datetime, timedelta

from ..middleware.message_protocol import (
    deserialize_message,
    serialize_message,
    create_response,
    ResponseStatus,
    MessageType
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ServiceRegistry:
    """Registro centralizado de servidores disponibles."""

    def __init__(self, host: str = "0.0.0.0", port: int = 9001, 
                 heartbeat_timeout: int = 15, cleanup_interval: int = 10):
        """
        Inicializa el registro de servicios.

        Args:
            host: Dirección IP para escuchar
            port: Puerto de escucha
            heartbeat_timeout: Timeout en segundos para marcar servidor como caído
            cleanup_interval: Intervalo de limpieza en segundos
        """
        self.host = host
        self.port = port
        self.heartbeat_timeout = heartbeat_timeout
        self.cleanup_interval = cleanup_interval
        
        # Diccionario de servidores: server_id -> metadata
        self.servers: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        
        self.running = False
        self.server_socket: socket.socket = None
        self.cleanup_thread: threading.Thread = None
        
        logger.info(f"ServiceRegistry inicializado en {host}:{port}")

    def start(self) -> None:
        """Inicia el registro de servicios."""
        try:
            # Socket UDP para recibir heartbeats
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.settimeout(1.0)
            
            self.running = True
            logger.info(f"ServiceRegistry escuchando en {self.host}:{self.port}")
            
            # Thread de limpieza
            self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            self.cleanup_thread.start()
            
            # Loop principal
            while self.running:
                try:
                    data, addr = self.server_socket.recvfrom(4096)
                    self._handle_message(data, addr)
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        logger.error(f"Error recibiendo mensaje: {e}")
                        
        except Exception as e:
            logger.error(f"Error iniciando ServiceRegistry: {e}")
            raise
        finally:
            self.shutdown()

    def _handle_message(self, data: bytes, addr: tuple) -> None:
        """
        Maneja un mensaje recibido.

        Args:
            data: Datos recibidos
            addr: Dirección del emisor
        """
        try:
            message = deserialize_message(data)
            msg_type = message.get('type')
            
            if msg_type == MessageType.HEARTBEAT:
                self._handle_heartbeat(message, addr)
            elif msg_type == MessageType.ANNOUNCEMENT:
                self._handle_announcement(message, addr)
            else:
                logger.warning(f"Tipo de mensaje desconocido: {msg_type}")
                
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")

    def _handle_heartbeat(self, message: dict, addr: tuple) -> None:
        """
        Maneja un mensaje de heartbeat.

        Args:
            message: Mensaje de heartbeat
            addr: Dirección del emisor
        """
        server_id = message.get('server_id')
        metadata = message.get('metadata', {})
        
        if not server_id:
            logger.warning("Heartbeat sin server_id")
            return
        
        with self.lock:
            if server_id in self.servers:
                # Actualizar timestamp
                self.servers[server_id]['last_heartbeat'] = datetime.now()
                self.servers[server_id]['active'] = True
                logger.debug(f"Heartbeat actualizado para {server_id}")
            else:
                logger.info(f"Servidor desconocido envió heartbeat: {server_id}")

    def _handle_announcement(self, message: dict, addr: tuple) -> None:
        """
        Maneja un mensaje de anuncio de servidor.

        Args:
            message: Mensaje de anuncio
            addr: Dirección del emisor
        """
        server_id = message.get('server_id')
        host = message.get('host')
        port = message.get('port')
        metadata = message.get('metadata', {})
        
        if not all([server_id, host, port]):
            logger.warning("Anuncio incompleto")
            return
        
        with self.lock:
            self.servers[server_id] = {
                'server_id': server_id,
                'host': host,
                'port': port,
                'metadata': metadata,
                'last_heartbeat': datetime.now(),
                'active': True,
                'registered_at': datetime.now().isoformat()
            }
        
        logger.info(f"Servidor registrado: {server_id} ({host}:{port})")

    def _cleanup_loop(self) -> None:
        """Loop de limpieza de servidores inactivos."""
        while self.running:
            time.sleep(self.cleanup_interval)
            self._cleanup_inactive_servers()

    def _cleanup_inactive_servers(self) -> None:
        """Marca como inactivos los servidores que no han enviado heartbeat."""
        now = datetime.now()
        timeout = timedelta(seconds=self.heartbeat_timeout)
        
        with self.lock:
            for server_id, info in list(self.servers.items()):
                last_heartbeat = info.get('last_heartbeat')
                if last_heartbeat and (now - last_heartbeat) > timeout:
                    if info.get('active', False):
                        info['active'] = False
                        logger.warning(f"Servidor {server_id} marcado como inactivo (timeout)")

    def get_servers(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene la lista de todos los servidores registrados.

        Returns:
            Dict con información de servidores
        """
        with self.lock:
            return dict(self.servers)

    def get_active_servers(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene solo los servidores activos.

        Returns:
            Dict con servidores activos
        """
        with self.lock:
            return {
                sid: info for sid, info in self.servers.items()
                if info.get('active', False)
            }

    def shutdown(self) -> None:
        """Detiene el registro de servicios."""
        logger.info("Deteniendo ServiceRegistry...")
        self.running = False
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        logger.info("ServiceRegistry detenido")


def main():
    """Función principal para ejecutar el registro."""
    from ..utils.logger import setup_logger
    from ..utils.config import get_config
    
    # Configurar logging
    config = get_config()
    log_config = config.get_section('logging')
    setup_logger(
        'src.server',
        level=log_config.get('level', 'INFO'),
        log_format=log_config.get('format'),
        log_file=log_config.get('file'),
        console=log_config.get('console', True)
    )
    
    # Configurar registro
    registry_config = config.get_section('registry')
    registry = ServiceRegistry(
        host=registry_config.get('host', '0.0.0.0'),
        port=registry_config.get('port', 9001),
        heartbeat_timeout=registry_config.get('timeout', 15),
        cleanup_interval=registry_config.get('cleanup_interval', 10)
    )
    
    try:
        registry.start()
    except KeyboardInterrupt:
        logger.info("ServiceRegistry interrumpido por usuario")
        registry.shutdown()


if __name__ == '__main__':
    main()
