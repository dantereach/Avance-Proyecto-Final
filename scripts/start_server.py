#!/usr/bin/env python3
"""
Script para iniciar el servidor de procesos TCP/IP.
"""

import sys
import os
import argparse
import signal

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.server.tcp_server import TCPServer
from src.client.service_discovery import ServerAnnouncer
from src.utils.logger import setup_logger
from src.utils.config import get_config

# Variable global para el servidor
server = None
announcer = None


def signal_handler(sig, frame):
    """Maneja señales de interrupción."""
    global server, announcer
    print("\n\nDeteniendo servidor...")
    
    if announcer:
        announcer.stop()
    
    if server:
        server.shutdown()
    
    sys.exit(0)


def main():
    """Función principal."""
    global server, announcer
    
    # Parsear argumentos
    parser = argparse.ArgumentParser(description='Servidor de gestión de procesos')
    parser.add_argument('--host', type=str, help='Host de escucha')
    parser.add_argument('--port', type=int, help='Puerto de escucha')
    parser.add_argument('--config', type=str, default='config.yaml', help='Archivo de configuración')
    parser.add_argument('--no-announce', action='store_true', help='No anunciar servidor en la red')
    args = parser.parse_args()
    
    # Cargar configuración
    config = get_config(args.config)
    
    # Configurar logging
    log_config = config.get_section('logging')
    logger = setup_logger(
        'src.server',
        level=log_config.get('level', 'INFO'),
        log_format=log_config.get('format'),
        log_file=log_config.get('file'),
        console=log_config.get('console', True)
    )
    
    # Configuración del servidor
    server_config = config.get_section('server')
    host = args.host or server_config.get('host', '0.0.0.0')
    port = args.port or server_config.get('port', 9000)
    buffer_size = server_config.get('buffer_size', 4096)
    
    # Crear servidor
    server = TCPServer(host, port, buffer_size)
    
    # Configurar anunciador si está habilitado
    if not args.no_announce:
        discovery_config = config.get_section('discovery')
        import uuid
        server_id = f"server-{uuid.uuid4().hex[:8]}"
        
        announcer = ServerAnnouncer(
            server_id=server_id,
            host=host if host != '0.0.0.0' else 'localhost',
            port=port,
            broadcast_port=discovery_config.get('broadcast_port', 9002),
            announcement_interval=discovery_config.get('announcement_interval', 5)
        )
        announcer.start()
        logger.info(f"Anuncio de servidor habilitado (ID: {server_id})")
    
    # Manejar señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Iniciar servidor
    logger.info(f"Iniciando servidor en {host}:{port}")
    print(f"\n{'='*60}")
    print(f"Servidor de Procesos Iniciado")
    print(f"{'='*60}")
    print(f"Host: {host}")
    print(f"Puerto: {port}")
    print(f"Presiona Ctrl+C para detener")
    print(f"{'='*60}\n")
    
    try:
        server.start()
    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
