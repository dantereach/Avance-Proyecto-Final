"""
Balanceador de carga para distribuir peticiones entre múltiples servidores.
"""

import threading
from typing import List, Dict, Any, Optional
from itertools import cycle

from ..utils.logger import get_logger

logger = get_logger(__name__)


class LoadBalancer:
    """Balanceador de carga para seleccionar servidores."""

    def __init__(self, strategy: str = "round_robin"):
        """
        Inicializa el balanceador de carga.

        Args:
            strategy: Estrategia de balanceo ('round_robin', 'least_loaded')
        """
        self.strategy = strategy
        self.servers: List[Dict[str, Any]] = []
        self.server_stats: Dict[str, Dict[str, int]] = {}
        self.lock = threading.Lock()
        
        # Para round-robin
        self.round_robin_cycle = None
        
        logger.info(f"LoadBalancer inicializado con estrategia: {strategy}")

    def add_server(self, server_id: str, host: str, port: int, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Agrega un servidor al pool.

        Args:
            server_id: ID del servidor
            host: Host del servidor
            port: Puerto del servidor
            metadata: Metadatos adicionales
        """
        with self.lock:
            server_info = {
                'server_id': server_id,
                'host': host,
                'port': port,
                'metadata': metadata or {},
                'active': True
            }
            
            # Evitar duplicados
            for i, srv in enumerate(self.servers):
                if srv['server_id'] == server_id:
                    self.servers[i] = server_info
                    logger.info(f"Servidor actualizado: {server_id}")
                    return
            
            self.servers.append(server_info)
            self.server_stats[server_id] = {'requests': 0, 'errors': 0}
            
            # Reiniciar round-robin
            if self.strategy == "round_robin":
                self.round_robin_cycle = cycle(self.servers)
            
            logger.info(f"Servidor agregado: {server_id} ({host}:{port})")

    def remove_server(self, server_id: str) -> None:
        """
        Elimina un servidor del pool.

        Args:
            server_id: ID del servidor a eliminar
        """
        with self.lock:
            self.servers = [s for s in self.servers if s['server_id'] != server_id]
            
            if server_id in self.server_stats:
                del self.server_stats[server_id]
            
            # Reiniciar round-robin
            if self.strategy == "round_robin" and self.servers:
                self.round_robin_cycle = cycle(self.servers)
            
            logger.info(f"Servidor eliminado: {server_id}")

    def update_servers(self, servers_dict: Dict[str, Dict[str, Any]]) -> None:
        """
        Actualiza la lista de servidores desde un diccionario.

        Args:
            servers_dict: Dict con información de servidores
        """
        with self.lock:
            # Limpiar servidores actuales
            current_ids = {s['server_id'] for s in self.servers}
            new_ids = set(servers_dict.keys())
            
            # Eliminar servidores que ya no existen (sin llamar remove_server para evitar deadlock)
            for sid in current_ids - new_ids:
                self.servers = [s for s in self.servers if s['server_id'] != sid]
                if sid in self.server_stats:
                    del self.server_stats[sid]
                logger.info(f"Servidor eliminado: {sid}")
            
            # Agregar o actualizar servidores (sin llamar add_server para evitar deadlock)
            for server_id, info in servers_dict.items():
                if info.get('active', False):
                    server_info = {
                        'server_id': server_id,
                        'host': info['host'],
                        'port': info['port'],
                        'metadata': info.get('metadata', {}),
                        'active': True
                    }
                    
                    # Evitar duplicados
                    found = False
                    for i, srv in enumerate(self.servers):
                        if srv['server_id'] == server_id:
                            self.servers[i] = server_info
                            found = True
                            logger.info(f"Servidor actualizado: {server_id}")
                            break
                    
                    if not found:
                        self.servers.append(server_info)
                        self.server_stats[server_id] = {'requests': 0, 'errors': 0}
                        logger.info(f"Servidor agregado: {server_id}")
            
            # Reiniciar round-robin
            if self.strategy == "round_robin" and self.servers:
                self.round_robin_cycle = cycle(self.servers)

    def get_next_server(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene el siguiente servidor según la estrategia de balanceo.

        Returns:
            Dict con información del servidor o None si no hay servidores
        """
        with self.lock:
            if not self.servers:
                logger.warning("No hay servidores disponibles")
                return None
            
            if self.strategy == "round_robin":
                return self._round_robin()
            elif self.strategy == "least_loaded":
                return self._least_loaded()
            else:
                # Por defecto: primer servidor
                return self.servers[0]

    def _round_robin(self) -> Optional[Dict[str, Any]]:
        """
        Selecciona el siguiente servidor usando round-robin.

        Returns:
            Dict con información del servidor
        """
        if not self.round_robin_cycle:
            self.round_robin_cycle = cycle(self.servers)
        
        # Buscar siguiente servidor activo
        for _ in range(len(self.servers)):
            server = next(self.round_robin_cycle)
            if server.get('active', False):
                logger.debug(f"Servidor seleccionado (round-robin): {server['server_id']}")
                return server
        
        logger.warning("No hay servidores activos")
        return None

    def _least_loaded(self) -> Optional[Dict[str, Any]]:
        """
        Selecciona el servidor con menos carga.

        Returns:
            Dict con información del servidor
        """
        if not self.servers:
            return None
        
        # Encontrar servidor con menos requests
        min_requests = float('inf')
        selected_server = None
        
        for server in self.servers:
            if not server.get('active', False):
                continue
            
            server_id = server['server_id']
            requests = self.server_stats.get(server_id, {}).get('requests', 0)
            
            if requests < min_requests:
                min_requests = requests
                selected_server = server
        
        if selected_server:
            logger.debug(f"Servidor seleccionado (least-loaded): {selected_server['server_id']}")
        
        return selected_server

    def record_request(self, server_id: str, success: bool = True) -> None:
        """
        Registra una petición a un servidor.

        Args:
            server_id: ID del servidor
            success: Si la petición fue exitosa
        """
        with self.lock:
            if server_id not in self.server_stats:
                self.server_stats[server_id] = {'requests': 0, 'errors': 0}
            
            self.server_stats[server_id]['requests'] += 1
            
            if not success:
                self.server_stats[server_id]['errors'] += 1

    def get_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Obtiene estadísticas de uso de servidores.

        Returns:
            Dict con estadísticas por servidor
        """
        with self.lock:
            return dict(self.server_stats)

    def get_servers(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de servidores activos.

        Returns:
            Lista de servidores
        """
        with self.lock:
            return [s for s in self.servers if s.get('active', False)]

    def mark_server_inactive(self, server_id: str) -> None:
        """
        Marca un servidor como inactivo.

        Args:
            server_id: ID del servidor
        """
        with self.lock:
            for server in self.servers:
                if server['server_id'] == server_id:
                    server['active'] = False
                    logger.info(f"Servidor marcado como inactivo: {server_id}")
                    break

    def mark_server_active(self, server_id: str) -> None:
        """
        Marca un servidor como activo.

        Args:
            server_id: ID del servidor
        """
        with self.lock:
            for server in self.servers:
                if server['server_id'] == server_id:
                    server['active'] = True
                    logger.info(f"Servidor marcado como activo: {server_id}")
                    break
