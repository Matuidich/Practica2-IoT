# Estado de implementación por etapas

Fecha: 13 de octubre de 2026. El [informe de práctica 2](../informe.md) se conservó
sin cambios; la implementación se construyó sobre su arquitectura y sus comandos.
El [complemento técnico](implementation.md) documenta las precisiones y el código.

| Etapa del plan | Estado | Resultado |
| --- | --- | --- |
| 0. Preparación | Herramientas listas; montaje pendiente | Python 3.13.16 y PlatformIO Core 6.2.0 preparados localmente. Falta configurar WiFi/IP y conectar/identificar los dos ESP32. |
| 1. Monorepo | Implementada | `firmware/`, `server/`, `contracts/`, `tools/`, `docs/` y CI. Bibliotecas de medición, comunicación y actuación. |
| 2. Contrato y servidor | Implementada y probada | Sockets, roles, control central, buffers acotados, timeouts, apagado y simuladores. Compatibilidad con mensajes del informe. |
| 3. Dos firmwares | Implementada y compilada | Objetos sensor/actuador independientes; inicialización del sensor, reconexión y parpadeo sin `delay()`. Dos `.bin` generados. |
| 4. Integración | Software verificado; hardware pendiente | 29 pruebas Python, 30 casos de contrato C++, pruebas nativas y 60 s de intercambio con dos clientes TCP. Falta validar WiFi y salidas reales. |
| 5. Validación y entrega | Documentación y herramientas preparadas | Diagramas, circuitos, guía de montaje, captura/análisis CSV y plan físico. Faltan mediciones, fotos, completar resultados del informe por el grupo y entrega GitHub/LMS. |

## Evidencia de software

Ver [software-validation.md](evidence/software-validation.md). El recorrido de
60 s procesó 240 mensajes a 4 mensajes/s sin errores de correspondencia. La medición
de intercambio local no sustituye la respuesta física ni los restantes RNF.

Los ejecutables de firmware se encuentran en:

- `firmware/.pio/build/sensor/firmware.bin`.
- `firmware/.pio/build/actuator/firmware.bin`.

La carpeta `.pio/` se ignora en Git. Las fuentes y la configuración permiten
reconstruir ambos archivos en otra máquina.

## Siguiente etapa física

1. Completar `firmware/include/Config.local.h` y confirmar IP/puerto del PC.
2. Montar los [dos circuitos](hardware.md), identificar puertos USB y cargar cada firmware.
3. Ejecutar el servidor y verificar los tres rangos, límites y recuperación.
4. Seguir [validation.md](validation.md) para exactitud, muestreo, respuesta y estabilidad.
5. Incorporar las evidencias reales y completar el informe existente; cada integrante
   realiza sus propios commits y prepara la defensa.

CI está configurado para ejecutar pruebas y compilaciones cuando se publique el
cambio. No se ha comprobado una ejecución remota de GitHub Actions en esta sesión.
