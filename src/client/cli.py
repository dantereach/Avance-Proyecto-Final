"""
Interfaz de línea de comandos interactiva para el cliente.
"""

import sys
from typing import Optional

from .tcp_client import TCPClient
from .service_discovery import ServiceDiscovery
from ..utils.logger import setup_logger, get_logger
from ..utils.config import get_config

logger = get_logger(__name__)


class CLI:
    """Interfaz de línea de comandos para el cliente."""

    def __init__(self):
        """Inicializa la CLI."""
        self.client: Optional[TCPClient] = None
        self.discovery: Optional[ServiceDiscovery] = None
        self.running = True
        
        # Configurar colores (opcional)
        try:
            import colorama
            colorama.init()
            self.use_colors = True
        except ImportError:
            self.use_colors = False

    def print_banner(self) -> None:
        """Imprime el banner de bienvenida."""
        banner = """
╔═══════════════════════════════════════════════════════════╗
║  Sistema Distribuido de Administración de Procesos       ║
║  Cliente TCP/IP                                           ║
╚═══════════════════════════════════════════════════════════╝
        """
        print(banner)

    def print_help(self) -> None:
        """Imprime la ayuda de comandos disponibles."""
        help_text = """
Comandos disponibles:

Conexión:
  connect <host:port>     - Conectar a un servidor específico
  disconnect              - Desconectar del servidor actual
  servers                 - Listar servidores descubiertos

Gestión de procesos:
  list                    - Listar todos los procesos
  info <pid>              - Obtener información de un proceso
  start <command>         - Iniciar un nuevo proceso
  stop <pid> [--force]    - Detener un proceso
  monitor <pid>           - Monitorear CPU/memoria de un proceso
  stats                   - Obtener estadísticas del sistema

General:
  ping                    - Verificar conexión con el servidor
  help                    - Mostrar esta ayuda
  exit/quit               - Salir de la aplicación
        """
        print(help_text)

    def format_response(self, response: dict) -> str:
        """
        Formatea una respuesta del servidor para mostrar.

        Args:
            response: Respuesta del servidor

        Returns:
            String formateado
        """
        status = response.get('status', 'unknown')
        message = response.get('message', '')
        data = response.get('data')
        error = response.get('error')
        
        output = []
        
        # Status
        if status == 'success':
            output.append(f"✓ {message}")
        elif status == 'error':
            output.append(f"✗ Error: {error or message}")
        else:
            output.append(f"⚠ {message}")
        
        # Data
        if data:
            if isinstance(data, list):
                # Lista de procesos
                if len(data) > 0 and 'pid' in data[0]:
                    output.append("\n{:<8} {:<30} {:<12} {:<15} {:>8} {:>8}".format(
                        "PID", "NAME", "STATUS", "USER", "CPU%", "MEM%"
                    ))
                    output.append("-" * 90)
                    for proc in data:
                        output.append("{:<8} {:<30} {:<12} {:<15} {:>8.2f} {:>8.2f}".format(
                            proc.get('pid', ''),
                            proc.get('name', '')[:30],
                            proc.get('status', ''),
                            proc.get('username', '')[:15],
                            proc.get('cpu_percent', 0),
                            proc.get('memory_percent', 0)
                        ))
                else:
                    # Otra lista
                    for item in data:
                        output.append(f"  - {item}")
            elif isinstance(data, dict):
                # Dict de datos
                output.append("")
                for key, value in data.items():
                    if isinstance(value, dict):
                        output.append(f"{key}:")
                        for k, v in value.items():
                            output.append(f"  {k}: {v}")
                    else:
                        output.append(f"{key}: {value}")
        
        return "\n".join(output)

    def execute_command(self, command_line: str) -> None:
        """
        Ejecuta un comando ingresado por el usuario.

        Args:
            command_line: Línea de comando completa
        """
        parts = command_line.strip().split()
        
        if not parts:
            return
        
        command = parts[0].lower()
        args = parts[1:]
        
        try:
            if command in ['exit', 'quit']:
                self.running = False
                print("Cerrando cliente...")
                
            elif command == 'help':
                self.print_help()
                
            elif command == 'connect':
                if not args:
                    print("Uso: connect <host:port>")
                    return
                
                try:
                    host, port = args[0].split(':')
                    port = int(port)
                    
                    if self.client:
                        self.client.disconnect()
                    
                    self.client = TCPClient(host, port)
                    if self.client.connect():
                        print(f"✓ Conectado a {host}:{port}")
                    else:
                        print(f"✗ No se pudo conectar a {host}:{port}")
                        
                except ValueError:
                    print("Formato inválido. Uso: connect <host:port>")
                    
            elif command == 'disconnect':
                if self.client:
                    self.client.disconnect()
                    self.client = None
                    print("✓ Desconectado")
                else:
                    print("No hay conexión activa")
                    
            elif command == 'servers':
                if not self.discovery:
                    self.discovery = ServiceDiscovery()
                    self.discovery.start_discovery()
                
                servers = self.discovery.get_servers()
                if servers:
                    print("\nServidores descubiertos:")
                    print("{:<30} {:<15} {:<10}".format("SERVER_ID", "ADDRESS", "STATUS"))
                    print("-" * 55)
                    for server_id, info in servers.items():
                        status = "activo" if info.get('active', False) else "inactivo"
                        address = f"{info['host']}:{info['port']}"
                        print("{:<30} {:<15} {:<10}".format(server_id[:30], address, status))
                else:
                    print("No se encontraron servidores")
                    
            elif command == 'list':
                self._require_connection()
                response = self.client.list_processes()
                print(self.format_response(response))
                
            elif command == 'info':
                self._require_connection()
                if not args:
                    print("Uso: info <pid>")
                    return
                
                try:
                    pid = int(args[0])
                    response = self.client.get_process_info(pid)
                    print(self.format_response(response))
                except ValueError:
                    print("PID debe ser un número")
                    
            elif command == 'start':
                self._require_connection()
                if not args:
                    print("Uso: start <command>")
                    return
                
                cmd = ' '.join(args)
                response = self.client.start_process(cmd)
                print(self.format_response(response))
                
            elif command == 'stop':
                self._require_connection()
                if not args:
                    print("Uso: stop <pid> [--force]")
                    return
                
                try:
                    pid = int(args[0])
                    force = '--force' in args
                    response = self.client.stop_process(pid, force)
                    print(self.format_response(response))
                except ValueError:
                    print("PID debe ser un número")
                    
            elif command == 'monitor':
                self._require_connection()
                if not args:
                    print("Uso: monitor <pid>")
                    return
                
                try:
                    pid = int(args[0])
                    response = self.client.monitor_process(pid)
                    print(self.format_response(response))
                except ValueError:
                    print("PID debe ser un número")
                    
            elif command == 'stats':
                self._require_connection()
                response = self.client.get_system_stats()
                print(self.format_response(response))
                
            elif command == 'ping':
                self._require_connection()
                response = self.client.ping()
                print(self.format_response(response))
                
            else:
                print(f"Comando desconocido: {command}")
                print("Escribe 'help' para ver los comandos disponibles")
                
        except ConnectionError as e:
            print(f"✗ Error de conexión: {e}")
            if self.client:
                self.client.disconnect()
                self.client = None
        except Exception as e:
            print(f"✗ Error: {e}")
            logger.error(f"Error ejecutando comando: {e}")

    def _require_connection(self) -> None:
        """
        Verifica que haya una conexión activa.

        Raises:
            ConnectionError: Si no hay conexión
        """
        if not self.client or not self.client.is_connected():
            raise ConnectionError("No conectado al servidor. Usa 'connect <host:port>' primero")

    def run(self) -> None:
        """Ejecuta el loop principal de la CLI."""
        self.print_banner()
        print("Escribe 'help' para ver los comandos disponibles\n")
        
        while self.running:
            try:
                # Prompt
                if self.client and self.client.is_connected():
                    prompt = f"[{self.client.get_address()}] > "
                else:
                    prompt = "[desconectado] > "
                
                command = input(prompt).strip()
                
                if command:
                    self.execute_command(command)
                    
            except KeyboardInterrupt:
                print("\nUsa 'exit' para salir")
            except EOFError:
                break
        
        # Cleanup
        if self.client:
            self.client.disconnect()
        if self.discovery:
            self.discovery.stop_discovery()


def main():
    """Función principal para ejecutar la CLI."""
    # Configurar logging
    config = get_config()
    log_config = config.get_section('logging')
    setup_logger(
        'src.client',
        level=log_config.get('level', 'INFO'),
        log_format=log_config.get('format'),
        log_file=log_config.get('file'),
        console=log_config.get('console', True)
    )
    
    cli = CLI()
    cli.run()


if __name__ == '__main__':
    main()
