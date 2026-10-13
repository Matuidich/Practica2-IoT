# Planificación y cierre — Práctica 2

**Actividad:** Integración de Objetos Inteligentes con TCP/IP.

**Base:** [enunciado](Práctica_2.md) e [informe existente](informe.md).

**Seguimiento:** [estado por etapas](docs/ETAPAS.md) y [verificaciones de software](docs/evidence/software-validation.md).

La entrega se organiza como un monorepo con dos clientes ESP32, un servidor TCP
Python, el protocolo compartido, pruebas y documentación. El informe existente
se conserva; el [complemento técnico](docs/implementation.md) explica el código.

## Arquitectura y responsabilidades

- **ESP32 sensor:** obtiene distancia con HC-SR04 y transmite una lectura cada 250 ms.
- **Servidor TCP en PC:** registra ambos clientes, valida mensajes, clasifica la
  distancia y genera comandos para el actuador.
- **ESP32 actuador:** recibe comandos y controla tres LEDs, manteniendo el
  parpadeo con temporización y atendiendo la conexión.

Ambos ESP32 inician conexiones TCP independientes al PC sobre WiFi. La actuación
se decide en el servidor y se ejecuta en el segundo objeto. Ver
[arquitectura y funcionamiento](docs/architecture.md) y [diagramas](docs/diagrams/design.md).

## Organización

```text
Practica2-IoT/
├── firmware/       # PlatformIO: sensor y actuator; bibliotecas compartidas
├── server/         # Sockets TCP, clasificación, control y pruebas
├── contracts/      # Protocolo y casos comunes C++ / Python
├── tools/          # Simuladores, captura y verificación
├── docs/           # Arquitectura, circuitos, implementación y evidencias
├── .github/        # Verificaciones automáticas
├── informe.md      # Informe de la práctica 2
├── Práctica_2.md    # Enunciado
├── README.md       # Configuración y ejecución
└── PLANIFICACION.md
```

## Etapas

| Etapa | Trabajo | Criterio de cierre | Estado |
| --- | --- | --- | --- |
| 0. Preparación | Herramientas, dos ESP32, montaje, red y configuración. | Clientes alcanzan la IP y puerto del PC. | Herramientas listas; configuración y montaje pendientes. |
| 1. Monorepo | Fuentes, configuración de ejemplo y entornos separados. | Dos firmwares y entrada del servidor disponibles. | Implementada. |
| 2. Contrato y servidor | Roles, delimitación TCP, rangos, comandos y timeouts. | Pruebas del servidor y contrato aprobadas. | Implementada y probada. |
| 3. Firmwares | Adquisición, envío, actuación, parpadeo y reconexión. | Compilaciones sensor/actuator satisfactorias. | Implementada y compilada. |
| 4. Integración | Flujo completo, límites, datos inválidos y recuperación. | Funcionamiento en la LAN con ambos objetos. | Software probado; hardware pendiente. |
| 5. Validación y entrega | Medidas físicas, evidencias, informe, demo y defensa. | Requisitos demostrados y repositorio accesible para el docente. | Guías y herramientas listas; pruebas físicas y cierre pendientes. |

## Control y protocolo

| Distancia en centímetros | Comportamiento |
| --- | --- |
| `0 < d < 20` | Rojo parpadea a 4 Hz; otros apagados. |
| `20 <= d <= 40` | Amarillo fijo; otros apagados. |
| `d > 40` | Verde fijo; otros apagados. |
| Medición inválida o datos vencidos | Todos apagados. |

Los límites 20 y 40 pertenecen al rango intermedio. El
[contrato](contracts/protocol.md) mantiene `REGISTER`, `POST` y `SET` del informe,
con extensiones opcionales para secuencias, registro confirmado y diagnóstico.
Cada mensaje termina en salto de línea; los receptores manejan fragmentos y
líneas agrupadas mediante buffers acotados.

## Validación pendiente

1. Configurar WiFi, IPv4 del PC y puerto en `Config.local.h`; cargar los programas
   en sus respectivos ESP32 y comprobar registro.
2. Verificar los tres rangos y sus fronteras, mediciones inválidas y reconexiones.
3. Exactitud: al menos 10 muestras por referencia a 10, 20, 30, 40, 50 y 60 cm;
   comprobar error absoluto máximo de 3 cm.
4. Respuesta: medir sensor → servidor → actuador con una referencia temporal común;
   máximo declarado de 1 s.
5. Muestreo: capturar al menos 60 s y verificar un mínimo de 2 lecturas/s.
6. Estabilidad: ejecutar 15 minutos, registrar incidencias y verificar el mínimo
   de 10 minutos sin reinicios ni bloqueos.

Ver los procedimientos y comandos en [validation.md](docs/validation.md).

## Lista de entrega

- [ ] Configuración de red y prototipo funcional con los dos ESP32.
- [ ] Fotografías del montaje y datos crudos de las pruebas físicas.
- [ ] Informe Markdown con las ocho secciones exigidas, completando el contenido existente.
- [ ] Diagramas de arquitectura, circuito de cada objeto, clases y secuencia.
- [ ] Protocolo, rangos y resultados coherentes con el código.
- [ ] Commits propios de cada integrante y ensayo de demo/defensa.
- [ ] Repositorio accesible en GitHub y enlace enviado por LMS-UCB dentro del plazo del enunciado.
