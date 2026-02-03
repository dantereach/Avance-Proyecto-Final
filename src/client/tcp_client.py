"""
Cliente TCP/IP para conectarse al servidor de gestión de procesos.
"""

import socket
from typing import Dict, Any, Optional

from ..middleware.message_protocol import (
    create_request,
    serialize_message,
    deserialize_message,
    CommandType
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TCPClient:
    """Cliente TCP/IP para comunicación con el servidor."""

    def __init__(self, host: str = "localhost", port: int = 9000, timeout: int = 30):
        """
        Inicializa el cliente TCP.

        Args:
            host: Dirección del servidor
            port: Puerto del servidor
            timeout: Timeout para operaciones de red
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket: Optional[socket.socket] = None
        self.connected = False
        
        logger.info(f"TCPClient inicializado para {host}:{port}")

    def connect(self) -> bool:
        """
        Conecta al servidor.

        Returns:
            True si la conexión fue exitosa, False en caso contrario
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            self.connected = True
            logger.info(f"Conectado a {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Error conectando a {self.host}:{self.port}: {e}")
            self.connected = False
            return False

    def disconnect(self) -> None:
        """Desconecta del servidor."""
        if self.socket:
            try:
                self.socket.close()
                self.connected = False
                logger.info("Desconectado del servidor")
            except:
                pass

    def send_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Envía un comando al servidor y retorna la respuesta.

        Args:
            command: Comando a ejecutar
            params: Parámetros del comando

        Returns:
            Dict con la respuesta del servidor

        Raises:
            ConnectionError: Si no hay conexión con el servidor
            Exception: Si hay error en la comunicación
        """
        if not self.connected or not self.socket:
            raise ConnectionError("No conectado al servidor")

        try:
            # Crear y serializar request
            request = create_request(command, params)
            data = serialize_message(request)
            
            # Enviar
            self.socket.sendall(data)
            logger.debug(f"Comando enviado: {command}")
            
            # Recibir respuesta
            response_data = self.socket.recv(4096)
            
            if not response_data:
                raise ConnectionError("Servidor cerró la conexión")
            
            # Deserializar respuesta
            response = deserialize_message(response_data)
            logger.debug(f"Respuesta recibida: {response.get('status')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error en comunicación: {e}")
            self.connected = False
            raise

    def list_processes(self) -> Dict[str, Any]:
        """
        Lista todos los procesos del servidor.

        Returns:
            Dict con la respuesta del servidor
        """
        return self.send_command(CommandType.LIST_PROCESSES)

    def get_process_info(self, pid: int) -> Dict[str, Any]:
        """
        Obtiene información de un proceso específico.

        Args:
            pid: ID del proceso

        Returns:
            Dict con la respuesta del servidor
        """
        return self.send_command(CommandType.GET_PROCESS_INFO, {'pid': pid})

    def start_process(self, command: str) -> Dict[str, Any]:
        """
        Inicia un nuevo proceso en el servidor.

        Args:
            command: Comando a ejecutar

        Returns:
            Dict con la respuesta del servidor
        """
        return self.send_command(CommandType.START_PROCESS, {'command': command})

    def stop_process(self, pid: int, force: bool = False) -> Dict[str, Any]:
        """
        Detiene un proceso en el servidor.

        Args:
            pid: ID del proceso
            force: Si True, usa kill; si False, usa terminate

        Returns:
            Dict con la respuesta del servidor
        """
        return self.send_command(CommandType.STOP_PROCESS, {'pid': pid, 'force': force})

    def monitor_process(self, pid: int) -> Dict[str, Any]:
        """
        Monitorea un proceso específico.

        Args:
            pid: ID del proceso

        Returns:
            Dict con la respuesta del servidor
        """
        return self.send_command(CommandType.MONITOR_PROCESS, {'pid': pid})

    def get_system_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del sistema del servidor.

        Returns:
            Dict con la respuesta del servidor
        """
        return self.send_command(CommandType.GET_SYSTEM_STATS)

    def ping(self) -> Dict[str, Any]:
        """
        Hace ping al servidor para verificar conectividad.

        Returns:
            Dict con la respuesta del servidor
        """
        return self.send_command(CommandType.PING)

    def is_connected(self) -> bool:
        """
        Verifica si está conectado al servidor.

        Returns:
            True si está conectado, False en caso contrario
        """
        return self.connected

    def get_address(self) -> str:
        """
        Obtiene la dirección del servidor.

        Returns:
            String con host:port
        """
        return f"{self.host}:{self.port}"
