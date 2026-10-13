# Práctica 2 — Objetos inteligentes con TCP/IP

Monorepo con dos clientes ESP32 y un servidor TCP Python. Un HC-SR04 mide distancia;
el servidor clasifica y el segundo ESP32 controla tres LEDs sobre la misma red WiFi.

El [informe existente](informe.md) se conserva. La implementación sigue sus mensajes
`REGISTER`, `POST` y `SET`; el [contrato](contracts/protocol.md) detalla delimitación,
errores y extensiones opcionales. El [estado por etapas](docs/ETAPAS.md) indica qué
está verificado y qué requiere montaje físico.

## Organización

| Ruta | Contenido |
| --- | --- |
| `firmware/` | Entornos PlatformIO `sensor` y `actuator`, bibliotecas compartidas. |
| `server/` | Servidor, control y pruebas de sockets reales en loopback. |
| `contracts/` | Protocolo y casos de conformidad C++ / Python. |
| `tools/` | Simuladores, captura de mediciones y verificaciones. |
| `docs/` | Implementación, diagramas, montaje y validación complementaria. |

La [explicación de la arquitectura](docs/architecture.md) muestra las responsabilidades
de cada componente y el recorrido completo de una medición.

## Herramientas

El servidor requiere Python 3.10 o posterior y solo utiliza la biblioteca estándar.
Para compilar: PlatformIO Core `6.2.0`, ESP32 `6.13.0` y Arduino `2.0.17`.
Las pruebas nativas requieren `g++`, disponible mediante MSYS2 en Windows.
En VS Code, instalar la extensión C/C++ recomendada. Para usar las tareas de
PlatformIO, seleccionar `firmware/` al abrir el proyecto desde su extensión.

En esta carpeta se preparó un Python local en `.tools/python/`, ignorado por Git.
Los lanzadores Windows lo seleccionan automáticamente:

```powershell
.\tools\python.cmd --version
.\tools\pio.cmd --version
.\tools\verify.cmd
```

Los `.cmd` funcionan también cuando PowerShell restringe archivos `.ps1`.
Al abrir la raíz del repositorio en VS Code, generar las rutas de IntelliSense:

```powershell
.\tools\pio.cmd run -d firmware -e sensor -e actuator -t compiledb
.\tools\python.cmd -m tools.test_firmware
```

También se puede ejecutar `Terminal > Run Task > Firmware: regenerar IntelliSense`.
Repetirlo si cambian las bibliotecas o la configuración de compilación. VS Code
lee las cabeceras, macros y compiladores reales de cada entorno; las pruebas
nativas usan su propia configuración y su simulación de `Arduino.h`.

En otra máquina, instalar Python y preparar las herramientas:

```powershell
python -m pip install -r requirements-dev.txt
python -m tools.verify
```

En Linux se usan esos mismos comandos Python. La verificación incluye pruebas
nativas C++, servidor, recorrido TCP de 5 s y compilación de los dos firmwares.
Para omitir solamente la compilación ESP32:

```powershell
.\tools\verify.cmd --software-only
```

## Configurar los ESP32

1. Montar ambos objetos siguiendo [hardware.md](docs/hardware.md).
2. Copiar `firmware/include/Config.example.h` a `firmware/include/Config.local.h`.
3. Completar SSID, contraseña WiFi, **IPv4 local del PC** y puerto TCP. El archivo
   local queda ignorado por Git. Los valores de ejemplo permiten compilar, pero
   deben reemplazarse antes de utilizar el prototipo.
4. Ambos ESP32 deben poder alcanzar al PC en la red local. Una red de invitados
   con aislamiento entre equipos puede impedir la comunicación.

Pines en [Config.h](firmware/include/Config.h): sensor TRIG 5 y ECHO 18; actuador
rojo 25, amarillo 26 y verde 27. Cada ESP32 utiliza solamente su conjunto.

## Ejecutar el servidor

Desde la raíz:

```powershell
.\tools\python.cmd -m server --host 0.0.0.0 --port 5000 --log-file logs/server.jsonl
```

`0.0.0.0` es la dirección de escucha. Los ESP32 usan la IP local concreta del PC,
obtenida mediante `ipconfig`. Permitir TCP entrante al puerto 5000 en el firewall
para la red privada utilizada. Detener el servidor con `Ctrl+C`.

## Compilar y cargar

```powershell
.\tools\pio.cmd run -d firmware -e sensor
.\tools\pio.cmd run -d firmware -e actuator
.\tools\pio.cmd device list
.\tools\pio.cmd run -d firmware -e sensor -t upload --upload-port COM_SENSOR
.\tools\pio.cmd run -d firmware -e actuator -t upload --upload-port COM_ACTUATOR
.\tools\pio.cmd device monitor --port COM_SENSOR --baud 115200
```

Sustituir los marcadores por los puertos reales y cargar el programa correspondiente
en cada placa. Los logs muestran IP, registro, muestras y comandos. Abrir un monitor
serial puede reiniciar la placa según el adaptador/controlador; iniciar las pruebas
de estabilidad después del arranque.

## Simular sin hardware

En tres terminales independientes:

```powershell
# Terminal 1.
.\tools\python.cmd -m server
# Terminal 2.
.\tools\python.cmd -m tools.simulate_actuator
# Terminal 3.
.\tools\python.cmd -m tools.simulate_sensor --repeat
```

Comprobación autónoma que inicia su propio servidor en un puerto libre y cierra
todos los sockets al terminar:

```powershell
.\tools\python.cmd -m tools.smoke_test --duration 60
```

La simulación verifica mensajes y estados lógicos. Exactitud, frecuencia física
de LEDs, respuesta y estabilidad de los objetos se comprueban con el
[plan de validación](docs/validation.md).

## Documentación para la entrega

- [Informe de práctica 2](informe.md).
- [Planificación](PLANIFICACION.md) y [etapas](docs/ETAPAS.md).
- [Implementación y trazabilidad](docs/implementation.md).
- [Arquitectura y funcionamiento](docs/architecture.md).
- [Diagramas](docs/diagrams/design.md) y [montaje](docs/hardware.md).
- [Validación física](docs/validation.md).

Cada integrante debe hacer sus propios commits. Verificar el acceso del docente,
incorporar las evidencias del prototipo y entregar el enlace por LMS-UCB.
