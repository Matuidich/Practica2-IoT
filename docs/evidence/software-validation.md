# Verificaciones de software — 13 de octubre de 2026

Estos resultados proceden de ejecuciones locales del código de la práctica 2.
No acreditan todavía el funcionamiento de los sensores/LEDs reales sobre WiFi.

## Entorno

- Windows, Python 3.13.16 local en `.tools/python/`.
- PlatformIO Core 6.2.0 y plataforma `espressif32@6.13.0`.
- Arduino `2.0.17`: paquete `3.20017.241212+sha.dcc1105b`.
- Compilador ESP32 `8.4.0+2021r2-patch5`; esptool `4.11.0`.
- Pruebas de escritorio C++ con `g++`, C++17 y `-Wall -Wextra -Werror`.

## Pruebas ejecutadas

| Comprobación | Resultado |
| --- | --- |
| `python -m unittest discover -s server/tests -v` | 29 pruebas aprobadas. |
| Contrato compartido C++ / Python | 30 casos válidos/invalidos verificados en ambos lenguajes. |
| Pruebas C++ con GPIO simulado | Delimitación, parpadeo 2/4 Hz, fase ante comando repetido, reloj desbordado, inicialización y cálculo ultrasónico aprobados. |
| Compilación `sensor` | SUCCESS; firmware generado. RAM 45 312 bytes; flash 754 025 bytes. |
| Compilación `actuator` | SUCCESS; firmware generado. RAM 45 352 bytes; flash 753 681 bytes. |
| Compilación sintáctica de módulos Python | Aprobada con `compileall`. |
| Integridad de `informe.md` | SHA-256 idéntico antes y después de la implementación. |

La integración usa sockets TCP reales en loopback. Incluye registro, conexiones
en distinto orden, roles duplicados, lecturas inválidas, mensajes divididos y
agrupados, errores recuperables, apagado por timeout y reconexión de los dos roles.

## Recorrido continuo en loopback

Comando: `python -m tools.smoke_test --duration 60`.

```json
{
  "scope": "software_loopback",
  "duration_s": 60.0,
  "messages": 240,
  "messages_per_s": 4.0,
  "max_exchange_ms": 3.643,
  "physical_requirements_verified": false
}
```

El tiempo corresponde al intercambio local entre simuladores, incluyendo envío
de confirmación; varía con el equipo y no es una medida sensor físico → LED físico.
Un minuto de software tampoco acredita los 10 minutos de estabilidad del montaje.

## Evidencias físicas pendientes

- Dos ESP32 identificados y conectados a la LAN, con configuración real de WiFi.
- Fotografías de los circuitos y comportamiento de los tres rangos.
- Referencias físicas 10–60 cm, al menos 10 muestras por punto y error máximo ≤ 3 cm.
- Medición extremo a extremo con una referencia temporal común, máximo ≤ 1 s.
- Cadencia del sensor durante 60 s, al menos 2 lecturas/s.
- Prueba de estabilidad de 15 minutos del sistema distribuido completo.

Se consultaron los puertos seriales: solo se enumeró `COM1`, sin identificación
de dos ESP32 disponibles. No se ejecutó una carga ni se registraron mediciones
físicas en esta sesión.
