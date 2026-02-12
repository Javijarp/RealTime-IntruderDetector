# Implementación de Semáforos - Sistema de Reconocimiento Facial

## Objetivo

Sincronizar y controlar la concurrencia entre el **Edge Module (Python)** y el **Backend (Spring Boot)** usando semáforos.

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                        EDGE MODULE (Python)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Thread 1: CAPTURE                                              │
│  ├─ Semáforo 1: Frame Buffer (5 slots)                         │
│  └─ Captura frames a 30 FPS → Queue                            │
│                           ↓                                      │
│  Thread 2: PROCESSING                                           │
│  ├─ Semáforo 1: Consume frame → libera slot                    │
│  ├─ Semáforo 2: YOLO Inference (2 simultáneos)                 │
│  └─ Genera eventos → Queue                                      │
│                           ↓                                      │
│  Thread 3: TRANSMISSION                                         │
│  ├─ Semáforo 3: HTTP Requests (3 simultáneos)                  │
│  └─ POST /api/events → Backend                                 │
│                           ↓                                      │
│  Thread 4: STREAMING                                            │
│  └─ Semáforo 4: Video Stream (1 activo)                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP POST
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     BACKEND (Spring Boot)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  EventProcessingService                                         │
│  ├─ Semáforo 1: Event Processing (5 simultáneos)               │
│  ├─ Semáforo 2: Database Writes (3 simultáneas)                │
│  ├─ Semáforo 3: WebSocket Notify (10 simultáneas)              │
│  └─ Semáforo 4: Image Processing (2 simultáneos)               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Semáforos Implementados

### Python Edge Module

| #   | Nombre                         | Capacidad | Propósito                              | Bloqueo      |
| --- | ------------------------------ | --------- | -------------------------------------- | ------------ |
| 1   | `_frame_buffer_semaphore`      | 5         | Controlar buffer de frames capturados  | Non-blocking |
| 2   | `_yolo_processing_semaphore`   | 2         | Limitar procesamiento YOLO concurrente | Blocking     |
| 3   | `_http_transmission_semaphore` | 3         | Limitar requests HTTP simultáneos      | Timeout 5s   |
| 4   | `_video_streaming_semaphore`   | 1         | Garantizar un solo stream activo       | Non-blocking |

### Java Backend

| #   | Nombre                           | Capacidad | Propósito                         | Bloqueo      |
| --- | -------------------------------- | --------- | --------------------------------- | ------------ |
| 1   | `eventProcessingSemaphore`       | 5         | Limitar procesamiento de eventos  | Timeout 5s   |
| 2   | `databaseWriteSemaphore`         | 3         | Controlar escrituras a BD         | Blocking     |
| 3   | `websocketNotificationSemaphore` | 10        | Limitar notificaciones WebSocket  | Non-blocking |
| 4   | `imageProcessingSemaphore`       | 2         | Limitar procesamiento de imágenes | Timeout 3s   |

---

## Flujo de Sincronización

### 1. Captura de Frame (Thread 1)

```python
if frame_buffer_semaphore.acquire(blocking=False):  # Non-blocking
    try:
        frame_queue.put(frame)                      # Agregar a cola
    except queue.Full:
        frame_buffer_semaphore.release()           # Liberar si falla
```

### 2. Procesamiento YOLO (Thread 2)

```python
frame = frame_queue.get()                          # Sacar frame
frame_buffer_semaphore.release()                  # ✓ Liberar slot buffer

yolo_processing_semaphore.acquire()               # Bloquear hasta disponible
try:
    detections = run_yolo(frame)                  # Inferencia YOLO
finally:
    yolo_processing_semaphore.release()           # ✓ Siempre liberar
```

### 3. Transmisión HTTP (Thread 3)

```python
if http_transmission_semaphore.acquire(timeout=5.0):  # Timeout 5s
    try:
        http_post(backend_url, event)             # Enviar al backend
    finally:
        http_transmission_semaphore.release()     # ✓ Siempre liberar
else:
    buffer.add(event)                             # Timeout → buffer local
```

### 4. Procesamiento en Backend (Java)

