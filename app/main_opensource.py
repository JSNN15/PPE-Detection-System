"""
PPE Detection System - Open Source Solution
Aplicación principal para detección de EPP usando YOLOv8

Características:
- Detección en tiempo real con múltiples cámaras IP
- Integración MQTT y Webhooks con Node-RED
- Exportación a CSV
- Dashboard en tiempo real
- 100% Open Source y Gratuito
"""

import os
import sys
import yaml
import logging
import argparse
import time
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import cv2

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.camera_stream import CameraStream
from src.core.mqtt_client import MQTTPublisher
from src.core.webhook_sender import WebhookSender
from src.core.csv_exporter import CSVExporter
from src.opensource_solution.yolo_detector import YOLODetector
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ppe_detection.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class PPEDetectionSystem:
    """
    Sistema principal de detección de EPP
    """

    def __init__(self, config_dir: Path):
        """
        Inicializa el sistema

        Args:
            config_dir: Directorio con archivos de configuración
        """
        self.config_dir = config_dir
        self.is_running = False

        # Cargar configuraciones
        logger.info("Cargando configuraciones...")
        self.ppe_config = self._load_config('ppe_config.yaml')
        self.camera_config = self._load_config('camera_config.yaml')

        # Cargar variables de entorno
        load_dotenv()

        # Inicializar componentes
        self.detector = None
        self.cameras: Dict[str, CameraStream] = {}
        self.mqtt_client = None
        self.webhook_sender = None
        self.csv_exporter = None

        logger.info("Sistema de detección de EPP inicializado")

    def _load_config(self, filename: str) -> dict:
        """Carga archivo de configuración YAML"""
        config_path = self.config_dir / filename
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def initialize_detector(self):
        """Inicializa el detector YOLO"""
        logger.info("Inicializando detector YOLO...")

        model_path = os.getenv('YOLO_MODEL_PATH', 'data/models/yolo_training/ppe_detector_v1/weights/best.pt')
        confidence = float(os.getenv('YOLO_CONFIDENCE_THRESHOLD', 0.7))
        iou = float(os.getenv('YOLO_IOU_THRESHOLD', 0.45))

        # Obtener nombres de clases desde configuración
        class_names = []
        for ppe in self.ppe_config['ppe_detection']['mandatory']:
            class_names.append(ppe['name'])
        for ppe in self.ppe_config['ppe_detection']['conditional']:
            class_names.append(ppe['name'])

        self.detector = YOLODetector(
            model_path=model_path,
            confidence_threshold=confidence,
            iou_threshold=iou,
            class_names=class_names
        )

        logger.info(f"✅ Detector inicializado: {self.detector}")

    def initialize_mqtt(self):
        """Inicializa cliente MQTT"""
        if not os.getenv('MQTT_ENABLED', 'false').lower() == 'true':
            logger.info("MQTT deshabilitado")
            return

        logger.info("Inicializando cliente MQTT...")

        self.mqtt_client = MQTTPublisher(
            broker_host=os.getenv('MQTT_BROKER_HOST', 'localhost'),
            broker_port=int(os.getenv('MQTT_BROKER_PORT', 1883)),
            username=os.getenv('MQTT_USERNAME'),
            password=os.getenv('MQTT_PASSWORD'),
            topic_prefix=os.getenv('MQTT_TOPIC_PREFIX', 'ppe_detection'),
            qos=int(os.getenv('MQTT_QOS', 1)),
        )

        if self.mqtt_client.connect():
            logger.info("✅ MQTT conectado")
        else:
            logger.warning("⚠️ No se pudo conectar a MQTT")

    def initialize_webhook(self):
        """Inicializa webhook sender"""
        if not os.getenv('WEBHOOK_ENABLED', 'false').lower() == 'true':
            logger.info("Webhook deshabilitado")
            return

        logger.info("Inicializando webhook sender...")

        self.webhook_sender = WebhookSender(
            webhook_url=os.getenv('WEBHOOK_URL'),
            method=os.getenv('WEBHOOK_METHOD', 'POST'),
            timeout=int(os.getenv('WEBHOOK_TIMEOUT_SECONDS', 10)),
            retry_attempts=int(os.getenv('WEBHOOK_RETRY_ATTEMPTS', 3)),
            auth_type=os.getenv('WEBHOOK_AUTH_TYPE', 'none'),
            username=os.getenv('WEBHOOK_USERNAME'),
            password=os.getenv('WEBHOOK_PASSWORD'),
            bearer_token=os.getenv('WEBHOOK_BEARER_TOKEN'),
            api_key=os.getenv('WEBHOOK_API_KEY'),
            api_key_header=os.getenv('WEBHOOK_API_KEY_HEADER', 'X-API-Key'),
        )

        if self.webhook_sender.test_connection():
            logger.info("✅ Webhook configurado")
        else:
            logger.warning("⚠️ Webhook no respondió al test")

    def initialize_csv_exporter(self):
        """Inicializa exportador CSV"""
        if not os.getenv('CSV_EXPORT_ENABLED', 'false').lower() == 'true':
            logger.info("Exportación CSV deshabilitada")
            return

        logger.info("Inicializando exportador CSV...")

        export_path = os.getenv('CSV_EXPORT_PATH', 'exports/')

        self.csv_exporter = CSVExporter(
            export_path=export_path,
            buffer_size=100,
            auto_flush_interval=60
        )

        logger.info(f"✅ CSV Exporter inicializado en: {export_path}")

    def initialize_cameras(self):
        """Inicializa streams de cámaras"""
        logger.info("Inicializando cámaras...")

        enabled_cameras = [cam for cam in self.camera_config['cameras'] if cam['enabled']]

        if not enabled_cameras:
            logger.warning("⚠️ No hay cámaras habilitadas en la configuración")
            return

        for camera_config in enabled_cameras:
            camera_id = camera_config['camera_id']

            try:
                camera_stream = CameraStream(
                    camera_config=camera_config,
                    buffer_size=1,
                    reconnect_attempts=camera_config.get('reconnect_attempts', 5),
                    reconnect_delay=camera_config.get('reconnect_delay_seconds', 10)
                )

                self.cameras[camera_id] = camera_stream
                logger.info(f"✅ Cámara {camera_id} configurada")

            except Exception as e:
                logger.error(f"❌ Error configurando cámara {camera_id}: {e}")

        logger.info(f"Total de cámaras configuradas: {len(self.cameras)}")

    def process_camera(self, camera_id: str, camera_stream: CameraStream):
        """
        Procesa frames de una cámara

        Args:
            camera_id: ID de la cámara
            camera_stream: Stream de la cámara
        """
        camera_config = next(
            (cam for cam in self.camera_config['cameras'] if cam['camera_id'] == camera_id),
            None
        )

        if not camera_config:
            logger.error(f"No se encontró configuración para {camera_id}")
            return

        zone = camera_config.get('zone', 'unknown')
        frame_count = 0
        last_heartbeat = time.time()

        while self.is_running:
            ret, frame = camera_stream.read()

            if not ret or frame is None:
                time.sleep(0.1)
                continue

            frame_count += 1

            # Procesar cada N frames (optimización)
            process_every_n = int(os.getenv('PROCESS_EVERY_N_FRAMES', 2))
            if frame_count % process_every_n != 0:
                continue

            # Detectar EPP
            results = self.detector.detect(frame, return_annotated=False)

            timestamp = datetime.now()
            detections = results['detections']

            # Si hay detecciones, procesarlas
            if len(detections) > 0:
                # Publicar a MQTT
                if self.mqtt_client and self.mqtt_client.is_connected:
                    self.mqtt_client.publish_detection(
                        camera_id=camera_id,
                        detections=detections,
                        frame_metadata={
                            'zone': zone,
                            'fps': results['fps'],
                            'inference_time': results['inference_time']
                        }
                    )

                # Enviar webhook
                if self.webhook_sender:
                    self.webhook_sender.send_detection(
                        camera_id=camera_id,
                        detections=detections,
                        frame_metadata={
                            'zone': zone,
                            'camera_name': camera_config['name']
                        }
                    )

                # Exportar a CSV
                if self.csv_exporter:
                    self.csv_exporter.add_detection(
                        camera_id=camera_id,
                        camera_name=camera_config['name'],
                        timestamp=timestamp,
                        detections=detections,
                        zone=zone
                    )

                # Verificar cumplimiento de EPP
                required_ppe = self._get_required_ppe(zone)
                compliance = self.detector.check_ppe_compliance(detections, required_ppe)

                if not compliance['is_compliant']:
                    # Generar alerta
                    self._generate_alert(
                        camera_id=camera_id,
                        camera_name=camera_config['name'],
                        zone=zone,
                        missing_ppe=compliance['missing_ppe']
                    )

            # Heartbeat cada 60 segundos
            if time.time() - last_heartbeat > 60:
                if self.mqtt_client and self.mqtt_client.is_connected:
                    self.mqtt_client.publish_status(
                        camera_id=camera_id,
                        status='online',
                        stats=camera_stream.get_stats()
                    )
                last_heartbeat = time.time()

    def _get_required_ppe(self, zone: str) -> List[str]:
        """
        Obtiene EPPs requeridos para una zona

        Args:
            zone: ID de la zona

        Returns:
            Lista de EPPs requeridos
        """
        zone_config = next(
            (z for z in self.ppe_config.get('zones', []) if z['zone_id'] == zone),
            None
        )

        if not zone_config:
            # Zona no configurada, usar EPPs obligatorios
            return [ppe['name'] for ppe in self.ppe_config['ppe_detection']['mandatory']]

        required = zone_config.get('mandatory_ppe', [])

        # Añadir condicionales si están habilitados
        for ppe in self.ppe_config['ppe_detection']['conditional']:
            if ppe['enabled'] and ppe['name'] in zone_config.get('conditional_ppe', []):
                required.append(ppe['name'])

        return required

    def _generate_alert(
        self,
        camera_id: str,
        camera_name: str,
        zone: str,
        missing_ppe: List[str]
    ):
        """
        Genera alerta cuando falta EPP

        Args:
            camera_id: ID de la cámara
            camera_name: Nombre de la cámara
            zone: Zona
            missing_ppe: EPPs faltantes
        """
        timestamp = datetime.now()
        message = f"EPP faltante detectado en {camera_name}: {', '.join(missing_ppe)}"

        logger.warning(f"🚨 ALERTA: {message}")

        # Publicar a MQTT
        if self.mqtt_client and self.mqtt_client.is_connected:
            self.mqtt_client.publish_alert(
                camera_id=camera_id,
                alert_type='missing_ppe',
                severity='high',
                message=message,
                details={'missing_ppe': missing_ppe, 'zone': zone}
            )

        # Enviar webhook
        if self.webhook_sender:
            self.webhook_sender.send_alert(
                camera_id=camera_id,
                alert_type='missing_ppe',
                severity='high',
                message=message,
                details={'missing_ppe': missing_ppe, 'zone': zone, 'camera_name': camera_name}
            )

        # Exportar a CSV
        if self.csv_exporter:
            self.csv_exporter.add_alert(
                camera_id=camera_id,
                camera_name=camera_name,
                timestamp=timestamp,
                alert_type='missing_ppe',
                severity='high',
                message=message,
                zone=zone
            )

    def start(self):
        """Inicia el sistema de detección"""
        logger.info("=" * 70)
        logger.info("INICIANDO SISTEMA DE DETECCIÓN DE EPP")
        logger.info("=" * 70)

        # Inicializar componentes
        self.initialize_detector()
        self.initialize_mqtt()
        self.initialize_webhook()
        self.initialize_csv_exporter()
        self.initialize_cameras()

        if not self.cameras:
            logger.error("No hay cámaras disponibles. Saliendo...")
            return

        # Iniciar streams de cámaras
        for camera_id, camera_stream in self.cameras.items():
            camera_stream.start()
            logger.info(f"📹 Stream iniciado: {camera_id}")

        self.is_running = True

        logger.info("=" * 70)
        logger.info("✅ SISTEMA ACTIVO - Detectando EPP en tiempo real")
        logger.info("=" * 70)

        # Loop principal
        import threading

        threads = []
        for camera_id, camera_stream in self.cameras.items():
            thread = threading.Thread(
                target=self.process_camera,
                args=(camera_id, camera_stream),
                daemon=True
            )
            thread.start()
            threads.append(thread)

        # Heartbeat del sistema
        try:
            while self.is_running:
                time.sleep(10)

                # Publicar estadísticas del sistema
                if self.mqtt_client and self.mqtt_client.is_connected:
                    system_stats = {
                        'active_cameras': len([c for c in self.cameras.values() if c.is_running]),
                        'total_cameras': len(self.cameras),
                        'detector_stats': self.detector.get_stats(),
                    }
                    self.mqtt_client.publish_heartbeat(system_stats)

        except KeyboardInterrupt:
            logger.info("\\n⏹️ Deteniendo sistema...")
            self.stop()

    def stop(self):
        """Detiene el sistema"""
        logger.info("Deteniendo sistema de detección...")

        self.is_running = False

        # Detener cámaras
        for camera_id, camera_stream in self.cameras.items():
            camera_stream.stop()
            logger.info(f"Cámara {camera_id} detenida")

        # Cerrar conexiones
        if self.mqtt_client:
            self.mqtt_client.disconnect()

        if self.webhook_sender:
            self.webhook_sender.close()

        if self.csv_exporter:
            self.csv_exporter.close()

        # Mostrar estadísticas finales
        logger.info("=" * 70)
        logger.info("ESTADÍSTICAS FINALES")
        logger.info("=" * 70)
        logger.info(f"Detector: {self.detector.get_stats()}")

        if self.mqtt_client:
            logger.info(f"MQTT: {self.mqtt_client.get_stats()}")

        if self.webhook_sender:
            logger.info(f"Webhook: {self.webhook_sender.get_stats()}")

        if self.csv_exporter:
            logger.info(f"CSV: {self.csv_exporter.get_stats()}")

        logger.info("=" * 70)
        logger.info("✅ Sistema detenido correctamente")


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Sistema de Detección de EPP - Solución Open Source"
    )
    parser.add_argument(
        '--config-dir',
        type=str,
        default='config',
        help='Directorio con archivos de configuración'
    )

    args = parser.parse_args()

    # Crear directorio de logs
    Path('logs').mkdir(exist_ok=True)

    # Crear sistema
    system = PPEDetectionSystem(config_dir=Path(args.config_dir))

    # Manejar señales
    def signal_handler(sig, frame):
        logger.info("\\nSeñal de interrupción recibida")
        system.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Iniciar sistema
    system.start()


if __name__ == "__main__":
    main()
