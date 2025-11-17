"""
MQTT Publisher para integración con Node-RED
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MQTTPublisher:
    """
    Cliente MQTT para publicar eventos de detección
    Integración profesional con Node-RED
    """

    def __init__(
        self,
        broker_host: str,
        broker_port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        topic_prefix: str = "ppe_detection",
        qos: int = 1,
        retain: bool = False,
        use_tls: bool = False,
        ca_cert: Optional[str] = None,
        client_cert: Optional[str] = None,
        client_key: Optional[str] = None,
    ):
        """
        Inicializa el publicador MQTT

        Args:
            broker_host: Host del broker MQTT
            broker_port: Puerto del broker
            username: Usuario MQTT (opcional)
            password: Contraseña MQTT (opcional)
            topic_prefix: Prefijo para todos los topics
            qos: Quality of Service (0, 1, 2)
            retain: Si retener mensajes
            use_tls: Si usar TLS/SSL
            ca_cert: Path al certificado CA
            client_cert: Path al certificado del cliente
            client_key: Path a la llave del cliente
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic_prefix = topic_prefix
        self.qos = qos
        self.retain = retain

        # Crear cliente MQTT
        self.client = mqtt.Client(client_id=f"ppe_detector_{datetime.now().timestamp()}")

        # Configurar credenciales
        if username and password:
            self.client.username_pw_set(username, password)

        # Configurar TLS
        if use_tls:
            if ca_cert:
                self.client.tls_set(
                    ca_certs=ca_cert,
                    certfile=client_cert,
                    keyfile=client_key
                )
            else:
                self.client.tls_set()

        # Callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish

        self.is_connected = False
        self.published_count = 0

        logger.info(f"MQTT Publisher inicializado para {broker_host}:{broker_port}")

    def _on_connect(self, client, userdata, flags, rc):
        """Callback cuando se conecta al broker"""
        if rc == 0:
            self.is_connected = True
            logger.info(f"✅ Conectado al broker MQTT: {self.broker_host}:{self.broker_port}")
        else:
            self.is_connected = False
            logger.error(f"❌ Error conectando a MQTT broker: código {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback cuando se desconecta del broker"""
        self.is_connected = False
        if rc != 0:
            logger.warning(f"Desconectado inesperadamente del broker MQTT (código {rc})")
        else:
            logger.info("Desconectado del broker MQTT")

    def _on_publish(self, client, userdata, mid):
        """Callback cuando se publica un mensaje"""
        self.published_count += 1

    def connect(self, timeout: int = 10) -> bool:
        """
        Conecta al broker MQTT

        Args:
            timeout: Timeout en segundos

        Returns:
            True si conexión exitosa
        """
        try:
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            self.client.loop_start()

            # Esperar conexión
            import time
            start_time = time.time()
            while not self.is_connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)

            return self.is_connected

        except Exception as e:
            logger.error(f"Error conectando a broker MQTT: {e}")
            return False

    def disconnect(self):
        """Desconecta del broker MQTT"""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Desconectado de broker MQTT")

    def publish_detection(
        self,
        camera_id: str,
        detections: list,
        frame_metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Publica evento de detección

        Args:
            camera_id: ID de la cámara
            detections: Lista de detecciones
            frame_metadata: Metadatos adicionales del frame
        """
        if not self.is_connected:
            logger.warning("No conectado a broker MQTT, saltando publicación")
            return

        # Construir payload
        payload = {
            "timestamp": datetime.now().isoformat(),
            "camera_id": camera_id,
            "num_detections": len(detections),
            "detections": detections,
        }

        if frame_metadata:
            payload["metadata"] = frame_metadata

        # Topic específico: ppe_detection/camera_id/detections
        topic = f"{self.topic_prefix}/{camera_id}/detections"

        try:
            result = self.client.publish(
                topic,
                json.dumps(payload),
                qos=self.qos,
                retain=self.retain
            )

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Publicado a {topic}: {len(detections)} detecciones")
            else:
                logger.warning(f"Error publicando a {topic}: código {result.rc}")

        except Exception as e:
            logger.error(f"Excepción publicando a MQTT: {e}")

    def publish_alert(
        self,
        camera_id: str,
        alert_type: str,
        severity: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Publica alerta de seguridad

        Args:
            camera_id: ID de la cámara
            alert_type: Tipo de alerta (ej: 'missing_ppe', 'unauthorized_access')
            severity: Severidad ('low', 'medium', 'high', 'critical')
            message: Mensaje de la alerta
            details: Detalles adicionales
        """
        if not self.is_connected:
            logger.warning("No conectado a broker MQTT, saltando alerta")
            return

        payload = {
            "timestamp": datetime.now().isoformat(),
            "camera_id": camera_id,
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
        }

        if details:
            payload["details"] = details

        # Topic de alertas: ppe_detection/alerts/severity
        topic = f"{self.topic_prefix}/alerts/{severity}"

        try:
            result = self.client.publish(
                topic,
                json.dumps(payload),
                qos=2,  # Máxima QoS para alertas
                retain=True  # Retener últimas alertas
            )

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"🚨 Alerta publicada: {alert_type} ({severity})")
            else:
                logger.warning(f"Error publicando alerta: código {result.rc}")

        except Exception as e:
            logger.error(f"Excepción publicando alerta: {e}")

    def publish_status(
        self,
        camera_id: str,
        status: str,
        stats: Optional[Dict[str, Any]] = None
    ):
        """
        Publica estado de cámara/sistema

        Args:
            camera_id: ID de la cámara
            status: Estado ('online', 'offline', 'error')
            stats: Estadísticas adicionales
        """
        if not self.is_connected:
            return

        payload = {
            "timestamp": datetime.now().isoformat(),
            "camera_id": camera_id,
            "status": status,
        }

        if stats:
            payload["stats"] = stats

        topic = f"{self.topic_prefix}/{camera_id}/status"

        try:
            self.client.publish(topic, json.dumps(payload), qos=1, retain=True)
            logger.debug(f"Estado publicado: {camera_id} -> {status}")
        except Exception as e:
            logger.error(f"Error publicando estado: {e}")

    def publish_heartbeat(self, system_stats: Optional[Dict[str, Any]] = None):
        """
        Publica heartbeat del sistema

        Args:
            system_stats: Estadísticas del sistema
        """
        if not self.is_connected:
            return

        payload = {
            "timestamp": datetime.now().isoformat(),
            "status": "alive",
            "published_messages": self.published_count,
        }

        if system_stats:
            payload["stats"] = system_stats

        topic = f"{self.topic_prefix}/system/heartbeat"

        try:
            self.client.publish(topic, json.dumps(payload), qos=0, retain=False)
        except Exception as e:
            logger.error(f"Error publicando heartbeat: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del publisher"""
        return {
            "is_connected": self.is_connected,
            "broker": f"{self.broker_host}:{self.broker_port}",
            "published_count": self.published_count,
            "topic_prefix": self.topic_prefix,
        }

    def __enter__(self):
        """Context manager support"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support"""
        self.disconnect()
