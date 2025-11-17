# Guía Rápida de Deployment - Solución Open Source

## 🚀 Deployment en 10 minutos

### Prerequisitos

- Python 3.10+
- (Opcional) Docker y Docker Compose

---

## Opción 1: Deployment Local (Sin Docker)

### Paso 1: Clonar e instalar

```bash
git clone https://github.com/JSNN15/Test-Gemini-Chat-Bot.git
cd Test-Gemini-Chat-Bot

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 2: Configurar

```bash
# Copiar plantilla de configuración
cp .env.example .env

# Editar .env con tus configuraciones
nano .env
```

Configuración mínima en `.env`:

```bash
# Modelo (usar pre-entrenado o entrenar el tuyo)
YOLO_MODEL_PATH=yolov8n.pt  # Modelo pequeño por defecto

# Desactivar integraciones para prueba rápida
MQTT_ENABLED=false
WEBHOOK_ENABLED=false
CSV_EXPORT_ENABLED=true
CSV_EXPORT_PATH=exports/
```

### Paso 3: Configurar cámaras

Editar `config/camera_config.yaml`:

```yaml
cameras:
  - camera_id: "cam_001"
    name: "Cámara de Prueba"
    enabled: true
    protocol: "rtsp"  # o "http"
    host: "192.168.1.100"  # IP de tu cámara
    port: 554
    path: "/stream1"
    username: "admin"
    password: "${CAM_001_PASSWORD}"
```

Y en `.env` añade:
```bash
CAM_001_PASSWORD=tu_password_aqui
```

### Paso 4: Ejecutar

```bash
# Crear directorios necesarios
mkdir -p logs exports data/models

# Ejecutar aplicación
python app/main_opensource.py
```

---

## Opción 2: Deployment con Docker

### Paso 1: Preparar configuraciones

```bash
# Clonar repositorio
git clone https://github.com/JSNN15/Test-Gemini-Chat-Bot.git
cd Test-Gemini-Chat-Bot

# Configurar .env
cp .env.example .env
nano .env

# Configurar cámaras
nano config/camera_config.yaml
```

### Paso 2: Build y Run

```bash
# Build imagen Docker
docker build -t ppe-detection:latest -f docker/Dockerfile.opensource .

# Run container
docker run -d \
  --name ppe-detection \
  --restart unless-stopped \
  --env-file .env \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/exports:/app/exports \
  -v $(pwd)/logs:/app/logs \
  -p 8501:8501 \
  ppe-detection:latest

# Ver logs
docker logs -f ppe-detection
```

---

## Opción 3: Docker Compose (Recomendado)

### Paso 1: Configurar

```bash
git clone https://github.com/JSNN15/Test-Gemini-Chat-Bot.git
cd Test-Gemini-Chat-Bot

cp .env.example .env
nano .env
nano config/camera_config.yaml
```

### Paso 2: Iniciar stack completo

```bash
# Iniciar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down
```

El stack incluye:
- PPE Detection Service
- MQTT Broker (Mosquitto)
- InfluxDB (time-series database)
- Grafana (dashboard)

**Accesos:**
- Grafana: http://localhost:3000 (admin/admin)
- MQTT: localhost:1883

---

## Testing Rápido

### 1. Test con imagen estática

```python
from ultralytics import YOLO

# Cargar modelo
model = YOLO('yolov8n.pt')

# Probar con imagen
results = model.predict('test_image.jpg', conf=0.5)

# Mostrar resultados
results[0].show()
```

### 2. Test con webcam

```bash
# Modificar config/camera_config.yaml
test_camera:
  enabled: true
  source: 0  # Webcam

# Ejecutar
python app/main_opensource.py
```

### 3. Test con cámara IP

```bash
# Verificar conexión a cámara
ffplay rtsp://user:pass@192.168.1.100:554/stream1

# Si funciona, configurar en camera_config.yaml y ejecutar
python app/main_opensource.py
```

---

## Integración con Node-RED

### Paso 1: Instalar Node-RED

```bash
# Docker
docker run -d --name nodered \
  -p 1880:1880 \
  nodered/node-red

