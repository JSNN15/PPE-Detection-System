"""
Camera Stream Management
Manejo de streams de cámaras IP (RTSP/HTTP)
"""

import cv2
import time
import threading
import logging
from typing import Optional, Callable
from queue import Queue
import os

logger = logging.getLogger(__name__)


def build_camera_url(camera_config: dict) -> str:
    """
    Construye URL de conexión para cámara IP

    Args:
        camera_config: Diccionario con configuración de cámara

    Returns:
        URL de conexión formateada
    """
    protocol = camera_config['protocol']
    host = camera_config['host']
    port = camera_config['port']
    path = camera_config['path']
    username = camera_config.get('username', '')

    # Obtener password de variable de entorno
    password_var = camera_config.get('password', '')
    if password_var.startswith('${') and password_var.endswith('}'):
        env_var = password_var[2:-1]
        password = os.getenv(env_var, '')
    else:
        password = password_var

    # Construir URL según protocolo
    if protocol.lower() == 'rtsp':
        if username and password:
            url = f"rtsp://{username}:{password}@{host}:{port}{path}"
        else:
            url = f"rtsp://{host}:{port}{path}"

    elif protocol.lower() == 'http':
        if username and password:
            url = f"http://{username}:{password}@{host}:{port}{path}"
        else:
            url = f"http://{host}:{port}{path}"

    else:
        raise ValueError(f"Protocolo no soportado: {protocol}")

    return url


class CameraStream:
    """
    Clase para manejar stream de cámara IP con auto-reconexión
    """

    def __init__(
        self,
        camera_config: dict,
        buffer_size: int = 1,
        reconnect_attempts: int = 5,
        reconnect_delay: int = 10
    ):
        """
        Inicializa el stream de cámara

        Args:
            camera_config: Configuración de la cámara
            buffer_size: Tamaño del buffer de frames
            reconnect_attempts: Intentos de reconexión
            reconnect_delay: Delay entre intentos (segundos)
        """
        self.camera_config = camera_config
        self.camera_id = camera_config['camera_id']
        self.name = camera_config['name']
        self.buffer_size = buffer_size
        self.reconnect_attempts = reconnect_attempts
        self.reconnect_delay = reconnect_delay

        self.url = build_camera_url(camera_config)
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.frame_queue = Queue(maxsize=buffer_size)

        self.frame_count = 0
        self.error_count = 0
        self.last_frame_time = None

        logger.info(f"CameraStream inicializado para {self.camera_id}: {self.name}")

    def connect(self, timeout: int = 30) -> bool:
        """
        Conecta a la cámara

        Returns:
            True si conexión exitosa, False en caso contrario
        """
        # Sanitize URL para logging (ocultar credenciales)
        safe_url = self.url
        if '@' in safe_url:
            # Ocultar user:pass
            parts = safe_url.split('@')
            safe_url = f"{parts[0].split('://')[0]}://***:***@{parts[1]}"

        logger.info(f"Conectando a {self.camera_id}: {safe_url}")

        self.cap = cv2.VideoCapture(self.url)

        # Configurar propiedades
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)

        # Verificar conexión leyendo un frame
        start_time = time.time()
        while time.time() - start_time < timeout:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                h, w = frame.shape[:2]
                logger.info(f"✅ Conectado a {self.camera_id} - Resolución: {w}x{h}")
                return True
            time.sleep(0.5)

        logger.error(f"❌ Timeout conectando a {self.camera_id} ({timeout}s)")
        if self.cap:
            self.cap.release()
            self.cap = None
        return False

    def start(self):
        """
        Inicia el thread de captura de frames
        """
        if self.is_running:
            logger.warning(f"Stream {self.camera_id} ya está corriendo")
            return

        if not self.connect():
            logger.error(f"No se pudo iniciar stream {self.camera_id}")
            return

        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        logger.info(f"Stream {self.camera_id} iniciado")

    def _capture_loop(self):
        """
        Loop principal de captura de frames (ejecuta en thread)
        """
        consecutive_errors = 0

        while self.is_running:
            try:
                ret, frame = self.cap.read()

                if not ret or frame is None:
                    consecutive_errors += 1
                    self.error_count += 1

                    if consecutive_errors >= 10:
                        logger.warning(f"Múltiples errores en {self.camera_id}, intentando reconectar...")
                        if self._reconnect():
                            consecutive_errors = 0
                        else:
                            logger.error(f"Reconexión falló para {self.camera_id}")
                            break

                    time.sleep(0.1)
                    continue

                # Frame capturado exitosamente
                consecutive_errors = 0
                self.frame_count += 1
                self.last_frame_time = time.time()

                # Añadir a queue (remover viejo si está lleno)
                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()
                    except:
                        pass

                self.frame_queue.put(frame)

            except Exception as e:
                logger.error(f"Error en capture loop de {self.camera_id}: {e}")
                consecutive_errors += 1
                time.sleep(0.1)

        logger.info(f"Capture loop terminado para {self.camera_id}")

    def _reconnect(self) -> bool:
        """
        Intenta reconectar a la cámara

        Returns:
            True si reconexión exitosa
        """
        if self.cap:
            self.cap.release()

        for attempt in range(1, self.reconnect_attempts + 1):
            logger.info(f"Intento de reconexión {attempt}/{self.reconnect_attempts} para {self.camera_id}")
            time.sleep(self.reconnect_delay)

            if self.connect():
                logger.info(f"✅ Reconexión exitosa a {self.camera_id}")
                return True

        logger.error(f"❌ Falló reconexión a {self.camera_id}")
        return False

    def read(self) -> Optional[tuple]:
        """
        Lee el frame más reciente

        Returns:
            (True, frame) si hay frame disponible, (False, None) en caso contrario
        """
        if self.frame_queue.empty():
            return False, None

        try:
            frame = self.frame_queue.get_nowait()
            return True, frame
        except:
            return False, None

    def stop(self):
        """
        Detiene el stream de cámara
        """
        logger.info(f"Deteniendo stream {self.camera_id}")
        self.is_running = False

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

        if self.cap:
            self.cap.release()
            self.cap = None

        logger.info(f"Stream {self.camera_id} detenido")

    def get_stats(self) -> dict:
        """
        Retorna estadísticas del stream
        """
        return {
            'camera_id': self.camera_id,
            'name': self.name,
            'is_running': self.is_running,
            'frame_count': self.frame_count,
            'error_count': self.error_count,
            'queue_size': self.frame_queue.qsize(),
            'last_frame_time': self.last_frame_time,
        }

    def __enter__(self):
        """Context manager support"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support"""
        self.stop()
