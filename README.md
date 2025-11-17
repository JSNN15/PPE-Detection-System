# PPE Detection System 🏭🔬

## Sistema de Detección de EPP para Planta Química

**Sistema profesional de visión artificial para reconocimiento automático de Equipos de Protección Personal (EPP) en plantas de lixiviación química.**

## 🌟 Características Principales

### Detección Inteligente
- ✅ **Gafas/lentes de seguridad** (obligatorio)
- ✅ **Zapatos de seguridad** (obligatorio)
- ✅ **Traje/overol verde o cotona blanca/azul** (obligatorio)
- ⚡ **Mascarilla/respirador químico** (activable)
- ⚡ **Guantes resistentes a químicos** (activable)

### Integraciones Profesionales
- 📹 **Múltiples cámaras IP** (RTSP/HTTP)
- 📊 **Dashboard en tiempo real**
- 📁 **Exportación CSV** para auditorías
- 🔗 **MQTT & Webhooks** para Node-RED
- 🚨 **Alertas automáticas** cuando falta EPP

### Dos Soluciones Paralelas

#### 1. Solución Azure (Cloud Corporativo)
- 🔒 Privacidad total (datos en tenant empresarial)
- ☁️ Azure Custom Vision + Azure ML
- 📈 Escalabilidad automática
- 💰 Costo modesto: ~$50-150/mes

#### 2. Solución Open Source (100% Gratuita)
- 🆓 **Costo $0 en software**
- 🚀 YOLOv8 (state-of-the-art)
- 🐳 Docker + FastAPI + Grafana
- 🏠 On-premise o cloud

---

## 🚀 Inicio Rápido

### Prerrequisitos
```bash
Python 3.10+
pip o pip3
```

### Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/JSNN15/PPE-Detection-System.git
cd PPE-Detection-System
```

2. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus credenciales
```

4. **Configurar cámaras**
```bash
# Editar config/camera_config.yaml con tus cámaras IP
```

5. **Ejecutar aplicación**
```bash
# Solución Open Source
python app/main_opensource.py

# O con Docker
docker-compose up
```

---

## 📚 Documentación Completa

### 📓 Notebooks de Experimentación

El proyecto incluye Jupyter Notebooks interactivos para aprendizaje:

1. **[01_data_preparation.ipynb](notebooks/01_data_preparation.ipynb)**
   - Preparación de dataset de EPP
   - Anotación de imágenes
   - Data augmentation

2. **[03_model_training_opensource.ipynb](notebooks/03_model_training_opensource.ipynb)**
   - Entrenamiento de YOLOv8
   - Evaluación de métricas
   - Exportación de modelos

3. **[05_testing_inference.ipynb](notebooks/05_testing_inference.ipynb)**
   - Testing con cámaras IP
   - Benchmarks de velocidad
   - Análisis de performance

### 🗂️ Estructura del Proyecto

```
PPE-Detection-System/
├── config/                     # Configuraciones
│   ├── ppe_config.yaml        # EPPs a detectar
│   └── camera_config.yaml     # Cámaras IP
├── notebooks/                  # Jupyter Notebooks
│   ├── 01_data_preparation.ipynb
│   ├── 03_model_training_opensource.ipynb
│   └── 05_testing_inference.ipynb
├── src/                       # Código fuente
│   ├── core/                  # Módulos compartidos
│   │   ├── camera_stream.py   # Manejo de cámaras IP
│   │   ├── mqtt_client.py     # Cliente MQTT
│   │   ├── webhook_sender.py  # Webhooks
│   │   └── csv_exporter.py    # Exportación CSV
│   ├── opensource_solution/   # Solución YOLOv8
│   │   └── yolo_detector.py
│   └── azure_solution/        # Solución Azure (WIP)
├── app/                       # Aplicaciones principales
│   └── main_opensource.py     # App de producción
├── data/                      # Datasets y modelos
│   ├── raw/
│   ├── processed/
│   └── models/
├── deployment/                # Scripts de deployment
├── docker/                    # Dockerfiles
├── .env.example              # Plantilla de configuración
├── requirements.txt          # Dependencias Python
└── README.md                 # Este archivo
```

