# Validación del prototipo y evidencias

El [informe actual](../informe.md) declara 10 minutos sin reinicios/bloqueos,
error máximo de 3 cm, respuesta de hasta 1 s y al menos 2 lecturas/s. Estas pruebas
permiten comprobar esos objetivos con el montaje real. Las verificaciones de
software se registran por separado en [software-validation.md](evidence/software-validation.md).

## Preparación y pruebas funcionales

1. Completar WiFi/IP/puerto en `Config.local.h`, cargar ambos firmwares y comprobar
   registro de sensor y actuador en el servidor.
2. Guardar fotografías de cada circuito y su montaje, y logs del PC y ambos ESP32.
3. Recorrer distancias cercanas, intermedias y lejanas, comprobando rojo a 4 Hz,
   amarillo fijo y verde fijo. Verificar que los otros dos LEDs estén apagados.
4. Contrastar los límites con las pruebas deterministas de 19,99; 20; 20,01;
   39,99; 40 y 40,01 cm. En el montaje se clasifica la lectura transmitida, que
   puede diferir de la distancia de la cinta métrica por el error del sensor.
5. Provocar falta de eco y comprobar `status=invalid` y apagado. Desconectar cada
   ESP32 y reiniciar el servidor; verificar apagado y registro nuevo al recuperarse.
6. Iniciar el sensor antes del actuador y viceversa; comprobar que una conexión
   nueva no ejecute comandos basados en lecturas anteriores.

## Exactitud (RNF02)

- Declarar inicialmente un intervalo de trabajo de **10–60 cm**.
- Fijar una superficie plana perpendicular al sensor y medir con cinta métrica.
- Obtener al menos 10 lecturas por punto a 10, 20, 30, 40, 50 y 60 cm.
- Calcular por cada lectura válida `abs(distance_cm - reference_cm)` y conservar
  el máximo. El promedio no sustituye este criterio de máximo.
- Registrar también las mediciones inválidas, el montaje y las condiciones de prueba.

Ejemplo de captura real, desde la raíz, sustituyendo el puerto:

```powershell
.\tools\python.cmd -m tools.capture_serial --port COM_SENSOR --seconds 10 --reference-cm 20 --output docs/evidence/exactitud-20cm.csv
.\tools\python.cmd -m tools.analyze_measurements docs/evidence/exactitud-20cm.csv
```

El capturador crea archivos nuevos y no sobrescribe evidencias anteriores. Abrir
el puerto serial puede reiniciar la placa; esperar su registro antes de seleccionar
el intervalo útil. Si la referencia cambia durante la captura, separar archivos.

**Aceptación:** error máximo observado ≤ 3 cm en el intervalo declarado. El resultado
`referenced_valid_samples_within_3_cm` se refiere solamente a muestras válidas que
tienen referencia; revisar el número de muestras, los inválidos y la cobertura de
los seis puntos antes de concluir cumplimiento del requisito.

## Muestreo (RNF04)

Capturar al menos 60 s de adquisiciones del sensor. La rutina de adquisición marca
cada muestra con `seq` y `sensor_time_ms`; `sent` indica si el envío pudo ponerse
en marcha en la conexión y no constituye una confirmación física del actuador.

```powershell
.\tools\python.cmd -m tools.capture_serial --port COM_SENSOR --seconds 65 --output docs/evidence/muestreo.csv
.\tools\python.cmd -m tools.analyze_measurements docs/evidence/muestreo.csv
```

Seleccionar un intervalo continuo de 60 s después del arranque y contar al menos
120 muestras. Contrastar las secuencias con los logs `measurement` del servidor.
La herramienta informa la cadencia de **muestras capturadas**, el máximo intervalo
y muestras faltantes en serial. No interpretar una captura con pérdidas o reinicios
como una medida completa de la adquisición; separar las sesiones si hubo reinicio.

**Aceptación:** al menos 2 lecturas/s durante el intervalo declarado. El objetivo
de diseño es 4 lecturas/s; reportar también interrupciones e intervalos observados.

## Respuesta extremo a extremo (RNF03)

Medir en una referencia temporal común desde el inicio de adquisición del sensor
hasta el cambio físico de salida del actuador. Opciones:

- Analizador lógico: capturar el flanco TRIG del sensor y la salida GPIO del LED
  del actuador, con la tierra común necesaria para la medición. Relacionar la
  lectura que cambia de rango con su `seq` en los logs.
- Video: incluir un marcador visible de adquisición y el LED, declarar tasa de
  cuadros y documentar cómo se identificaron los dos instantes. Si hace falta
  un marcador adicional, agregarlo al montaje de prueba antes de afirmar esta medida.

Repetir al menos 10 veces cada transición entre rangos, guardar video/captura y
completar [response-template.csv](evidence/response-template.csv). El tiempo incluye
adquisición, transporte, control y salida; no restar relojes de distintas placas
sin sincronización. `APPLIED` y la latencia de loopback son datos de diagnóstico,
no pruebas por sí solos de este requisito físico.

**Aceptación:** máximo observado ≤ 1 s. Declarar resolución de la medición y sus
limitaciones. Verificar además el parpadeo rojo de 4 Hz con captura de señal o video.

## Estabilidad (RNF01)

Ejecutar el montaje completo por **15 minutos** para verificar el funcionamiento
más allá del mínimo declarado de 10 minutos. Mantener activos ambos clientes y el
servidor, mover el objeto entre rangos y registrar:

- Hora inicial/final y duración.
- Reinicios y bloqueos de cada componente.
- Lecturas inválidas, desconexiones y recuperación.
- Comportamiento durante el mínimo de 10 minutos y durante el intervalo completo.
- Logs y evidencia de cualquier anomalía, sin atribuir una causa que no se comprobó.

**Aceptación mínima:** 10 minutos continuos sin reinicios ni bloqueos. La prueba
extendida debe reportarse íntegra aunque aparezcan errores después del mínimo.
Las pruebas deliberadas de desconexión se hacen en otra ejecución para distinguir
incidencias inducidas del funcionamiento normal.

## Registro y cierre

Cada evidencia debe incluir fecha, versión del código, responsables, condiciones,
datos crudos y conclusión fundada. Las plantillas contienen solamente cabeceras;
no son mediciones ni resultados aprobados. Utilizar fotografías de los dos objetos
de este montaje para respaldar las pruebas del sistema distribuido.

El grupo puede completar las secciones pendientes de su informe con estas medidas,
los [diagramas](diagrams/design.md) y la [implementación](implementation.md), manteniendo
sus textos existentes. Ensayar demo y defensa individual, comprobar los commits
de ambos integrantes y entregar el enlace del repositorio por LMS-UCB.
