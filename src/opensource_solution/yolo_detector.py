"""
YOLO Detector para detección de EPP
Solución Open Source con YOLOv8
"""

import logging
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np
from ultralytics import YOLO
import torch

logger = logging.getLogger(__name__)


class YOLODetector:
    """
    Detector de EPP usando YOLOv8
    Solución completamente gratuita y open source
    """

    def __init__(
        self,
        model_path: str,
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        device: Optional[str] = None,
        class_names: Optional[List[str]] = None
    ):
        """
        Inicializa el detector YOLO

        Args:
            model_path: Path al modelo entrenado (.pt o .onnx)
            confidence_threshold: Umbral de confianza
            iou_threshold: Umbral de IoU para NMS
            device: Dispositivo ('cpu', 'cuda', 'mps' o None para auto)
            class_names: Nombres de las clases (opcional)
        """
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold

        # Determinar dispositivo
        if device is None:
            if torch.cuda.is_available():
                self.device = 'cuda'
            elif torch.backends.mps.is_available():
                self.device = 'mps'
            else:
                self.device = 'cpu'
        else:
            self.device = device

        logger.info(f"Cargando modelo YOLO desde: {self.model_path}")
        logger.info(f"Dispositivo: {self.device}")

        # Cargar modelo
        try:
            self.model = YOLO(str(self.model_path))
            logger.info(f"✅ Modelo YOLO cargado exitosamente")
        except Exception as e:
            logger.error(f"❌ Error cargando modelo: {e}")
            raise

        # Obtener nombres de clases
        if class_names:
            self.class_names = class_names
        else:
            # Obtener del modelo
            self.class_names = self.model.names if hasattr(self.model, 'names') else []

        logger.info(f"Clases configuradas: {len(self.class_names)}")

        # Estadísticas
        self.total_detections = 0
        self.total_frames = 0
        self.total_inference_time = 0.0

        # Warm-up del modelo
        self._warmup()

    def _warmup(self, warmup_frames: int = 3):
        """
        Warm-up del modelo para optimizar primera inferencia
        """
        logger.info("Realizando warm-up del modelo...")
        dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)

        for _ in range(warmup_frames):
            _ = self.model.predict(
                dummy_img,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                device=self.device,
                verbose=False
            )

        logger.info("✅ Warm-up completado")

    def detect(
        self,
        frame: np.ndarray,
        return_annotated: bool = False
    ) -> Dict[str, Any]:
        """
        Detecta EPP en un frame

        Args:
            frame: Imagen (numpy array BGR)
            return_annotated: Si retornar frame anotado

        Returns:
            Diccionario con detecciones y metadatos
        """
        start_time = time.time()

        # Hacer predicción
        results = self.model.predict(
            frame,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            device=self.device,
            verbose=False
        )[0]

        inference_time = time.time() - start_time

        # Procesar resultados
        detections = []

        for box in results.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]

            detection = {
                'class_id': class_id,
                'class': self.class_names[class_id] if class_id < len(self.class_names) else 'unknown',
                'confidence': confidence,
                'bbox': bbox,  # [x1, y1, x2, y2]
            }

            detections.append(detection)

        # Actualizar estadísticas
        self.total_frames += 1
        self.total_detections += len(detections)
        self.total_inference_time += inference_time

        # Construir respuesta
        response = {
            'num_detections': len(detections),
            'detections': detections,
            'inference_time': inference_time,
            'fps': 1 / inference_time if inference_time > 0 else 0,
        }

        if return_annotated:
            response['annotated_frame'] = results.plot()

        return response

    def detect_batch(
        self,
        frames: List[np.ndarray],
        return_annotated: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Detecta EPP en múltiples frames (batch processing)

        Args:
            frames: Lista de imágenes
            return_annotated: Si retornar frames anotados

        Returns:
            Lista de diccionarios con detecciones
        """
        start_time = time.time()

        # Hacer predicción batch
        results_batch = self.model.predict(
            frames,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            device=self.device,
            verbose=False
        )

        inference_time = time.time() - start_time

        # Procesar resultados
        all_results = []

        for results in results_batch:
            detections = []

            for box in results.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                bbox = box.xyxy[0].tolist()

                detection = {
                    'class_id': class_id,
                    'class': self.class_names[class_id] if class_id < len(self.class_names) else 'unknown',
                    'confidence': confidence,
                    'bbox': bbox,
                }

                detections.append(detection)

            response = {
                'num_detections': len(detections),
                'detections': detections,
            }

            if return_annotated:
                response['annotated_frame'] = results.plot()

            all_results.append(response)

            # Actualizar estadísticas
            self.total_frames += 1
            self.total_detections += len(detections)

        self.total_inference_time += inference_time

        return all_results

    def check_ppe_compliance(
        self,
        detections: List[Dict[str, Any]],
        required_ppe: List[str]
    ) -> Dict[str, Any]:
        """
        Verifica cumplimiento de EPP requerido

        Args:
            detections: Lista de detecciones
            required_ppe: Lista de EPPs requeridos

        Returns:
            Diccionario con estado de cumplimiento
        """
        detected_classes = {d['class'] for d in detections}

        missing_ppe = []
        for ppe in required_ppe:
            if ppe not in detected_classes:
                missing_ppe.append(ppe)

        is_compliant = len(missing_ppe) == 0

        return {
            'is_compliant': is_compliant,
            'required_ppe': required_ppe,
            'detected_ppe': list(detected_classes),
            'missing_ppe': missing_ppe,
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas del detector

        Returns:
            Diccionario con estadísticas
        """
        avg_inference_time = (
            self.total_inference_time / self.total_frames
            if self.total_frames > 0 else 0
        )

        avg_fps = 1 / avg_inference_time if avg_inference_time > 0 else 0

        return {
            'model_path': str(self.model_path),
            'device': self.device,
            'total_frames': self.total_frames,
            'total_detections': self.total_detections,
            'avg_detections_per_frame': (
                self.total_detections / self.total_frames
                if self.total_frames > 0 else 0
            ),
            'avg_inference_time': avg_inference_time,
            'avg_fps': avg_fps,
            'confidence_threshold': self.confidence_threshold,
            'iou_threshold': self.iou_threshold,
        }

    def reset_stats(self):
        """Reinicia estadísticas"""
        self.total_detections = 0
        self.total_frames = 0
        self.total_inference_time = 0.0
        logger.info("Estadísticas reiniciadas")

    def set_thresholds(
        self,
        confidence: Optional[float] = None,
        iou: Optional[float] = None
    ):
        """
        Actualiza umbrales de detección

        Args:
            confidence: Nuevo umbral de confianza
            iou: Nuevo umbral de IoU
        """
        if confidence is not None:
            self.confidence_threshold = confidence
            logger.info(f"Umbral de confianza actualizado a: {confidence}")

        if iou is not None:
            self.iou_threshold = iou
            logger.info(f"Umbral de IoU actualizado a: {iou}")

    def __repr__(self):
        return f"YOLODetector(model={self.model_path.name}, device={self.device}, classes={len(self.class_names)})"