---

## ⚙️ Configuración

### 1. Equipos de Protección Personal (EPP)

Edita `config/ppe_config.yaml` para configurar qué EPPs detectar:

```yaml
ppe_detection:
  mandatory:
    - name: "safety_glasses"
      enabled: true
    - name: "safety_shoes"
      enabled: true
    - name: "protective_clothing"
      enabled: true

  conditional:
    - name: "chemical_mask"
      enabled: false  # Activar según zona
    - name: "chemical_gloves"
      enabled: false
```

### 2. Cámaras IP

Edita `config/camera_config.yaml`:

```yaml
cameras:
  - camera_id: "cam_001"
    name: "Zona Lixiviación - Entrada"
    enabled: true
    protocol: "rtsp"  # o "http"
    host: "192.168.1.100"
    port: 554
    path: "/stream1"
    username: "admin"
    password: "${CAM_001_PASSWORD}"  # En .env
```

### 3. Variables de Entorno

Edita `.env`:

```bash
# Modelo YOLO
YOLO_MODEL_PATH=data/models/yolo_training/ppe_detector_v1/weights/best.pt
YOLO_CONFIDENCE_THRESHOLD=0.7

# MQTT (Node-RED)
MQTT_ENABLED=true
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=ppe_detector
MQTT_PASSWORD=your_password

# Webhook (Node-RED)
WEBHOOK_ENABLED=true
WEBHOOK_URL=http://your-nodered:1880/ppe-webhook

# CSV Export
CSV_EXPORT_ENABLED=true
CSV_EXPORT_PATH=exports/
```

---

## 🔧 Entrenamiento de Modelo Personalizado

### Opción 1: Google Colab (Gratis con GPU)

1. Abre el notebook en Colab:
   - `notebooks/03_model_training_opensource.ipynb`

2. Sube tus imágenes anotadas

3. Ejecuta el entrenamiento (2-8 horas con GPU T4 gratis)

4. Descarga el modelo entrenado

### Opción 2: Local

```bash
# Abrir Jupyter
jupyter notebook notebooks/03_model_training_opensource.ipynb

# Seguir las instrucciones del notebook
```

### Herramientas de Anotación Recomendadas

