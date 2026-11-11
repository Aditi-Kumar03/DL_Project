"""
NutriVision AI — Object Detection Adapter (YOLO)
Implements FoodModelInterface for future object detection models (e.g. YOLOv8 / YOLOv11)
when bounding-box annotated multi-food datasets (CVAT/Label Studio) are available.
"""

import os
from typing import List, Optional, Dict, Any
from PIL import Image

from backend.base_model import FoodModelInterface, PredictionResult


class FoodDetector(FoodModelInterface):
    """
    Object detection model adapter for multi-food plate detection (e.g., an Indian thali).
    Uses Ultralytics YOLO when bounding-box trained weights ('best.pt') are available.
    """

    def __init__(self, model_path: Optional[str] = None, device: Optional[str] = None):
        self.model = None
        self.device = device or "cpu"
        self.model_path = model_path
        self.classes: List[str] = []

        if model_path and os.path.exists(model_path):
            self.load(model_path, self.device)

    def load(self, model_path: str, device: Optional[str] = None) -> None:
        """Load YOLO model weights using ultralytics."""
        try:
            from ultralytics import YOLO
        except ImportError:
            raise ImportError(
                "Ultralytics is required for object detection. Install with: pip install ultralytics"
            )

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Detection weights not found at: {model_path}")

        self.model_path = model_path
        self.device = device or self.device
        self.model = YOLO(model_path)
        if hasattr(self.model, "names") and isinstance(self.model.names, dict):
            self.classes = [self.model.names[i] for i in sorted(self.model.names.keys())]

    def predict(self, image: Image.Image, conf_threshold: float = 0.25) -> List[PredictionResult]:
        """
        Run object detection inference across the image to localize and identify multiple food items.
        """
        if self.model is None:
            raise RuntimeError(
                "Detection model is not loaded. Train a YOLO model on a bounding-box annotated "
                "dataset or switch to FoodClassifier."
            )

        results = self.model.predict(source=image, conf=conf_threshold, device=self.device, verbose=False)
        predictions: List[PredictionResult] = []

        if not results:
            return predictions

        res = results[0]
        boxes = res.boxes

        for box in boxes:
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            xyxy = [int(v) for v in box.xyxy[0].tolist()]
            food_name = self.classes[cls_id] if cls_id < len(self.classes) else f"class_{cls_id}"

            predictions.append(PredictionResult(
                food_name=food_name,
                confidence=conf,
                class_id=cls_id,
                box=xyxy,
                top_k=[]
            ))

        return predictions

    def predict_region(self, image: Image.Image, box: List[int]) -> PredictionResult:
        """Run detection or classification on a cropped sub-region."""
        x1, y1, x2, y2 = box
        cropped = image.crop((x1, y1, x2, y2))
        sub_preds = self.predict(cropped)
        if sub_preds:
            best = sub_preds[0]
            best.box = [int(x1), int(y1), int(x2), int(y2)]
            return best
        return PredictionResult(
            food_name="unknown",
            confidence=0.0,
            class_id=-1,
            box=[int(x1), int(y1), int(x2), int(y2)]
        )

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_type": "object_detection",
            "architecture": "YOLO",
            "weights_path": self.model_path,
            "device": self.device,
            "classes": self.classes,
            "is_loaded": self.model is not None
        }
