
# Práctica 2 — Integración de Objetos Inteligentes con TCP/IP

**Asignatura:** Internet de las Cosas (SIS-234)  
**Carrera:** Ingeniería de Sistemas  
**Universidad:** Universidad Católica Boliviana  
**Integrantes:**
- Mateo Rojas Campos
- Lucia Escobar Galaburda

**Fecha de entrega:** 13 de octubre de 2026

---

## 1. Requerimientos Funcionales y No Funcionales

### 1.1 Descripción general

El proyecto consiste en el desarrollo de un sistema distribuido de objetos inteligentes que se comunican mediante sockets TCP sobre una red WiFi (IEEE 802.11).

El sistema está compuesto por tres componentes principales:

1. **Objeto inteligente sensor:** dispositivo ESP32 conectado a un sensor ultrasónico, encargado de medir distancias y transmitir los datos al servidor.
2. **Servidor TCP:** aplicación ejecutada en una computadora, responsable de recibir las mediciones, clasificarlas según los rangos establecidos y generar comandos de control.
3. **Objeto inteligente actuador:** dispositivo ESP32 encargado de recibir los comandos enviados por el servidor y controlar los actuadores correspondientes.

Ambos objetos inteligentes funcionan como clientes TCP y establecen conexiones independientes con el servidor.

Esta arquitectura permite separar las responsabilidades de adquisición de datos, procesamiento y actuación.

### 1.2 Requerimientos funcionales

| Código | Requerimiento | Descripción | Criterio de verificación |
|--------|---------------|-------------|-------------------------|
| RF01 | Medición de distancia | El ESP32 sensor debe medir la distancia entre el sensor ultrasónico y un objeto, expresada en centímetros. | Comparar las mediciones obtenidas con distancias físicas conocidas. |
| RF02 | Comunicación TCP | El ESP32 sensor debe transmitir sus mediciones al servidor mediante sockets TCP sobre WiFi. | Verificar la recepción de los mensajes en el servidor. |
| RF03 | Clasificación de distancias | El servidor debe clasificar cada medición válida en tres rangos contiguos y sin solapamiento. | Probar valores dentro de cada rango y exactamente en sus fronteras. |
| RF04 | Control de actuadores | El servidor debe enviar comandos al ESP32 actuador según el rango de distancia identificado. | Verificar que cada rango produzca el comportamiento correspondiente. |
| RF05 | Protocolo de aplicación | Los clientes y el servidor deben intercambiar mensajes utilizando un protocolo de aplicación definido por el grupo. | Comprobar el formato, contenido y secuencia de los mensajes intercambiados. |

### 1.3 Requerimientos no funcionales

Los valores establecidos representan objetivos de diseño que deberán verificarse experimentalmente durante la etapa de pruebas.

| Código | Atributo | Valor objetivo | Método de verificación |
|--------|----------|----------------|------------------------|
| RNF01 | Estabilidad | Operación continua durante al menos 10 minutos sin reinicios ni bloqueos. | Ejecutar el sistema durante 10 minutos, registrando interrupciones y errores. |
| RNF02 | Exactitud | Error absoluto máximo de 3 cm respecto a una referencia física dentro del rango de trabajo declarado. | Comparar múltiples lecturas con una cinta métrica y calcular el error absoluto. |
| RNF03 | Tiempo de respuesta | Máximo 1 segundo desde la medición hasta la actuación. | Medir el tiempo extremo a extremo mediante marcas de tiempo sincronizadas o análisis de video. |
| RNF04 | Frecuencia de muestreo | Al menos 2 lecturas por segundo. | Registrar la cantidad de mediciones realizadas durante un intervalo conocido. |
| RNF05 | Mantenibilidad | Código modular, orientado a objetos y documentado. | Revisar la separación de responsabilidades, las clases y la documentación del código. |

### 1.4 Definición de rangos y lógica de control

Los rangos de distancia y el comportamiento de los actuadores serán definidos por el grupo y documentados de acuerdo con la implementación final.

Se deberán establecer tres intervalos contiguos, sin superposiciones ni valores sin clasificar.

La definición incluirá:
- Límites exactos de cada intervalo.
- Comportamiento esperado de los actuadores.
- Tratamiento de mediciones inválidas.
- Verificación de los valores de frontera.

### 1.5 Matriz de trazabilidad

La matriz de trazabilidad permitirá relacionar cada requerimiento con los componentes responsables y las pruebas utilizadas para verificar su cumplimiento.

| Requerimiento | Componente responsable | Prueba prevista |
|---------------|------------------------|-----------------|
| RF01 | ESP32 sensor | Medición de distancias conocidas |
| RF02 | ESP32 sensor y servidor TCP | Recepción de mediciones |
| RF03 | Servidor TCP | Clasificación y valores de frontera |
| RF04 | Servidor TCP y ESP32 actuador | Respuesta de actuadores por rango |
| RF05 | Clientes TCP y servidor | Validación de mensajes |
| RNF01 | Sistema completo | Prueba de estabilidad |
| RNF02 | ESP32 sensor | Prueba de exactitud |
| RNF03 | Sistema completo | Medición de respuesta extremo a extremo |
| RNF04 | ESP32 sensor | Conteo de lecturas por segundo |
| RNF05 | Código fuente | Revisión de modularidad y documentación |

Los resultados y las evidencias correspondientes se incorporarán en la sección de Pruebas y Validaciones.