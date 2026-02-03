#!/usr/bin/env python3
"""
Script para iniciar el registro de servicios.
"""

import sys
import os
import argparse
import signal

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.server.service_registry import ServiceRegistry
from src.utils.logger import setup_logger
from src.utils.config import get_config

# Variable global para el registro
registry = None


def signal_handler(sig, frame):
    """Maneja señales de interrupción."""
    global registry
    print("\n\nDeteniendo registro...")
    
    if registry:
        registry.shutdown()
    
    sys.exit(0)


def main():
    """Función principal."""
    global registry
    
    # Parsear argumentos
    parser = argparse.ArgumentParser(description='Registro de servicios')
    parser.add_argument('--host', type=str, help='Host de escucha')
    parser.add_argument('--port', type=int, help='Puerto de escucha')
    parser.add_argument('--config', type=str, default='config.yaml', help='Archivo de configuración')
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
    
    # Configuración del registro
    registry_config = config.get_section('registry')
    host = args.host or registry_config.get('host', '0.0.0.0')
    port = args.port or registry_config.get('port', 9001)
    heartbeat_timeout = registry_config.get('timeout', 15)
    cleanup_interval = registry_config.get('cleanup_interval', 10)
    
    # Crear registro
    registry = ServiceRegistry(host, port, heartbeat_timeout, cleanup_interval)
    
    # Manejar señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Iniciar registro
    logger.info(f"Iniciando registro de servicios en {host}:{port}")
    print(f"\n{'='*60}")
    print(f"Registro de Servicios Iniciado")
    print(f"{'='*60}")
    print(f"Host: {host}")
    print(f"Puerto: {port}")
    print(f"Heartbeat timeout: {heartbeat_timeout}s")
    print(f"Presiona Ctrl+C para detener")
    print(f"{'='*60}\n")
    
    try:
        registry.start()
    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
