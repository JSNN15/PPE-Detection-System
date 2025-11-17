"""
CSV Exporter para logs de detecciones
Formato estándar industrial
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import threading
import queue

logger = logging.getLogger(__name__)


class CSVExporter:
    """
    Exportador de detecciones a CSV
    Thread-safe para múltiples cámaras
    """

    def __init__(
        self,
        export_path: str,
        buffer_size: int = 100,
        auto_flush_interval: int = 60
    ):
        """
        Inicializa el exportador CSV

        Args:
            export_path: Path base para archivos CSV
            buffer_size: Tamaño del buffer antes de flush
            auto_flush_interval: Intervalo de auto-flush en segundos
        """
        self.export_path = Path(export_path)
        self.export_path.mkdir(parents=True, exist_ok=True)

        self.buffer_size = buffer_size
        self.auto_flush_interval = auto_flush_interval

        # Buffer thread-safe
        self.buffer = queue.Queue()
        self.lock = threading.Lock()

        # Estadísticas
        self.exported_count = 0
        self.current_file = None
        self.current_date = None

        logger.info(f"CSV Exporter inicializado en: {self.export_path}")

    def add_detection(
        self,
        camera_id: str,
        camera_name: str,
        timestamp: datetime,
        detections: List[Dict[str, Any]],
        zone: Optional[str] = None
    ):
        """
        Añade una detección al buffer

        Args:
            camera_id: ID de la cámara
            camera_name: Nombre de la cámara
            timestamp: Timestamp de la detección
            detections: Lista de detecciones
            zone: Zona de la planta
        """
        # Crear una entrada por cada objeto detectado
        for detection in detections:
            entry = {
                'timestamp': timestamp.isoformat(),
                'date': timestamp.strftime('%Y-%m-%d'),
                'time': timestamp.strftime('%H:%M:%S'),
                'camera_id': camera_id,
                'camera_name': camera_name,
                'zone': zone or 'unknown',
                'object_class': detection.get('class', 'unknown'),
                'confidence': f"{detection.get('confidence', 0):.3f}",
                'bbox_x1': detection.get('bbox', [0, 0, 0, 0])[0],
                'bbox_y1': detection.get('bbox', [0, 0, 0, 0])[1],
                'bbox_x2': detection.get('bbox', [0, 0, 0, 0])[2],
                'bbox_y2': detection.get('bbox', [0, 0, 0, 0])[3],
            }

            self.buffer.put(entry)

        # Flush si el buffer está lleno
        if self.buffer.qsize() >= self.buffer_size:
            self.flush()

    def add_alert(
        self,
        camera_id: str,
        camera_name: str,
        timestamp: datetime,
        alert_type: str,
        severity: str,
        message: str,
        zone: Optional[str] = None
    ):
        """
        Añade una alerta al CSV de alertas

        Args:
            camera_id: ID de la cámara
            camera_name: Nombre de la cámara
            timestamp: Timestamp
            alert_type: Tipo de alerta
            severity: Severidad
            message: Mensaje
            zone: Zona
        """
        entry = {
            'timestamp': timestamp.isoformat(),
            'date': timestamp.strftime('%Y-%m-%d'),
            'time': timestamp.strftime('%H:%M:%S'),
            'camera_id': camera_id,
            'camera_name': camera_name,
            'zone': zone or 'unknown',
            'alert_type': alert_type,
            'severity': severity,
            'message': message,
        }

        # Escribir directamente (las alertas son críticas)
        self._write_alert(entry)

    def flush(self):
        """
        Escribe el buffer al archivo CSV
        """
        if self.buffer.empty():
            return

        with self.lock:
            entries = []
            while not self.buffer.empty():
                try:
                    entries.append(self.buffer.get_nowait())
                except queue.Empty:
                    break

            if not entries:
                return

            # Escribir al archivo
            self._write_detections(entries)
            self.exported_count += len(entries)

            logger.info(f"Exportadas {len(entries)} detecciones a CSV")

    def _write_detections(self, entries: List[Dict[str, Any]]):
        """
        Escribe entradas al archivo CSV de detecciones
        """
        # Obtener fecha actual
        current_date = datetime.now().strftime('%Y-%m-%d')

        # Nombre del archivo por día
        filename = self.export_path / f"detections_{current_date}.csv"

        # Verificar si archivo existe
        file_exists = filename.exists()

        # Escribir al archivo
        with open(filename, 'a', newline='', encoding='utf-8') as f:
            fieldnames = [
                'timestamp', 'date', 'time', 'camera_id', 'camera_name', 'zone',
                'object_class', 'confidence', 'bbox_x1', 'bbox_y1', 'bbox_x2', 'bbox_y2'
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)

            # Escribir header si es nuevo archivo
            if not file_exists:
                writer.writeheader()

            # Escribir entradas
            writer.writerows(entries)

    def _write_alert(self, entry: Dict[str, Any]):
        """
        Escribe una alerta al archivo CSV de alertas
        """
        current_date = datetime.now().strftime('%Y-%m-%d')
        filename = self.export_path / f"alerts_{current_date}.csv"

        file_exists = filename.exists()

        with open(filename, 'a', newline='', encoding='utf-8') as f:
            fieldnames = [
                'timestamp', 'date', 'time', 'camera_id', 'camera_name',
                'zone', 'alert_type', 'severity', 'message'
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow(entry)

    def export_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Genera resumen de detecciones para una fecha

        Args:
            date: Fecha en formato YYYY-MM-DD (default: hoy)

        Returns:
            Diccionario con estadísticas
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        filename = self.export_path / f"detections_{date}.csv"

        if not filename.exists():
            logger.warning(f"No existe archivo CSV para {date}")
            return {}

        # Leer archivo y generar estadísticas
        stats = {
            'date': date,
            'total_detections': 0,
            'by_camera': {},
            'by_class': {},
            'by_zone': {},
        }

        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                stats['total_detections'] += 1

                # Por cámara
                camera = row['camera_id']
                stats['by_camera'][camera] = stats['by_camera'].get(camera, 0) + 1

                # Por clase
                obj_class = row['object_class']
                stats['by_class'][obj_class] = stats['by_class'].get(obj_class, 0) + 1

                # Por zona
                zone = row['zone']
                stats['by_zone'][zone] = stats['by_zone'].get(zone, 0) + 1

        logger.info(f"Resumen generado para {date}: {stats['total_detections']} detecciones")
        return stats

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del exporter"""
        return {
            'export_path': str(self.export_path),
            'buffer_size': self.buffer.qsize(),
            'exported_count': self.exported_count,
        }

    def close(self):
        """Cierra el exporter y hace flush final"""
        logger.info("Cerrando CSV Exporter...")
        self.flush()
        logger.info(f"CSV Exporter cerrado. Total exportado: {self.exported_count}")

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support"""
        self.close()