- **[Roboflow](https://roboflow.com)** (Cloud, gratis hasta 10K imágenes)
- **[LabelImg](https://github.com/heartexlabs/labelImg)** (Local, open source)
- **[CVAT](https://cvat.org)** (Cloud/Local, open source)

---

## 📡 Integración con Node-RED

### MQTT Topics

El sistema publica a los siguientes topics:

```
ppe_detection/{camera_id}/detections    # Detecciones
ppe_detection/alerts/{severity}         # Alertas
ppe_detection/{camera_id}/status        # Estado de cámara
ppe_detection/system/heartbeat          # Heartbeat del sistema
```

### Formato de Mensajes

**Detección:**
```json
{
  "timestamp": "2025-01-17T10:30:45",
  "camera_id": "cam_001",
  "num_detections": 3,
  "detections": [
    {
      "class": "safety_glasses",
      "confidence": 0.95,
      "bbox": [100, 150, 200, 250]
    }
  ],
  "metadata": {
    "zone": "zona_lixiviacion",
    "fps": 25.3
  }
}
```

**Alerta:**
```json
{
  "timestamp": "2025-01-17T10:31:00",
  "camera_id": "cam_001",
  "alert_type": "missing_ppe",
  "severity": "high",
  "message": "EPP faltante: safety_glasses, chemical_mask",
  "details": {
    "missing_ppe": ["safety_glasses", "chemical_mask"],
    "zone": "zona_lixiviacion"
  }
}
```

### Webhook

También puedes recibir eventos vía HTTP POST:

```bash
POST http://your-nodered:1880/ppe-webhook
Content-Type: application/json

{
  "event_type": "detection",
  "timestamp": "2025-01-17T10:30:45",
  "camera_id": "cam_001",
  ...
}
```

---

## 📊 Exportación CSV

El sistema genera archivos CSV diarios:

**Detecciones** (`exports/detections_2025-01-17.csv`):
```csv
timestamp,date,time,camera_id,camera_name,zone,object_class,confidence,bbox_x1,bbox_y1,bbox_x2,bbox_y2
2025-01-17T10:30:45,2025-01-17,10:30:45,cam_001,Zona Lixiviación,zona_lixiviacion,safety_glasses,0.950,100,150,200,250
```

**Alertas** (`exports/alerts_2025-01-17.csv`):
```csv
timestamp,date,time,camera_id,camera_name,zone,alert_type,severity,message
2025-01-17T10:31:00,2025-01-17,10:31:00,cam_001,Zona Lixiviación,zona_lixiviacion,missing_ppe,high,EPP faltante: safety_glasses
```

---

## 🐳 Deployment con Docker

### Build

```bash
docker build -t ppe-detection:latest -f docker/Dockerfile.opensource .
```

### Run

```bash
docker run -d \
  --name ppe-detection \
  --env-file .env \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/exports:/app/exports \
  -p 8501:8501 \
  ppe-detection:latest
```

### Docker Compose

```bash
docker-compose up -d
```

---

## 🎯 Métricas y Performance

### Precisión Esperada
- **mAP50**: > 85% (excelente)
- **Recall**: > 90% (crítico para seguridad)
- **Precision**: > 80% (reducir falsas alarmas)

### Velocidad
- **CPU**: 5-10 FPS (suficiente para monitoreo)
- **GPU**: 30-60 FPS (tiempo real completo)
- **Latencia**: 100-200ms por frame

### Recursos
- **RAM**: 2-4 GB
- **GPU**: Opcional pero recomendada (NVIDIA con CUDA)
- **Disco**: 5-10 GB (modelo + logs)

---

## 🔐 Privacidad y Seguridad

### Solución Open Source
- ✅ Datos procesados localmente (on-premise)
- ✅ Sin envío a servicios cloud externos
- ✅ Control total de imágenes y logs
- ✅ Cumplimiento GDPR/CCPA ready

### Solución Azure
- ✅ Datos dentro del tenant corporativo
- ✅ Compliance con ISO 27001, SOC 2
- ✅ Cifrado en tránsito y reposo
- ✅ Auditoría completa

---

## 🛠️ Troubleshooting

### Cámara no conecta

1. Verifica que la cámara esté accesible:
```bash
ping 192.168.1.100
```

2. Prueba la URL con VLC o ffplay:
```bash
ffplay rtsp://user:pass@192.168.1.100:554/stream1
```

3. Verifica protocolo y path (consulta manual del fabricante)

### Modelo no carga

1. Verifica que el modelo existe:
```bash
ls -lh data/models/yolo_training/ppe_detector_v1/weights/best.pt
```

2. Entrena un modelo siguiendo el notebook 03

### Baja precisión

1. Añade más imágenes al dataset (objetivo: 1000+)
2. Mejora la calidad de anotaciones
3. Aumenta épocas de entrenamiento (200-300)
4. Usa modelo más grande (YOLOv8m o YOLOv8l)

---

## 📈 Roadmap

- [x] Sistema de detección con YOLOv8
- [x] Integración MQTT/Webhooks
- [x] Exportación CSV
- [x] Múltiples cámaras IP
- [ ] Dashboard Grafana en tiempo real
- [ ] Solución Azure completa
- [ ] App móvil para alertas
- [ ] Reconocimiento facial (opcional)
- [ ] Detección de zonas restringidas

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para más detalles.

---

## 📞 Soporte

Para preguntas o problemas:

- 📧 Email: soporte@ppe-detection.com
- 💬 Issues: [GitHub Issues](https://github.com/JSNN15/PPE-Detection-System/issues)
- 📚 Docs: [Documentación completa](./PROJECT_PLAN.md)

---

## 🙏 Agradecimientos

- **Ultralytics** por YOLOv8
- **Roboflow** por herramientas de dataset
- **OpenCV** por procesamiento de video
- **MQTT/Paho** por integración IoT

---

## 📊 Estadísticas del Proyecto

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)

---

**Desarrollado con ❤️ para mejorar la seguridad industrial**

**Versión**: 1.0.0
**Última actualización**: 2025-01-17
