# Arquitectura y funcionamiento — Práctica 2

El sistema tiene tres componentes: un objeto que mide, una computadora que decide
y otro objeto que actúa. Comparten una red WiFi y se comunican mediante TCP.

```mermaid
flowchart LR
    U["HC-SR04"] --> S["ESP32 sensor<br/>Mide y envía"]
    S -->|"POST: distancia"| P["PC: servidor Python<br/>Valida y decide"]
    P -->|"SET: estados de LEDs"| A["ESP32 actuador<br/>Ejecuta el comando"]
    A --> L["Rojo / amarillo / verde"]
    A -.->|"APPLIED: confirmación"| P
```

## Clientes y servidor

La computadora ejecuta el servidor y escucha normalmente en el puerto **5000**.
Cada ESP32 se conecta a esa IP/puerto: hay una conexión para el sensor y otra
para el actuador. Los dos son clientes aunque el actuador reciba instrucciones.
El servidor envía comandos por la conexión que el actuador ya abrió.

Al conectarse, cada objeto envía `REGISTER type=sensor` o
`REGISTER type=actuator`. El servidor confirma con `OK`, asocia el rol a su
socket y mantiene ambas conexiones abiertas. Los firmwares agregan `version=1`
como dato opcional del contrato.

## Responsabilidad de cada componente

| Componente | Responsabilidad | Código principal |
| --- | --- | --- |
| ESP32 sensor | Inicializa HC-SR04, mide, comprueba validez y envía. | [sensor/main.cpp](../firmware/src/sensor/main.cpp) |
| Servidor PC | Atiende clientes, valida, clasifica y produce comandos. | [tcp_server.py](../server/tcp_server.py) y [controller.py](../server/controller.py) |
| ESP32 actuador | Aplica estados y actualiza parpadeo de LEDs. | [actuator/main.cpp](../firmware/src/actuator/main.cpp) |

`UltrasonicSensor` encapsula la medición. `WifiConnection` y `TcpConnection`
gestionan conectividad; `ProtocolCodec` interpreta los mensajes. En Python,
`DeviceRegistry` identifica los clientes, `DistanceClassifier` decide el rango
y `ControlService` genera el comando. `LedController` modifica las salidas.

El sensor utiliza TRIG en GPIO 5 y ECHO en GPIO 18. El actuador utiliza GPIO 25,
26 y 27 para rojo, amarillo y verde. Los montajes se detallan en
[hardware.md](hardware.md).

## Recorrido de una medición

1. El ESP32 sensor genera un pulso TRIG y mide cuánto dura ECHO. Convierte ese
   tiempo en centímetros. Si no recibe eco dentro del timeout, marca la lectura
   como inválida.
2. Cada 250 ms adquiere una lectura nueva, con objetivo de 4 lecturas/s. Cuando
   está registrado, transmite un `POST` terminado en salto de línea.
3. El servidor valida la lectura y la clasifica. Esta decisión se ejecuta en Python.
4. El servidor envía `SET` por el socket del actuador.
5. El segundo ESP32 instala los estados de los LEDs y envía `APPLIED`. La secuencia
   permite relacionar lectura, comando y confirmación en los logs.

Ejemplo para 15 cm:

```text
Sensor → servidor:
POST seq=42 distance=15.00

Servidor → actuador:
SET seq=42 redLed=blink_4, yellowLed=off, greenLed=off

Actuador → servidor:
APPLIED seq=42
```

El rojo alterna cada 125 ms: 125 ms encendido y 125 ms apagado forman un ciclo
de 250 ms, equivalente a 4 Hz. La temporización se actualiza en cada vuelta del
programa mediante `millis()`, mientras continúa la atención de la conexión.

## Rangos y recuperación

| Lectura | Salida |
| --- | --- |
| `0 < d < 20 cm` | Rojo parpadeando a 4 Hz. |
| `20 <= d <= 40 cm` | Amarillo encendido. |
| `d > 40 cm` | Verde encendido. |
| Inválida | Todos apagados. |

Los otros dos LEDs están apagados en cada rango. Exactamente 20 y 40 cm son
intermedios. Una lectura inválida se envía como `POST status=invalid`.

El actuador empieza apagado y recibe otro apagado al registrarse. Si se detecta
una desconexión o transcurren 2 s sin comandos válidos, vuelve al apagado. El
servidor también envía apagado si el sensor cierra su conexión o deja de mandar
mediciones aceptadas. Los clientes reintentan conectarse y vuelven a registrarse.

## Monorepo y ejecución

Monorepo significa que estos tres programas, sus pruebas y su documentación están
en el mismo repositorio. Se compilan **dos firmwares diferentes**, uno por ESP32;
el servidor Python se ejecuta en la PC. Las bibliotecas comunes de C++ se usan
desde los dos entornos de PlatformIO.

En la configuración de los ESP32 se coloca la IP local de la PC, además del SSID,
contraseña y puerto. `0.0.0.0` es una dirección para escuchar en el servidor; los
clientes utilizan la IPv4 concreta de la PC.

Las pruebas automáticas y las compilaciones están verificadas. Para la entrega
del prototipo falta configurar la red, cargar las placas y registrar las medidas
físicas siguiendo [validation.md](validation.md). Ver ejecución y comandos en
[README.md](../README.md).
