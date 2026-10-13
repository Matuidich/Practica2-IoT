# Protocolo de aplicación de la práctica 2

Esta especificación concreta los mensajes de [informe.md](../informe.md). Los
formatos originales siguen siendo válidos. `version`, `seq`, `status`, `OK`,
`APPLIED` y `ERROR` agregan confirmación de registro y diagnóstico.

## Transporte y delimitación

- TCP IPv4, puerto configurable; predeterminado `5000`.
- Cada ESP32 inicia una conexión independiente al PC y la mantiene abierta.
- ASCII imprimible, un mensaje por línea terminada en LF (`\n`). Se acepta CRLF.
- Máximo 256 bytes antes del terminador, excluyendo el CR opcional de CRLF.
- Las claves distinguen mayúsculas. Se aceptan espacios y comas como separadores
  y cualquier orden de argumentos. Claves repetidas o desconocidas se rechazan.
  Tabulaciones y otros caracteres de control son inválidos.
- Distancias positivas y finitas, en centímetros, con punto decimal. Sin signo,
  notación exponencial, coma decimal, `nan` ni `inf`.
- Las recepciones pueden contener fragmentos o varias líneas. Los receptores
  conservan buffers acotados; los emisores completan escrituras parciales.
  Véase la [documentación de sockets de Python](https://docs.python.org/3/howto/sockets.html#using-a-socket).

## Mensajes

| Mensaje | Dirección | Obligatorios | Opcionales |
| --- | --- | --- | --- |
| `REGISTER` | Cliente → servidor | `type=sensor` o `type=actuator` | `version=1` |
| `OK` | Servidor → cliente | `type` del cliente | `version=1`, si llegó en el registro |
| `POST` válido | Sensor → servidor | `distance=<cm>` | `seq=<entero>` |
| `POST` inválido | Sensor → servidor | `status=invalid` | `seq=<entero>` |
| `SET` | Servidor → actuador | `redLed`, `yellowLed`, `greenLed` | `seq=<entero>` |
| `APPLIED` | Actuador → servidor | Ninguno | `seq=<entero>` |
| `ERROR` | Servidor → cliente | `code=<código>` | Ninguno |

Cada LED acepta `on`, `off`, `blink_2` y `blink_4`. Los intervalos de alternancia
son 250 y 125 ms, con 50 % de ciclo de trabajo. Repetir un comando idéntico conserva
la fase del parpadeo.

`seq` pertenece a `[0, 4294967295]`. Correlaciona muestras dentro de una sesión;
puede reiniciarse al reiniciar el sensor y desbordarse como un contador de 32 bits.
No es una fecha ni un criterio para ordenar sesiones distintas. El servidor copia
el `seq` del `POST` al `SET`; si no existe en la lectura, tampoco se agrega al comando.
Los apagados por conexión o timeout no llevan secuencia. `APPLIED` confirma la
instalación de la primera salida del estado, no el transcurso de un ciclo completo
de parpadeo ni toda la latencia desde el sensor.

Ejemplos compatibles con el informe:

```text
REGISTER type=sensor
POST distance=9
SET redLed=blink_4, yellowLed=off, greenLed=off
```

Secuencia de los firmwares nuevos:

```text
REGISTER type=actuator version=1
OK type=actuator version=1
SET redLed=off, yellowLed=off, greenLed=off
APPLIED
REGISTER type=sensor version=1
OK type=sensor version=1
POST seq=42 distance=19.80
SET seq=42 redLed=blink_4, yellowLed=off, greenLed=off
APPLIED seq=42
POST seq=43 status=invalid
SET seq=43 redLed=off, yellowLed=off, greenLed=off
APPLIED seq=43
```

## Estados y recuperación

1. El cliente tiene 3 s para registrarse. No puede enviar datos antes de `REGISTER`.
2. Un cliente activo por rol. Un registro duplicado se rechaza y se cierra;
   un cliente registrado no puede cambiar de rol.
3. Un actuador nuevo recibe apagado y espera una lectura nueva. No se reproduce
   ninguna lectura obtenida antes de su conexión.
4. Solo el sensor puede enviar `POST`; solo el actuador puede enviar `APPLIED`.
5. `status=invalid` provoca apagado. Un mensaje mal formado genera `ERROR` y no
   renueva la vigencia de la última medición.
6. El servidor apaga al cerrar el sensor o transcurrir 2 s sin un mensaje de
   medición aceptado. El actuador tiene un timeout propio de 2 s sin `SET` válido
   y también apaga cuando detecta desconexión.
7. El sensor adquiere cada 250 ms y transmite un comando por muestra, incluso si
   el rango no cambia. Durante desconexiones adquiere sin guardar una cola.
8. Reintentos TCP cada 2 s y WiFi cada 5 s; cada conexión nueva vuelve a registrar
   el rol. Intentos TCP limitados a 300 ms. Envíos no bloqueantes con un único
   mensaje pendiente y timeout de 300 ms.

| Error | Situación | Acción del servidor |
| --- | --- | --- |
| `BAD_MESSAGE` | Sintaxis, clave, valor o comando inválido | Permite el siguiente mensaje correcto. |
| `LINE_TOO_LONG` | Buffer excedido | Cierra la conexión. |
| `REGISTER_REQUIRED` | Datos antes del registro | Espera registro dentro del plazo. |
| `REGISTER_TIMEOUT` | Registro ausente durante 3 s | Cierra la conexión. |
| `ROLE_IN_USE` | El rol ya tiene cliente | Rechaza y cierra al nuevo cliente. |
| `ALREADY_REGISTERED` | Segundo registro en la misma sesión | Conserva el rol original. |
| `WRONG_ROLE` | Comando incompatible con el rol | Rechaza el comando. |
| `UNSUPPORTED_VERSION` | Versión distinta de 1 | Rechaza el mensaje. |

Un error de delimitación o codificación cierra la conexión. Los firmwares
desconectan/reintentan ante mensajes inválidos del servidor o un `ERROR`.

## Control y conformidad

| Distancia | Rojo | Amarillo | Verde |
| --- | --- | --- | --- |
| `0 < d < 20` | `blink_4` | `off` | `off` |
| `20 <= d <= 40` | `off` | `on` | `off` |
| `d > 40` | `off` | `off` | `on` |
| Medición inválida o datos vencidos | `off` | `off` | `off` |

Los [30 casos comunes](protocol-cases.json) se ejecutan contra Python y C++.
Las [pruebas TCP](../server/tests/test_tcp_server.py) verifican roles, fragmentos,
agrupación, fronteras, conexión en distintos órdenes, timeouts y reconexión.