# Acceder a: http://localhost:1880
```

### Paso 2: Configurar MQTT en Node-RED

1. Añadir nodo **mqtt in**
2. Configurar broker: `localhost:1883`
3. Topic: `ppe_detection/#`
4. Deploy

### Paso 3: Habilitar MQTT en PPE Detection

En `.env`:
```bash
MQTT_ENABLED=true
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
```

Reiniciar servicio:
```bash
# Local
Ctrl+C
python app/main_opensource.py

# Docker
docker restart ppe-detection
```

### Paso 4: Ver eventos en Node-RED

Añade nodo **debug** después del **mqtt in** y verás los eventos en tiempo real.

---

## Troubleshooting Común

### Error: "No module named 'ultralytics'"

```bash
pip install ultralytics
```

### Error: "Can't connect to camera"

1. Verificar IP y puerto:
```bash
ping 192.168.1.100
```

2. Probar URL con ffplay:
```bash
ffplay rtsp://user:pass@ip:port/path
```

3. Verificar firewall

### Error: "Model not found"

```bash
# Usar modelo pre-entrenado
YOLO_MODEL_PATH=yolov8n.pt  # en .env

# O entrenar el tuyo con notebooks/03_model_training_opensource.ipynb
```

### CPU muy lento

```bash
# Procesar menos frames
PROCESS_EVERY_N_FRAMES=5  # en .env

# Usar modelo más pequeño
YOLO_MODEL_PATH=yolov8n.pt
```

---

## Entrenamiento de Modelo Personalizado

### Opción Rápida: Google Colab (Gratis)

1. Abre: `notebooks/03_model_training_opensource.ipynb`
2. Click en "Open in Colab"
3. Sube tus imágenes anotadas
4. Ejecuta el notebook (2-8 horas)
5. Descarga `best.pt`
6. Coloca en `data/models/` y actualiza `.env`

### Datasets Públicos

Puedes empezar con datasets pre-anotados:

1. Busca en Roboflow Universe: https://universe.roboflow.com/search?q=ppe
2. Descarga en formato YOLOv8
3. Entrena con notebook 03

---

## Monitoreo y Logs

### Ver logs en tiempo real

```bash
# Local
tail -f logs/ppe_detection.log

# Docker
docker logs -f ppe-detection
```

### Revisar CSV exports

```bash
# Detecciones del día
cat exports/detections_$(date +%Y-%m-%d).csv

# Alertas
cat exports/alerts_$(date +%Y-%m-%d).csv
```

### Dashboard Grafana

Si usaste Docker Compose:

1. Accede a http://localhost:3000
2. Login: admin/admin
3. Añade data source: InfluxDB
4. Importa dashboard de PPE Detection

---

## Deployment en Producción

### Recomendaciones

1. **GPU**: Usa servidor con GPU NVIDIA para mejor performance
2. **Networking**: Coloca en VLAN con las cámaras IP
3. **Storage**: Monta volumen persistente para `data/` y `exports/`
4. **Backup**: Backup periódico de modelos y configuraciones
5. **Monitoring**: Usa Grafana para monitoreo 24/7
6. **Alertas**: Configura notificaciones en Node-RED

### Hardware Mínimo

- **CPU**: 4 cores
- **RAM**: 8 GB
- **Storage**: 50 GB SSD
- **Network**: 1 Gbps (para múltiples cámaras)

### Hardware Recomendado

- **CPU**: 8 cores
- **RAM**: 16 GB
- **GPU**: NVIDIA RTX 3060 o superior
- **Storage**: 500 GB NVMe SSD
- **Network**: 1 Gbps

---

## Soporte

¿Problemas? Contacta:

- GitHub Issues: https://github.com/JSNN15/Test-Gemini-Chat-Bot/issues
- Email: soporte@ppe-detection.com
- Docs: https://github.com/JSNN15/Test-Gemini-Chat-Bot/blob/main/README.md

---

**¡Listo para detectar EPP! 🎉**
