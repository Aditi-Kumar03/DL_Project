"""
NutriVision AI — Base Model Interface
Standardized abstraction for food identification models (Classifiers and Detectors).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from PIL import Image


@dataclass
class PredictionResult:
    """Represents a single detected or classified food item."""
    food_name: str
    confidence: float
    class_id: int
    box: Optional[List[int]] = None  # [x1, y1, x2, y2] bounding box coordinates, or None for full image
    top_k: List[Dict[str, Any]] = field(default_factory=list)  # Top alternative predictions for user correction

    def to_dict(self) -> Dict[str, Any]:
        return {
            "food_name": self.food_name,
            "confidence": round(self.confidence, 4),
            "class_id": self.class_id,
            "box": self.box,
            "top_k": self.top_k
        }


class FoodModelInterface(ABC):
    """
    Abstract Model Interface ensuring the frontend and nutrition engine remain
    agnostic to whether the backend is powered by a classifier or an object detector.
    """

    @abstractmethod
    def load(self, model_path: str, device: Optional[str] = None) -> None:
        """Load model weights and metadata from disk."""
        pass

    @abstractmethod
    def predict(self, image: Image.Image, conf_threshold: float = 0.25) -> List[PredictionResult]:
        """
        Run inference on a single image.
        For a classifier: Returns a single PredictionResult for the whole image (or top candidate).
        For a detector: Returns multiple PredictionResults, one for each localized bounding box.
        """
        pass

    @abstractmethod
    def predict_region(self, image: Image.Image, box: List[int]) -> PredictionResult:
        """
        Run classification on a cropped sub-region of an image (e.g. an individual dish from a thali).
        box is [x1, y1, x2, y2].
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Return metadata about the loaded model architecture and configuration."""
        pass
