# Implementación complementaria de la práctica 2

Este documento acompaña el [informe existente](../informe.md). Conserva su arquitectura
ESP32 sensor → servidor Python → ESP32 actuador y sus comandos de aplicación.
Las precisiones de rangos, delimitación y diagnóstico se documentan aquí y en el
[contrato](../contracts/protocol.md) sin reemplazar el contenido ya escrito.

## Requerimientos y trazabilidad

| Informe actual | Enunciado | Implementación | Verificación |
| --- | --- | --- | --- |
| RF01: medir | RF1 | [UltrasonicSensor](../firmware/lib/UltrasonicSensor/src/UltrasonicSensor.cpp) y [cliente sensor](../firmware/src/sensor/main.cpp) | Prueba nativa del cálculo/validez y medición física pendiente. |
| RF02: TCP | RF4 | [TcpConnection](../firmware/lib/Communication/src/TcpConnection.cpp) y [TcpServer](../server/tcp_server.py) | Integración con sockets reales en loopback; WiFi real pendiente. |
| RF03: rangos | RF2 | [DistanceClassifier](../server/controller.py) | Valores interiores y fronteras 20/40. |
| RF04: actuadores | RF3 y RF4 | `ControlService` y [LedController](../firmware/lib/LedController/src/LedController.cpp) | Comandos por rango y temporización nativa; salida física pendiente. |
| RF05: protocolo | RF4 | [Parser Python](../server/protocol.py), [parser C++](../firmware/lib/Communication/src/ProtocolCodec.cpp) y contrato | 30 casos compartidos, delimitación, errores y roles. |
| RNF01: estabilidad | Estabilidad | Timeouts, reconexión y memoria acotada | [Plan físico de 15 minutos](validation.md), pendiente. |
| RNF02: exactitud | Exactitud | Adquisición y CSV por muestra | Capturas de referencia 10–60 cm pendientes. |
| RNF03: respuesta | Respuesta | Muestreo de 250 ms y actuación sin `delay()` | Captura común sensor/actuador pendiente. |
| RNF04: muestreo | Muestreo | Temporización y log de cada adquisición | Captura serial de 60 s pendiente. |
| RNF05: modularidad | Código modular POO | Clases de medición, comunicación, LEDs, sesiones y control | Diagramas, pruebas y separación de responsabilidades. |

Los rangos implementados son `0 < d < 20`, `20 <= d <= 40` y `d > 40`.
Los límites de 20 y 40 cm pertenecen al rango intermedio. El sensor
transmite centímetros con resolución decimal de 0,01 cm; la clasificación aplica
al valor transmitido. Una lectura sin eco es `status=invalid`, que apaga los LEDs.

## Diseño y ejecución

Ver los [diagramas propios](diagrams/design.md) y el [montaje de ambos circuitos](hardware.md).

El sensor llama a `begin()` para inicializar los pines antes de medir. La espera
del eco mantiene su límite de 30 ms. Adquiere cada 250 ms, genera una secuencia
y transmite solo si la sesión TCP está registrada; no acumula lecturas desconectado.

El servidor mantiene un socket de escucha y un hilo por cliente. `DeviceRegistry`
asocia conexiones a roles; `ClientSession` delimita mensajes y completa envíos.
`DistanceClassifier` decide el rango y `ControlService` produce el `SET`. Se
coordinan el registro y el control con locks y se serializan escrituras por conexión.
El watchdog envía apagado cuando deja de recibir mediciones aceptadas.

El actuador empieza apagado. `LedController` instala un estado inmediatamente y
actualiza el parpadeo según `millis()`, conservando la fase ante comandos repetidos.
La resta de tiempos de 32 bits admite el desbordamiento del reloj. `TcpConnection`
emplea envíos no bloqueantes por el descriptor del socket y un mensaje pendiente
acotado. `APPLIED` se emite después de instalar las salidas; permite diagnóstico.

La configuración PlatformIO fija ESP32 `6.13.0`, que utiliza Arduino `2.0.17`.
Los dos entornos comparten biblioteca de comunicación y excluyen las fuentes del
otro objeto. La configuración local de WiFi se ignora en Git y el ejemplo permite
compilar CI sin credenciales.

## Pruebas y límites de los resultados

Las [pruebas del servidor](../server/tests/test_tcp_server.py) abren sockets TCP
reales en puertos efímeros, prueban mensajes del informe y las extensiones, orden
de conexiones, reconexión, errores y pérdida de datos. Las pruebas del controlador
validan 19,99; 20; 20,01; 39,99; 40 y 40,01 cm, además de entradas inválidas.

La [verificación nativa C++](../tools/test_firmware.py) compila el parser y las
clases de sensor y LEDs con GPIO simulado. Verifica temporización de 2/4 Hz,
conservación de fase, desbordamiento del reloj, inicialización y cálculo del sensor.
No equivale a medir el sensor ni el LED real.

La [prueba de recorrido TCP](../tools/smoke_test.py) permite repetir intercambios
durante un intervalo declarado y reporta su alcance como `software_loopback`.
Los [resultados de esta sesión](evidence/software-validation.md) documentan lo
ejecutado. Exactitud, respuesta física, WiFi real y estabilidad del montaje
requieren las evidencias descritas en [validation.md](validation.md).

## Conclusiones y recomendaciones de implementación

La arquitectura separa adquisición, decisión y actuación conforme al enunciado.
La implementación conserva los formatos ya definidos y hace explícito el manejo
de un flujo TCP, de datos inválidos y de conexiones que dejan de producir datos.
Las pruebas automáticas comprueban el comportamiento de software; las conclusiones
sobre el prototipo se completarán con medidas físicas.

Realizar una prueba física de 15 minutos, registrar cada incidencia y verificar
alimentación, conexiones y logs antes de atribuir su causa. Cada integrante debe revisar los
tres componentes y realizar sus propios commits para preparar la defensa individual.
