"""
Servidor TCP/IP multi-hilo para gestión remota de procesos.
"""

import socket
import threading
import json
from typing import Optional

from .process_manager import ProcessManager
from ..middleware.message_protocol import (
    deserialize_message,
    serialize_message,
    create_response,
    ResponseStatus,
    CommandType,
    validate_request
)
from ..utils.logger import setup_logger, get_logger
from ..utils.config import get_config

logger = get_logger(__name__)


class TCPServer:
    """Servidor TCP/IP para gestión de procesos."""

    def __init__(self, host: str = "0.0.0.0", port: int = 9000, buffer_size: int = 4096):
        """
        Inicializa el servidor TCP.

        Args:
            host: Dirección IP del servidor
            port: Puerto de escucha
            buffer_size: Tamaño del buffer para recepción de datos
        """
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        self.process_manager = ProcessManager()
        self.clients = []
        
        logger.info(f"TCPServer inicializado en {host}:{port}")

    def start(self) -> None:
        """Inicia el servidor y comienza a escuchar conexiones."""
        try:
            # Crear socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind y listen
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.running = True
            logger.info(f"Servidor TCP escuchando en {self.host}:{self.port}")
            
            # Loop principal de aceptación de clientes
            while self.running:
                try:
                    # Configurar timeout para poder verificar self.running
                    self.server_socket.settimeout(1.0)
                    
                    try:
                        client_socket, client_address = self.server_socket.accept()
                        logger.info(f"Nueva conexión desde {client_address}")
                        
                        # Crear thread para manejar el cliente
                        client_thread = threading.Thread(
                            target=self._handle_client,
                            args=(client_socket, client_address),
                            daemon=True
                        )
                        client_thread.start()
                        self.clients.append(client_thread)
                        
                    except socket.timeout:
                        continue
                        
                except Exception as e:
                    if self.running:
                        logger.error(f"Error aceptando conexión: {e}")
                    
        except Exception as e:
            logger.error(f"Error iniciando servidor: {e}")
            raise
        finally:
            self.shutdown()

    def _handle_client(self, client_socket: socket.socket, client_address: tuple) -> None:
        """
        Maneja la comunicación con un cliente.

        Args:
            client_socket: Socket del cliente
            client_address: Dirección del cliente
        """
        try:
            while self.running:
                # Recibir datos
                data = client_socket.recv(self.buffer_size)
                
                if not data:
                    logger.info(f"Cliente {client_address} desconectado")
                    break
                
                # Procesar mensaje
                try:
                    message = deserialize_message(data)
                    logger.debug(f"Mensaje recibido de {client_address}: {message.get('command')}")
                    
                    # Validar request
                    if not validate_request(message):
                        response = create_response(
                            ResponseStatus.ERROR,
                            error="Formato de mensaje inválido"
                        )
                    else:
                        # Procesar comando
                        response = self._process_command(message)
                    
                    # Enviar respuesta
                    response_data = serialize_message(response)
                    client_socket.sendall(response_data)
                    
                except ValueError as e:
                    logger.error(f"Error deserializando mensaje: {e}")
                    response = create_response(
                        ResponseStatus.ERROR,
                        error=f"Error de deserialización: {str(e)}"
                    )
                    client_socket.sendall(serialize_message(response))
                except Exception as e:
                    logger.error(f"Error procesando mensaje: {e}")
                    response = create_response(
                        ResponseStatus.ERROR,
                        error=f"Error procesando comando: {str(e)}"
                    )
                    client_socket.sendall(serialize_message(response))
                    
        except Exception as e:
            logger.error(f"Error en conexión con {client_address}: {e}")
        finally:
            try:
                client_socket.close()
                logger.info(f"Conexión con {client_address} cerrada")
            except:
                pass

    def _process_command(self, message: dict) -> dict:
        """
        Procesa un comando recibido.

        Args:
            message: Mensaje con el comando

        Returns:
            Dict con la respuesta
        """
        command = message.get('command')
        params = message.get('params', {})
        
        try:
            if command == CommandType.LIST_PROCESSES:
                data = self.process_manager.list_processes()
                return create_response(
                    ResponseStatus.SUCCESS,
                    data=data,
                    message=f"Se listaron {len(data)} procesos"
                )
                
            elif command == CommandType.GET_PROCESS_INFO:
                pid = params.get('pid')
                if not pid:
                    return create_response(
                        ResponseStatus.ERROR,
                        error="Parámetro 'pid' requerido"
                    )
                
                data = self.process_manager.get_process_info(int(pid))
                return create_response(
                    ResponseStatus.SUCCESS,
                    data=data,
                    message=f"Información del proceso {pid}"
                )
                
            elif command == CommandType.START_PROCESS:
                cmd = params.get('command')
                if not cmd:
                    return create_response(
                        ResponseStatus.ERROR,
                        error="Parámetro 'command' requerido"
                    )
                
                data = self.process_manager.start_process(cmd)
                return create_response(
                    ResponseStatus.SUCCESS,
                    data=data,
                    message=data['message']
                )
                
            elif command == CommandType.STOP_PROCESS:
                pid = params.get('pid')
                force = params.get('force', False)
                
                if not pid:
                    return create_response(
                        ResponseStatus.ERROR,
                        error="Parámetro 'pid' requerido"
                    )
                
                data = self.process_manager.stop_process(int(pid), force)
                return create_response(
                    ResponseStatus.SUCCESS,
                    data=data,
                    message=data['message']
                )
                
            elif command == CommandType.MONITOR_PROCESS:
                pid = params.get('pid')
                if not pid:
                    return create_response(
                        ResponseStatus.ERROR,
                        error="Parámetro 'pid' requerido"
                    )
                
                data = self.process_manager.monitor_process(int(pid))
                return create_response(
                    ResponseStatus.SUCCESS,
                    data=data,
                    message=f"Estadísticas del proceso {pid}"
                )
                
            elif command == CommandType.GET_SYSTEM_STATS:
                data = self.process_manager.get_system_stats()
                return create_response(
                    ResponseStatus.SUCCESS,
                    data=data,
                    message="Estadísticas del sistema"
                )
                
            elif command == CommandType.PING:
                return create_response(
                    ResponseStatus.SUCCESS,
                    data={'pong': True},
                    message="Servidor activo"
                )
                
            else:
                return create_response(
                    ResponseStatus.ERROR,
                    error=f"Comando desconocido: {command}"
                )
                
        except Exception as e:
            logger.error(f"Error ejecutando comando {command}: {e}")
            return create_response(
                ResponseStatus.ERROR,
                error=str(e)
            )

    def shutdown(self) -> None:
        """Detiene el servidor y cierra todas las conexiones."""
        logger.info("Deteniendo servidor...")
        self.running = False
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        logger.info("Servidor detenido")


def main():
    """Función principal para ejecutar el servidor."""
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
    
    # Configurar servidor
    server_config = config.get_section('server')
    server = TCPServer(
        host=server_config.get('host', '0.0.0.0'),
        port=server_config.get('port', 9000),
        buffer_size=server_config.get('buffer_size', 4096)
    )
    
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Servidor interrumpido por usuario")
        server.shutdown()


if __name__ == '__main__':
    main()
