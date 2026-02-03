"""
Descubrimiento de servicios usando broadcast UDP.
"""

import socket
import threading
import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from ..middleware.message_protocol import (
    create_announcement,
    create_heartbeat,
    serialize_message,
    deserialize_message,
    MessageType
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ServiceDiscovery:
    """Cliente para descubrimiento de servidores en la red."""

    def __init__(self, broadcast_port: int = 9002, discovery_timeout: int = 10):
        """
        Inicializa el descubrimiento de servicios.

        Args:
            broadcast_port: Puerto para broadcast UDP
            discovery_timeout: Timeout para marcar servidor como inactivo
        """
        self.broadcast_port = broadcast_port
        self.discovery_timeout = discovery_timeout
        
        # Servidores descubiertos
        self.servers: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        
        self.running = False
        self.listen_socket: Optional[socket.socket] = None
        self.listen_thread: Optional[threading.Thread] = None
        
        logger.info(f"ServiceDiscovery inicializado en puerto {broadcast_port}")

    def start_discovery(self) -> None:
        """Inicia el descubrimiento de servidores."""
        if self.running:
            return
        
        try:
            # Socket UDP para escuchar anuncios
            self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.listen_socket.bind(('', self.broadcast_port))
            self.listen_socket.settimeout(1.0)
            
            self.running = True
            
            # Thread para escuchar
            self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.listen_thread.start()
            
            logger.info(f"Descubrimiento iniciado en puerto {self.broadcast_port}")
            
        except Exception as e:
            logger.error(f"Error iniciando descubrimiento: {e}")
            raise

    def stop_discovery(self) -> None:
        """Detiene el descubrimiento."""
        logger.info("Deteniendo descubrimiento...")
        self.running = False
        
        if self.listen_socket:
            try:
                self.listen_socket.close()
            except:
                pass
        
        logger.info("Descubrimiento detenido")

    def _listen_loop(self) -> None:
        """Loop para escuchar anuncios de servidores."""
        while self.running:
            try:
                data, addr = self.listen_socket.recvfrom(4096)
                self._handle_announcement(data, addr)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Error recibiendo anuncio: {e}")

    def _handle_announcement(self, data: bytes, addr: tuple) -> None:
        """
        Maneja un anuncio de servidor.

        Args:
            data: Datos recibidos
            addr: Dirección del emisor
        """
        try:
            message = deserialize_message(data)
            msg_type = message.get('type')
            
            if msg_type in [MessageType.ANNOUNCEMENT, MessageType.HEARTBEAT]:
                server_id = message.get('server_id')
                host = message.get('host', addr[0])
                port = message.get('port')
                metadata = message.get('metadata', {})
                
                if server_id and port:
                    with self.lock:
                        self.servers[server_id] = {
                            'server_id': server_id,
                            'host': host,
                            'port': port,
                            'metadata': metadata,
                            'last_seen': datetime.now(),
                            'active': True
                        }
                    
                    logger.debug(f"Servidor descubierto: {server_id} ({host}:{port})")
                    
        except Exception as e:
            logger.error(f"Error procesando anuncio: {e}")

    def get_servers(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene todos los servidores descubiertos.

        Returns:
            Dict con servidores descubiertos
        """
        # Actualizar estados
        self._update_server_status()
        
        with self.lock:
            return dict(self.servers)

    def get_active_servers(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene solo servidores activos.

        Returns:
            Dict con servidores activos
        """
        self._update_server_status()
        
        with self.lock:
            return {
                sid: info for sid, info in self.servers.items()
                if info.get('active', False)
            }

    def _update_server_status(self) -> None:
        """Actualiza el estado de los servidores basado en last_seen."""
        now = datetime.now()
        timeout = timedelta(seconds=self.discovery_timeout)
        
        with self.lock:
            for server_id, info in self.servers.items():
                last_seen = info.get('last_seen')
                if last_seen and (now - last_seen) > timeout:
                    if info.get('active', False):
                        info['active'] = False
                        logger.warning(f"Servidor {server_id} marcado como inactivo")


class ServerAnnouncer:
    """Anuncia un servidor en la red usando UDP broadcast."""

    def __init__(self, server_id: str, host: str, port: int,
                 broadcast_port: int = 9002, announcement_interval: int = 5):
        """
        Inicializa el anunciador de servidor.

        Args:
            server_id: ID único del servidor
            host: Host del servidor
            port: Puerto del servidor
            broadcast_port: Puerto de broadcast
            announcement_interval: Intervalo de anuncio en segundos
        """
        self.server_id = server_id
        self.host = host
        self.port = port
        self.broadcast_port = broadcast_port
        self.announcement_interval = announcement_interval
        
        self.running = False
        self.announce_thread: Optional[threading.Thread] = None
        self.broadcast_socket: Optional[socket.socket] = None
        
        logger.info(f"ServerAnnouncer inicializado para {server_id}")

    def start(self) -> None:
        """Inicia el anuncio del servidor."""
        if self.running:
            return
        
        try:
            # Socket UDP para broadcast
            self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            self.running = True
            
            # Thread de anuncio
            self.announce_thread = threading.Thread(target=self._announce_loop, daemon=True)
            self.announce_thread.start()
            
            logger.info(f"Anuncio de servidor iniciado")
            
        except Exception as e:
            logger.error(f"Error iniciando anuncio: {e}")
            raise

    def stop(self) -> None:
        """Detiene el anuncio del servidor."""
        logger.info("Deteniendo anuncio de servidor...")
        self.running = False
        
        if self.broadcast_socket:
            try:
                self.broadcast_socket.close()
            except:
                pass
        
        logger.info("Anuncio de servidor detenido")

    def _announce_loop(self) -> None:
        """Loop de anuncio periódico."""
        while self.running:
            try:
                # Crear mensaje de anuncio
                announcement = create_announcement(
                    self.server_id,
                    self.host,
                    self.port
                )
                
                # Serializar y enviar broadcast
                data = serialize_message(announcement)
                self.broadcast_socket.sendto(
                    data,
                    ('<broadcast>', self.broadcast_port)
                )
                
                logger.debug(f"Anuncio enviado: {self.server_id}")
                
            except Exception as e:
                if self.running:
                    logger.error(f"Error enviando anuncio: {e}")
            
            # Esperar antes del siguiente anuncio
            time.sleep(self.announcement_interval)
