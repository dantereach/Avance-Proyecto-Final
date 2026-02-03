#!/usr/bin/env python3
"""
Script para iniciar el cliente de gestión de procesos.
"""

import sys
import os
import argparse

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.client.cli import CLI
from src.utils.logger import setup_logger
from src.utils.config import get_config


def main():
    """Función principal."""
    # Parsear argumentos
    parser = argparse.ArgumentParser(description='Cliente de gestión de procesos')
    parser.add_argument('--config', type=str, default='config.yaml', help='Archivo de configuración')
    parser.add_argument('--host', type=str, help='Host del servidor (auto-conectar)')
    parser.add_argument('--port', type=int, help='Puerto del servidor (auto-conectar)')
    args = parser.parse_args()
    
    # Cargar configuración
    config = get_config(args.config)
    
    # Configurar logging
    log_config = config.get_section('logging')
    setup_logger(
        'src.client',
        level=log_config.get('level', 'INFO'),
        log_format=log_config.get('format'),
        log_file=log_config.get('file'),
        console=log_config.get('console', True)
    )
    
    # Crear y ejecutar CLI
    cli = CLI()
    
    # Auto-conectar si se especificaron host y port
    if args.host and args.port:
        from src.client.tcp_client import TCPClient
        cli.client = TCPClient(args.host, args.port)
        if cli.client.connect():
            print(f"✓ Conectado a {args.host}:{args.port}\n")
        else:
            print(f"✗ No se pudo conectar a {args.host}:{args.port}\n")
    
    # Ejecutar CLI
    cli.run()


if __name__ == '__main__':
    main()
