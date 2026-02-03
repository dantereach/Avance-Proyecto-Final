"""
Configuración centralizada del sistema de logging.
"""

import logging
import sys
from typing import Optional


def setup_logger(
    name: str,
    level: str = "INFO",
    log_format: Optional[str] = None,
    log_file: Optional[str] = None,
    console: bool = True
) -> logging.Logger:
    """
    Configura y retorna un logger.

    Args:
        name: Nombre del logger
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Formato personalizado de mensajes
        log_file: Ruta al archivo de log (opcional)
        console: Si True, también loguea a consola

    Returns:
        logging.Logger: Logger configurado
    """
    # Crear logger
    logger = logging.getLogger(name)
    
    # Convertir string de nivel a constante
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Evitar duplicar handlers
    if logger.handlers:
        return logger
    
    # Formato por defecto
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    formatter = logging.Formatter(log_format)
    
    # Handler para consola
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Handler para archivo
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger existente o crea uno nuevo con configuración por defecto.

    Args:
        name: Nombre del logger

    Returns:
        logging.Logger: Logger
    """
    return logging.getLogger(name)
