# Sistema Distribuido de Administración de Procesos

Sistema completo de administración de procesos distribuido implementado en Python, que permite gestionar procesos en sistemas remotos a través de una arquitectura cliente-servidor con descubrimiento automático de servicios.

## 📋 Tabla de Contenidos

- [Características](#características)
- [Arquitectura](#arquitectura)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Comandos Disponibles](#comandos-disponibles)
- [Testing](#testing)
- [Arquitectura Distribuida](#arquitectura-distribuida)
- [Ejemplos de Uso](#ejemplos-de-uso)
- [Troubleshooting](#troubleshooting)
- [Contribución](#contribución)
- [Licencia](#licencia)

## ✨ Características

### Parte 1: Gestión de Procesos
- ✅ Listar procesos activos con información detallada (PID, nombre, estado, usuario, CPU%, memoria%)
- ✅ Iniciar nuevas aplicaciones/procesos remotamente
- ✅ Detener procesos por PID (terminate y kill)
- ✅ Monitorear uso de CPU y memoria en tiempo real
- ✅ Obtener estadísticas del sistema (CPU, memoria, disco)

### Parte 2: Comunicación TCP/IP
- ✅ Servidor TCP/IP multi-hilo para conexiones concurrentes
- ✅ Cliente TCP/IP con interfaz CLI interactiva
- ✅ Protocolo de mensajes JSON estructurado
- ✅ Manejo robusto de errores y desconexiones
- ✅ Logging completo de operaciones

### Parte 3: Sistemas Distribuidos
- ✅ Descubrimiento automático de servidores via UDP broadcast
- ✅ Registro centralizado de servicios con heartbeats
- ✅ Balanceo de carga (round-robin y least-loaded)
- ✅ Detección automática de servidores caídos
- ✅ Middleware para comunicación transparente

## 🏗️ Arquitectura

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│                 │  TCP/IP │                  │  TCP/IP │                 │
│  Cliente CLI    ├────────►│  Servidor de     │◄────────┤  Cliente CLI    │
│                 │         │  Procesos        │         │                 │
└────────┬────────┘         └────────┬─────────┘         └────────┬────────┘
         │                           │                            │
         │ UDP Broadcast             │ UDP Heartbeat              │
         │                           │                            │
         └───────────────────────────┼────────────────────────────┘
                                     │
                          ┌──────────▼──────────┐
                          │                     │
                          │ Registro de         │
                          │ Servicios (UDP)     │
                          │                     │
                          └─────────────────────┘
```

### Componentes Principales

#### Servidor (`src/server/`)
- **process_manager.py**: Gestión de procesos usando `psutil`
- **tcp_server.py**: Servidor TCP multi-hilo
- **service_registry.py**: Registro centralizado de servicios

#### Cliente (`src/client/`)
- **tcp_client.py**: Cliente TCP para comunicación con servidor
- **cli.py**: Interfaz de línea de comandos interactiva
- **service_discovery.py**: Descubrimiento de servidores

#### Middleware (`src/middleware/`)
- **message_protocol.py**: Protocolo de mensajes JSON
- **load_balancer.py**: Balanceo de carga entre servidores

#### Utilidades (`src/utils/`)
- **logger.py**: Sistema de logging centralizado
- **config.py**: Gestión de configuración YAML

## 📦 Requisitos

- **Python 3.8+**
- Dependencias principales:
  - `psutil>=5.9.0` - Gestión de procesos
  - `pyyaml>=6.0` - Configuración
  - `pytest>=7.0.0` - Testing
  - `colorama>=0.4.6` - Colores en CLI (opcional)

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/dantereach/Avance-Proyecto-Final.git
cd Avance-Proyecto-Final
```

### 2. Crear entorno virtual (recomendado)

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

## ⚙️ Configuración

El sistema usa un archivo `config.yaml` para la configuración. Parámetros importantes:

```yaml
# Configuración del servidor TCP
server:
  host: "0.0.0.0"      # Dirección de escucha
  port: 9000           # Puerto TCP del servidor
  buffer_size: 4096    # Tamaño del buffer
  timeout: 30          # Timeout de conexión

# Configuración del cliente
client:
  timeout: 30
  reconnect_attempts: 3

# Registro de servicios
registry:
  host: "0.0.0.0"
  port: 9001           # Puerto UDP para registro
  heartbeat_interval: 5
  timeout: 15          # Timeout para marcar servidor caído

# Descubrimiento UDP
discovery:
  broadcast_port: 9002  # Puerto para broadcasts
  announcement_interval: 5

# Logging
logging:
  level: "INFO"        # DEBUG, INFO, WARNING, ERROR, CRITICAL
  file: "system.log"
  console: true
```

## 🎯 Uso

### Opción 1: Servidor Simple

Iniciar un servidor de procesos:

```bash
python scripts/start_server.py
```

Opciones:
```bash
python scripts/start_server.py --host 0.0.0.0 --port 9000
python scripts/start_server.py --config mi_config.yaml
python scripts/start_server.py --no-announce  # Sin anuncio UDP
```

### Opción 2: Arquitectura Distribuida Completa

**Terminal 1 - Registro de Servicios:**
```bash
python scripts/start_registry.py
```

**Terminal 2 - Servidor de Procesos:**
```bash
python scripts/start_server.py
```

**Terminal 3 - Cliente:**
```bash
python scripts/start_client.py
```

### Opción 3: Cliente con Auto-conexión

```bash
python scripts/start_client.py --host localhost --port 9000
```

## 📖 Comandos Disponibles

### Comandos de Conexión

```
connect <host:port>     - Conectar a un servidor específico
disconnect              - Desconectar del servidor actual
servers                 - Listar servidores descubiertos
ping                    - Verificar conexión con servidor
```

**Ejemplo:**
```
[desconectado] > connect localhost:9000
✓ Conectado a localhost:9000

[localhost:9000] > ping
✓ Servidor activo
```

### Comandos de Gestión de Procesos

```
list                    - Listar todos los procesos
info <pid>              - Información detallada de un proceso
start <command>         - Iniciar nuevo proceso
stop <pid> [--force]    - Detener proceso (--force para kill)
monitor <pid>           - Monitorear CPU/memoria de proceso
stats                   - Estadísticas del sistema
```

**Ejemplos:**
```
[localhost:9000] > list
✓ Se listaron 156 procesos

PID      NAME                           STATUS       USER            CPU%     MEM%
----------------------------------------------------------------------------------------
1        systemd                        running      root            0.00     0.15
1234     python                         running      user            2.45     1.23
5678     chrome                         sleeping     user            0.50     3.45

[localhost:9000] > start sleep 60
✓ Proceso iniciado exitosamente con PID 9999

[localhost:9000] > monitor 9999
✓ Estadísticas del proceso 9999

pid: 9999
name: sleep
cpu_percent: 0.0
memory_percent: 0.01
memory_rss_mb: 2.5
num_threads: 1
status: sleeping

[localhost:9000] > stop 9999
✓ Proceso 9999 (sleep) terminated exitosamente

[localhost:9000] > stats
✓ Estadísticas del sistema

cpu:
  percent: 15.2
  count: 8
  frequency_mhz: 2400.0
memory:
  total_gb: 16.0
  used_gb: 8.5
  percent: 53.1
disk:
  total_gb: 256.0
  used_gb: 128.5
  percent: 50.2
```

### Comandos Generales

```
help                    - Mostrar ayuda
exit/quit               - Salir de la aplicación
```

## 🧪 Testing

### Ejecutar todos los tests

```bash
pytest tests/ -v
```

### Tests con cobertura

```bash
pytest --cov=src tests/
```

### Ejecutar tests específicos

```bash
# Solo tests de ProcessManager
pytest tests/test_process_manager.py -v

# Solo tests de TCP
pytest tests/test_tcp_server.py -v

# Solo tests de protocolo
pytest tests/test_message_protocol.py -v

# Solo tests de balanceador
pytest tests/test_load_balancer.py -v
```

### Cobertura de código

```bash
pytest --cov=src --cov-report=html tests/
# Ver reporte en htmlcov/index.html
```

## 🌐 Arquitectura Distribuida

### Descubrimiento de Servicios

El sistema implementa dos mecanismos de descubrimiento:

1. **Broadcast UDP**: Los servidores anuncian su presencia cada 5 segundos
2. **Registro Centralizado**: Los servidores envían heartbeats a un registro central

### Flujo de Descubrimiento

```
1. Servidor inicia y anuncia via UDP broadcast
2. Cliente escucha broadcasts y descubre servidores
3. Cliente puede listar servidores con comando 'servers'
4. Cliente selecciona servidor y se conecta via TCP
5. Servidor envía heartbeats periódicos al registro
6. Registro marca servidores inactivos si no hay heartbeat
```

### Balanceo de Carga

Dos estrategias disponibles:

**Round-Robin**: Distribuye peticiones equitativamente
```python
load_balancer = LoadBalancer(strategy='round_robin')
```

**Least-Loaded**: Selecciona servidor con menos carga
```python
load_balancer = LoadBalancer(strategy='least_loaded')
```

### Tolerancia a Fallos

- **Heartbeat timeout**: Servidores sin heartbeat por 15s se marcan inactivos
- **Reconexión automática**: Cliente reintenta conexión
- **Failover**: Cambio automático a otro servidor si falla

## 💡 Ejemplos de Uso

### Escenario 1: Monitoreo de Proceso Específico

```bash
# Terminal 1 - Servidor
python scripts/start_server.py

# Terminal 2 - Cliente
python scripts/start_client.py --host localhost --port 9000

# En el cliente
> list
> info 1234
> monitor 1234
```

### Escenario 2: Iniciar Proceso Remoto

```bash
# En el cliente conectado
> start python -m http.server 8080
✓ Proceso iniciado exitosamente con PID 5555

> list
# Ver el nuevo proceso

> stop 5555
✓ Proceso 5555 (python) terminated exitosamente
```

### Escenario 3: Múltiples Servidores

```bash
# Terminal 1 - Registro
python scripts/start_registry.py

# Terminal 2 - Servidor 1
python scripts/start_server.py --port 9000

# Terminal 3 - Servidor 2
python scripts/start_server.py --port 9001

# Terminal 4 - Cliente
python scripts/start_client.py

# En el cliente
> servers
Servidores descubiertos:
SERVER_ID                      ADDRESS         STATUS
-------------------------------------------------------
server-abc123                  localhost:9000  activo
server-def456                  localhost:9001  activo

> connect localhost:9000
✓ Conectado a localhost:9000

> list
# Ver procesos del servidor 1
```

### Escenario 4: Monitoreo del Sistema

```bash
# En el cliente conectado
> stats

cpu:
  percent: 25.5
  count: 8
  frequency_mhz: 2800.0
memory:
  total_gb: 32.0
  available_gb: 18.5
  used_gb: 13.5
  percent: 42.2
disk:
  total_gb: 512.0
  used_gb: 256.3
  free_gb: 255.7
  percent: 50.1
system:
  boot_time: 2026-02-03T08:00:00
```

## 🔧 Troubleshooting

### Problema: "Conexión rechazada"

**Solución:**
- Verificar que el servidor esté corriendo
- Verificar host y puerto correctos
- Verificar firewall no bloquee el puerto

```bash
# Verificar si puerto está en uso
netstat -an | grep 9000

# Linux: abrir puerto en firewall
sudo ufw allow 9000
```

### Problema: "No se descubren servidores"

**Solución:**
- Verificar que el broadcast UDP no esté bloqueado
- Confirmar que servidor y cliente estén en misma red
- Verificar puerto de broadcast (9002) esté disponible

```bash
# Verificar broadcast
python scripts/start_server.py
python scripts/start_client.py
> servers
```

### Problema: "Acceso denegado al proceso"

**Solución:**
- Algunos procesos requieren privilegios
- Ejecutar servidor con permisos necesarios (root/admin)

```bash
# Linux
sudo python scripts/start_server.py

# Windows (ejecutar como Administrador)
python scripts/start_server.py
```

### Problema: "Comando no encontrado al iniciar proceso"

**Solución:**
- Verificar que el comando exista en PATH
- Usar ruta absoluta al ejecutable

```bash
# Incorrecto
> start notepad

# Correcto en Windows
> start C:\Windows\System32\notepad.exe

# Correcto en Linux
> start /usr/bin/gedit
```

### Problema: Tests fallan

**Solución:**
```bash
# Instalar dependencias de test
pip install pytest pytest-cov

# Ejecutar con más verbosidad
pytest tests/ -v -s

# Ver logs de tests
pytest tests/ --log-cli-level=DEBUG
```

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama de feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

### Estándares de Código

- Seguir PEP 8
- Agregar docstrings a funciones y clases
- Mantener cobertura de tests >70%
- Actualizar documentación

## 📄 Licencia

Este proyecto es software educativo desarrollado como proyecto final.

## 👥 Autor

**Dante Reach**
- GitHub: [@dantereach](https://github.com/dantereach)

---

## 📚 Referencias Técnicas

### Protocolo de Mensajes

Todos los mensajes usan JSON sobre TCP/UDP.

**Request:**
```json
{
  "type": "request",
  "command": "list_processes",
  "params": {},
  "timestamp": "2026-02-03T12:00:00"
}
```

**Response:**
```json
{
  "type": "response",
  "status": "success",
  "data": {...},
  "message": "Operación exitosa",
  "timestamp": "2026-02-03T12:00:01"
}
```

### Comandos Soportados

- `list_processes` - Listar procesos
- `get_process_info` - Info de proceso (requiere `pid`)
- `start_process` - Iniciar proceso (requiere `command`)
- `stop_process` - Detener proceso (requiere `pid`, opcional `force`)
- `monitor_process` - Monitorear proceso (requiere `pid`)
- `get_system_stats` - Estadísticas del sistema
- `ping` - Verificar conectividad

### Puertos por Defecto

- `9000` - Servidor TCP de procesos
- `9001` - Registro de servicios (UDP)
- `9002` - Broadcast de descubrimiento (UDP)

---

**¡Sistema listo para producción! 🚀**
