"""
Protocolo de mensajes JSON para la comunicación cliente-servidor.
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional


# Constantes del protocolo
class MessageType:
    """Tipos de mensajes soportados."""
    REQUEST = "request"
    RESPONSE = "response"
    HEARTBEAT = "heartbeat"
    ANNOUNCEMENT = "announcement"


class CommandType:
    """Comandos disponibles."""
    LIST_PROCESSES = "list_processes"
    GET_PROCESS_INFO = "get_process_info"
    START_PROCESS = "start_process"
    STOP_PROCESS = "stop_process"
    MONITOR_PROCESS = "monitor_process"
    GET_SYSTEM_STATS = "get_system_stats"
    REGISTER_SERVER = "register_server"
    UNREGISTER_SERVER = "unregister_server"
    LIST_SERVERS = "list_servers"
    PING = "ping"


class ResponseStatus:
    """Estados de respuesta."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


def create_request(command: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Crea un mensaje de request.

    Args:
        command: Comando a ejecutar
        params: Parámetros del comando

    Returns:
        Dict con la estructura del request
    """
    return {
        "type": MessageType.REQUEST,
        "command": command,
        "params": params or {},
        "timestamp": datetime.now().isoformat()
    }


def create_response(
    status: str,
    data: Optional[Any] = None,
    message: str = "",
    error: Optional[str] = None
) -> Dict[str, Any]:
    """
    Crea un mensaje de response.

    Args:
        status: Estado de la respuesta (success, error, warning)
        data: Datos de la respuesta
        message: Mensaje descriptivo
        error: Mensaje de error (si aplica)

    Returns:
        Dict con la estructura del response
    """
    response = {
        "type": MessageType.RESPONSE,
        "status": status,
        "data": data,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if error:
        response["error"] = error
    
    return response


def create_heartbeat(server_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Crea un mensaje de heartbeat.

    Args:
        server_id: Identificador del servidor
        metadata: Metadatos adicionales del servidor

    Returns:
        Dict con la estructura del heartbeat
    """
    return {
        "type": MessageType.HEARTBEAT,
        "server_id": server_id,
        "metadata": metadata or {},
        "timestamp": datetime.now().isoformat()
    }


def create_announcement(
    server_id: str,
    host: str,
    port: int,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Crea un mensaje de anuncio de servidor.

    Args:
        server_id: Identificador del servidor
        host: Host del servidor
        port: Puerto del servidor
        metadata: Metadatos adicionales

    Returns:
        Dict con la estructura del announcement
    """
    return {
        "type": MessageType.ANNOUNCEMENT,
        "server_id": server_id,
        "host": host,
        "port": port,
        "metadata": metadata or {},
        "timestamp": datetime.now().isoformat()
    }


def serialize_message(message: Dict[str, Any]) -> bytes:
    """
    Serializa un mensaje a bytes JSON con prefijo de longitud.

    Args:
        message: Mensaje a serializar

    Returns:
        bytes: Mensaje serializado con prefijo de 4 bytes de longitud

    Raises:
        ValueError: Si el mensaje no se puede serializar
    """
    try:
        json_str = json.dumps(message)
        json_bytes = json_str.encode('utf-8')
        # Agregar prefijo de longitud (4 bytes, big-endian)
        length = len(json_bytes)
        length_prefix = length.to_bytes(4, byteorder='big')
        return length_prefix + json_bytes
    except (TypeError, ValueError) as e:
        raise ValueError(f"Error al serializar mensaje: {e}")


def deserialize_message(data: bytes) -> Dict[str, Any]:
    """
    Deserializa un mensaje desde bytes JSON (sin prefijo de longitud).

    Args:
        data: Datos a deserializar (solo el JSON, sin prefijo)

    Returns:
        Dict: Mensaje deserializado

    Raises:
        ValueError: Si los datos no se pueden deserializar
    """
    try:
        json_str = data.decode('utf-8')
        return json.loads(json_str)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ValueError(f"Error al deserializar mensaje: {e}")


def validate_request(message: Dict[str, Any]) -> bool:
    """
    Valida que un mensaje de request tenga la estructura correcta.

    Args:
        message: Mensaje a validar

    Returns:
        bool: True si es válido, False en caso contrario
    """
    required_fields = ["type", "command", "params", "timestamp"]
    return all(field in message for field in required_fields)


def validate_response(message: Dict[str, Any]) -> bool:
    """
    Valida que un mensaje de response tenga la estructura correcta.

    Args:
        message: Mensaje a validar

    Returns:
        bool: True si es válido, False en caso contrario
    """
    required_fields = ["type", "status", "timestamp"]
    return all(field in message for field in required_fields)