```java
if (eventProcessingSemaphore.tryAcquire(5, TimeUnit.SECONDS)) {
    try {
        processEvent(event);                      // Procesar evento
    } finally {
        eventProcessingSemaphore.release();       // ✓ Siempre liberar
    }
} else {
    throw new ServiceUnavailableException();      // Sistema sobrecargado
}
```

---

## Ventajas de la Implementación

✅ **Control de Recursos**: Previene sobrecarga del sistema  
✅ **Backpressure**: Descarta frames/eventos cuando está saturado  
✅ **Predictibilidad**: Límites claros de concurrencia  
✅ **Graceful Degradation**: Buffers locales para retries  
✅ **Logging Detallado**: Trazabilidad completa  
✅ **Estadísticas en Tiempo Real**: Monitoreo de semáforos

---

## Pruebas y Validación

### 1. Prueba de Saturación (Python)

```bash
# Ejecutar con logging extendido
cd edge-module
python -m src.main --log-level DEBUG

# Observar:
# - Frames descartados por semáforo lleno
# - Tiempos de espera en semáforos
# - Tasa de eventos enviados vs buffered
```

### 2. Prueba de Carga (Backend)

```bash
# Simular 100 requests concurrentes
ab -n 1000 -c 100 -p event.json -T application/json \
   http://localhost:8080/api/events

# Monitorear estadísticas
curl http://localhost:8080/api/events/stats
```

### 3. Monitoreo de Estadísticas

```bash
# Python: Ver logs en tiempo real
tail -f edge-module/logs/system.log | grep "Semáforo"

# Java: Endpoint de métricas
watch -n 1 'curl -s http://localhost:8080/api/events/stats | jq .'
```

---

## Métricas Clave

### Python Edge Module

- **Frames Captured**: Total de frames capturados
- **Frames Dropped**: Frames descartados por semáforo lleno
- **Semaphore Waits**: Veces que un thread esperó por semáforo
- **Semaphore Timeouts**: Veces que se excedió el timeout
- **Events Buffered**: Eventos guardados para retry

### Java Backend

- **Events Received**: Total de eventos recibidos
- **Events Processed**: Eventos procesados exitosamente
- **Events Rejected**: Eventos rechazados (HTTP 503)
- **Semaphore Timeouts**: Timeouts esperando semáforos
- **Available Slots**: Slots disponibles por semáforo

---

## Ejecución del Sistema

### 1. Iniciar Backend

```bash
cd backend/security-backend
./gradlew bootRun
```

### 2. Iniciar Edge Module

```bash
cd edge-module
python -m src.main
```

### 3. Monitorear Sistema

```bash
# Terminal 1: Logs del Edge Module
tail -f edge-module/logs/system.log

# Terminal 2: Logs del Backend
tail -f backend/security-backend/logs/application.log

# Terminal 3: Estadísticas en tiempo real
watch -n 2 'curl -s http://localhost:8080/api/events/stats | jq .'
```

---

## Video Explicativo

### Estructura (8 minutos)

**0:00-1:00**: Introducción

- ¿Qué es un semáforo?
- ¿Por qué necesitamos sincronización?

**1:00-3:00**: Implementación en Python

- Mostrar código de los 4 semáforos
- Explicar flujo de captura → procesamiento → transmisión
- Demostrar logs en vivo

**3:00-5:00**: Implementación en Java

- Mostrar código del backend
- Explicar control de concurrencia
- Demostrar endpoint de estadísticas

**5:00-7:00**: Prueba de Carga

- Ejecutar sistema completo
- Generar carga con Apache Bench
- Mostrar cómo se comportan los semáforos

**7:00-8:00**: Conclusión

- Beneficios de usar semáforos
- Aprendizajes del proyecto
- Próximos pasos

---

## Conclusión

Esta implementación demuestra el uso de **semáforos para sincronización distribuida** entre:

- Múltiples threads en Python (Producer-Consumer pattern)
- Control de concurrencia en Spring Boot
- Comunicación HTTP con backpressure
- Monitoreo y observabilidad en tiempo real

**Resultado**: Sistema robusto, predecible y con manejo elegante de sobrecarga.
