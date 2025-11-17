# Sistema de Detección de EPP para Planta de Lixiviación Química

## Resumen del Proyecto

Sistema de visión artificial para reconocimiento automático de Equipos de Protección Personal (EPP) en plantas de lixiviación química, con dos soluciones paralelas: Azure Cloud y Open Source.

## EPPs a Detectar

### Obligatorios (Siempre Activos)
- ✓ Gafas/lentes de seguridad
- ✓ Traje/overol químico VERDE o Cotona BLANCA/AZUL
- ✓ Zapatos de seguridad

### Condicionales (Activables según zona/tarea)
- ⚡ Mascarilla/respirador químico
- ⚡ Guantes resistentes a químicos

## Arquitectura de Soluciones

### Solución 1: Azure Cloud (Corporativa)
**Objetivo**: Privacidad empresarial, datos dentro del tenant de Azure

**Servicios Azure**:
- **Azure Custom Vision** o **Azure ML**: Entrenamiento de modelos
- **Azure Container Instances**: Hosting de aplicación de detección
- **Azure Blob Storage**: Almacenamiento de imágenes/logs
- **Azure Event Hub**: Stream de eventos de detección
- **Azure IoT Hub** (opcional): Gestión de cámaras
- **Power BI Embedded**: Dashboard en tiempo real

**Costo estimado mensual**: $50-150 USD (uso modesto)

### Solución 2: Open Source (Gratuita)
**Objetivo**: Máxima economía, sin costos privativos

**Stack Tecnológico**:
- **YOLOv8/v9**: Detección de objetos (state-of-the-art, gratis)
- **Roboflow**: Anotación y entrenamiento (tier gratuito)
- **Docker**: Containerización
- **InfluxDB**: Time-series database (open source)
- **Grafana**: Dashboard en tiempo real (open source)
- **Mosquitto**: MQTT broker (open source)
- **FastAPI**: API REST
- **OpenCV**: Procesamiento de video

**Costo**: $0 (solo infraestructura básica: VPS ~$5-10/mes)

## Integraciones

### Node-RED
- **MQTT**: Publicación de eventos de detección
- **Webhook**: HTTP POST con JSON de detecciones
- **Formato estándar**: ISO 8601 timestamps, JSON estructurado

### Exportaciones
- **CSV**: Logs diarios de cumplimiento
- **Dashboard**: Visualización en tiempo real
- **Alertas**: Notificaciones cuando EPP falta

## Estructura del Proyecto

```
ppe-detection-system/
├── notebooks/              # Experimentación y entrenamiento
├── src/                   # Código fuente
│   ├── azure_solution/    # Implementación Azure
│   ├── opensource_solution/ # Implementación Open Source
│   └── core/              # Código compartido
├── app/                   # Aplicaciones principales
├── config/                # Configuraciones
├── deployment/            # Scripts de deployment
└── tests/                 # Pruebas
```

## Fases de Desarrollo

### Fase 1: Experimentación (Notebooks)
1. Preparación de dataset de EPP
2. Entrenamiento de modelos (Azure Custom Vision + YOLOv8)
3. Evaluación y comparación de precisión
4. Pruebas de inferencia

### Fase 2: Desarrollo de Aplicación
1. Conexión a cámaras RTSP/HTTP
2. Pipeline de detección en tiempo real
3. Integración MQTT/Webhooks
4. Exportación CSV
5. Dashboard

### Fase 3: Deployment
1. Containerización (Docker)
2. Deployment Azure (Container Instances)
3. Deployment Open Source (VPS/On-premise)
4. Configuración de Node-RED

## Requerimientos Técnicos

### Cámaras
- **Protocolo recomendado**: RTSP (estándar industrial)
- **Fallback**: HTTP/MJPEG
- **Resolución mínima**: 720p (1280x720)
- **FPS**: 5-15 fps suficiente para detección

### Precisión Esperada
- **mAP (mean Average Precision)**: >85%
- **Recall**: >90% (detectar cuando EPP falta es crítico)
- **Latencia**: 1-3 segundos aceptable

## Ventajas de Cada Solución

### Azure
- ✅ Privacidad total (datos en tenant corporativo)
- ✅ Soporte empresarial Microsoft
- ✅ Escalabilidad automática
- ✅ Integración con ecosistema Microsoft
- ❌ Costo mensual recurrente

### Open Source
- ✅ Costo $0 en software
- ✅ Control total del código
- ✅ Misma precisión que Azure
- ✅ Portabilidad (on-premise o cloud)
- ❌ Requiere más conocimiento técnico para mantener

## Próximos Pasos

1. Crear estructura de carpetas del proyecto
2. Desarrollar notebooks de experimentación
3. Implementar código de detección
4. Configurar integraciones
5. Documentar deployment

---

**Autor**: Sistema de IA Claude
**Fecha**: 2025-11-17
**Versión**: 1.0
