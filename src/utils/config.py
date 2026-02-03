"""
Gestión de configuración del sistema.
"""

import os
import yaml
from typing import Any, Dict, Optional


class Config:
    """Clase para gestionar la configuración del sistema."""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Inicializa la configuración.

        Args:
            config_path: Ruta al archivo de configuración YAML
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Carga la configuración desde el archivo YAML."""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
        else:
            # Configuración por defecto si no existe el archivo
            self.config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Retorna la configuración por defecto.

        Returns:
            Dict con configuración por defecto
        """
        return {
            "server": {
                "host": "0.0.0.0",
                "port": 9000,
                "buffer_size": 4096,
                "timeout": 30,
                "max_connections": 10
            },
            "client": {
                "timeout": 30,
                "reconnect_attempts": 3,
                "reconnect_delay": 5
            },
            "registry": {
                "host": "0.0.0.0",
                "port": 9001,
                "heartbeat_interval": 5,
                "timeout": 15,
                "cleanup_interval": 10
            },
            "discovery": {
                "broadcast_port": 9002,
                "multicast_group": "224.0.0.1",
                "announcement_interval": 5,
                "discovery_timeout": 10
            },
            "load_balancer": {
                "strategy": "round_robin",
                "health_check_interval": 30
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "system.log",
                "console": True
            },
            "processes": {
                "monitor_interval": 1,
                "kill_timeout": 5
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración usando notación de punto.

        Args:
            key: Clave en formato "section.subsection.key"
            default: Valor por defecto si la clave no existe

        Returns:
            Valor de configuración o default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value

    def set(self, key: str, value: Any) -> None:
        """
        Establece un valor de configuración usando notación de punto.

        Args:
            key: Clave en formato "section.subsection.key"
            value: Valor a establecer
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value

    def save(self) -> None:
        """Guarda la configuración actual al archivo YAML."""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False)

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Obtiene una sección completa de la configuración.

        Args:
            section: Nombre de la sección

        Returns:
            Dict con la sección de configuración
        """
        return self.config.get(section, {})


# Instancia global de configuración
_config: Optional[Config] = None


def get_config(config_path: str = "config.yaml") -> Config:
    """
    Obtiene la instancia global de configuración (singleton).

    Args:
        config_path: Ruta al archivo de configuración

    Returns:
        Config: Instancia de configuración
    """
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config
