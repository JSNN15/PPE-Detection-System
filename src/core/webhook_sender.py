"""
Webhook Sender para integración con Node-RED y otros sistemas
"""

import json
import logging
import requests
from typing import Optional, Dict, Any
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class WebhookSender:
    """
    Cliente para enviar eventos vía webhook HTTP
    Integración profesional con Node-RED y otros sistemas
    """

    def __init__(
        self,
        webhook_url: str,
        method: str = "POST",
        timeout: int = 10,
        retry_attempts: int = 3,
        auth_type: str = "none",
        username: Optional[str] = None,
        password: Optional[str] = None,
        bearer_token: Optional[str] = None,
        api_key: Optional[str] = None,
        api_key_header: str = "X-API-Key",
        custom_headers: Optional[Dict[str, str]] = None,
    ):
        """
        Inicializa el webhook sender

        Args:
            webhook_url: URL del webhook
            method: Método HTTP (POST, PUT)
            timeout: Timeout en segundos
            retry_attempts: Intentos de reintento
            auth_type: Tipo de autenticación ('none', 'basic', 'bearer', 'api_key')
            username: Usuario para basic auth
            password: Contraseña para basic auth
            bearer_token: Token para bearer auth
            api_key: API key
            api_key_header: Nombre del header para API key
            custom_headers: Headers adicionales
        """
        self.webhook_url = webhook_url
        self.method = method.upper()
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.auth_type = auth_type

        # Configurar sesión con retries
        self.session = requests.Session()

        retry_strategy = Retry(
            total=retry_attempts,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "PUT"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Configurar headers
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "PPE-Detection-System/1.0"
        }

        if custom_headers:
            self.headers.update(custom_headers)

        # Configurar autenticación
        if auth_type == "basic" and username and password:
            from requests.auth import HTTPBasicAuth
            self.session.auth = HTTPBasicAuth(username, password)

        elif auth_type == "bearer" and bearer_token:
            self.headers["Authorization"] = f"Bearer {bearer_token}"

        elif auth_type == "api_key" and api_key:
            self.headers[api_key_header] = api_key

        self.sent_count = 0
        self.error_count = 0

        logger.info(f"Webhook Sender inicializado para {webhook_url}")

    def send_detection(
        self,
        camera_id: str,
        detections: list,
        frame_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Envía evento de detección

        Args:
            camera_id: ID de la cámara
            detections: Lista de detecciones
            frame_metadata: Metadatos adicionales

        Returns:
            True si envío exitoso
        """
        payload = {
            "event_type": "detection",
            "timestamp": datetime.now().isoformat(),
            "camera_id": camera_id,
            "num_detections": len(detections),
            "detections": detections,
        }

        if frame_metadata:
            payload["metadata"] = frame_metadata

        return self._send_payload(payload)

    def send_alert(
        self,
        camera_id: str,
        alert_type: str,
        severity: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Envía alerta de seguridad

        Args:
            camera_id: ID de la cámara
            alert_type: Tipo de alerta
            severity: Severidad
            message: Mensaje
            details: Detalles adicionales

        Returns:
            True si envío exitoso
        """
        payload = {
            "event_type": "alert",
            "timestamp": datetime.now().isoformat(),
            "camera_id": camera_id,
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
        }

        if details:
            payload["details"] = details

        return self._send_payload(payload)

    def send_status(
        self,
        camera_id: str,
        status: str,
        stats: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Envía estado de cámara/sistema

        Args:
            camera_id: ID de la cámara
            status: Estado
            stats: Estadísticas

        Returns:
            True si envío exitoso
        """
        payload = {
            "event_type": "status",
            "timestamp": datetime.now().isoformat(),
            "camera_id": camera_id,
            "status": status,
        }

        if stats:
            payload["stats"] = stats

        return self._send_payload(payload)

    def _send_payload(self, payload: Dict[str, Any]) -> bool:
        """
        Envía payload vía HTTP

        Args:
            payload: Datos a enviar

        Returns:
            True si exitoso
        """
        try:
            if self.method == "POST":
                response = self.session.post(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers,
                    timeout=self.timeout
                )
            elif self.method == "PUT":
                response = self.session.put(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers,
                    timeout=self.timeout
                )
            else:
                logger.error(f"Método HTTP no soportado: {self.method}")
                return False

            response.raise_for_status()

            self.sent_count += 1
            logger.debug(f"Webhook enviado exitosamente: {payload['event_type']}")
            return True

        except requests.exceptions.Timeout:
            self.error_count += 1
            logger.warning(f"Timeout enviando webhook (>{self.timeout}s)")
            return False

        except requests.exceptions.ConnectionError as e:
            self.error_count += 1
            logger.error(f"Error de conexión con webhook: {e}")
            return False

        except requests.exceptions.HTTPError as e:
            self.error_count += 1
            logger.error(f"Error HTTP enviando webhook: {e.response.status_code} - {e.response.text}")
            return False

        except Exception as e:
            self.error_count += 1
            logger.error(f"Error inesperado enviando webhook: {e}")
            return False

    def test_connection(self) -> bool:
        """
        Prueba la conexión al webhook

        Returns:
            True si exitoso
        """
        test_payload = {
            "event_type": "test",
            "timestamp": datetime.now().isoformat(),
            "message": "Test connection from PPE Detection System"
        }

        logger.info(f"Probando conexión a webhook: {self.webhook_url}")
        success = self._send_payload(test_payload)

        if success:
            logger.info("✅ Conexión a webhook exitosa")
        else:
            logger.error("❌ Falló conexión a webhook")

        return success

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del sender"""
        return {
            "webhook_url": self.webhook_url,
            "method": self.method,
            "sent_count": self.sent_count,
            "error_count": self.error_count,
            "success_rate": (self.sent_count / (self.sent_count + self.error_count) * 100)
            if (self.sent_count + self.error_count) > 0 else 0
        }

    def close(self):
        """Cierra la sesión"""
        self.session.close()
        logger.info("Webhook sender cerrado")

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support"""
        self.close()
