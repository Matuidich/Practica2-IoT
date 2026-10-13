# Diagramas de la implementación

Complemento del [informe existente](../../informe.md). Los circuitos de los dos
objetos están en [sensor.svg](sensor.svg) y [actuator.svg](actuator.svg); su montaje
se describe en [hardware.md](../hardware.md).

## Arquitectura

```mermaid
flowchart LR
    subgraph WIFI["Red local WiFi — IEEE 802.11"]
        HC["HC-SR04"] --> S["ESP32 sensor<br/>UltrasonicSensor + TcpConnection"]
        P["PC<br/>TcpServer + ControlService"]
        A["ESP32 actuador<br/>TcpConnection + LedController"] --> L["3 LEDs"]
        S -->|"Conexión TCP / REGISTER / POST"| P
        A -->|"Conexión TCP / REGISTER / APPLIED"| P
        P -->|"SET por la conexión del actuador"| A
    end
```

## Secuencia

```mermaid
sequenceDiagram
    participant S as ESP32 sensor
    participant P as Servidor TCP Python
    participant A as ESP32 actuador
    S->>P: Conectar TCP
    A->>P: Conectar TCP
    S->>P: REGISTER type=sensor version=1
    P-->>S: OK type=sensor version=1
    A->>P: REGISTER type=actuator version=1
    P-->>A: OK type=actuator version=1
    P->>A: SET todos off
    A-->>P: APPLIED
    loop Cada 250 ms
        S->>S: Adquirir distancia (timeout 30 ms)
        S->>P: POST seq=n distance=d
        P->>P: Validar y clasificar d
        alt d menor que 20 cm
            P->>A: SET seq=n rojo blink_4, otros off
        else 20 cm hasta 40 cm inclusive
            P->>A: SET seq=n amarillo on, otros off
        else d mayor que 40 cm
            P->>A: SET seq=n verde on, otros off
        end
        A->>A: Aplicar salida y conservar fase si no cambió el modo
        A-->>P: APPLIED seq=n
    end
    opt Medición inválida
        S->>P: POST seq=n status=invalid
        P->>A: SET seq=n todos off
    end
    opt Sensor desconectado o mediciones vencidas
        P->>A: SET todos off
    end
    opt Actuador pierde conexión o no recibe SET durante 2 s
        A->>A: Apagar LEDs y reintentar conexión
    end
```

Las etiquetas abreviadas `todos off` y `otros off` representan los tres argumentos
completos descritos en el [contrato](../../contracts/protocol.md).

## Clases

```mermaid
classDiagram
    class UltrasonicSensor {
        +begin()
        +getDistance() Measurement
    }
    class Measurement {
        +isValid() bool
        +distanceCm() bool
    }
    class WifiConnection {
        +begin(ssid, password)
        +update(now) bool
    }
    class TcpConnection {
        +begin(host, port, role)
        +update(now, wifiOnline)
        +nextMessage(message) bool
        +sendLine(line) bool
        +ready() bool
        +disconnect()
    }
    class ProtocolCodec {
        +parse(line) Message
        +encode(message) bytes
    }
    class LineBuffer {
        +feed(data) lines
    }
    class LedController {
        +begin()
        +apply(command, now)
        +update(now)
        +off(now)
    }
    class TcpServer {
        +start()
        +handle(session, message)
        +disconnected(session)
        +stop()
    }
    class ClientSession {
        +send(message) bool
        +close()
    }
    class DeviceRegistry {
        +register(role, session) bool
        +get(role) ClientSession
        +remove(session)
    }
    class ControlService {
        +command_for(distance, sequence) Message
    }
    class DistanceClassifier {
        +classify(distance) DistanceState
    }
    UltrasonicSensor --> Measurement
    TcpConnection --> WifiConnection : disponibilidad recibida por la app
    TcpConnection *-- LineBuffer
    TcpConnection --> ProtocolCodec
    LedController --> ProtocolCodec : estados del mensaje
    TcpServer *-- DeviceRegistry
    TcpServer *-- ControlService
    TcpServer --> ClientSession
    ClientSession --> LineBuffer
    ClientSession --> ProtocolCodec
    ControlService *-- DistanceClassifier
```

`ProtocolCodec` y `LineBuffer` tienen implementaciones C++ y Python con la misma
gramática; sus firmas concretas cambian según el lenguaje (`push` en C++, `feed`
en Python). El diagrama resume ambas implementaciones. Las aplicaciones ESP32
coordinan adquisición, conectividad y actuación en sus `setup()`/`loop()`.
